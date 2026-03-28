from __future__ import annotations

import base64
from dataclasses import replace
from io import BytesIO
from tempfile import NamedTemporaryFile
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import ContextTypes
from PIL import Image

from invoicebot.models import SupportTicket
from invoicebot.services.billing import evaluate_quota
from invoicebot.services.checkout import create_checkout_session
from invoicebot.services.mock_data import seed_mock_clients
from invoicebot.services.parser import parse_line_items
from invoicebot.services.pdf import render_invoice_pdf
from invoicebot.services.storage import Repository
from invoicebot.services.template_catalog import TEMPLATES
from invoicebot.services.transcription import transcribe_audio_file


DEVELOPMENT_NOTICE = (
    "InvoiceBot is currently in development.\n\n"
    "Features may change, messages may be rough, and invoices should be reviewed before sending to real clients."
)

FIELD_LIMITS = {
    "company name": 60,
    "business address": 120,
    "business email": 80,
    "business phone": 32,
    "GST number": 32,
    "client name": 60,
    "client company": 60,
    "client email": 80,
    "client phone": 32,
    "client address": 120,
}

LOGO_MAX_FILE_SIZE = 5 * 1024 * 1024
LOGO_MIN_WIDTH = 120
LOGO_MIN_HEIGHT = 60
LOGO_MAX_WIDTH = 5000
LOGO_MAX_HEIGHT = 5000
ALLOWED_LOGO_MIME_TYPES = {"image/png", "image/jpeg"}
CLIENTS_PAGE_SIZE = 6
MAX_INVOICE_ITEMS = 14


def _user_key(update: Update) -> str:
    user = update.effective_user
    return str(user.id if user else "unknown")


def _repo(context: ContextTypes.DEFAULT_TYPE) -> Repository:
    return context.application.bot_data["repo"]


def _is_user_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    allowed_ids = context.application.bot_data["settings"].allowed_telegram_user_ids
    if not allowed_ids:
        return True
    return _user_key(update) in allowed_ids


def _is_admin_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admin_ids = context.application.bot_data["settings"].admin_telegram_user_ids
    return bool(admin_ids) and _user_key(update) in admin_ids


async def _deny_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target_message = update.callback_query.message if update.callback_query else update.message
    if not target_message:
        return
    await target_message.reply_text(
        "This bot is currently locked to approved testers only.\n\n"
        "If you should have access, please contact the owner for beta access."
    )


async def _deny_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target_message = update.callback_query.message if update.callback_query else update.message
    if not target_message:
        return
    await target_message.reply_text("This command is only available to configured bot admins.")


async def _validate_text_length(message: Message | None, label: str, value: str) -> bool:
    limit = FIELD_LIMITS[label]
    if len(value) <= limit:
        return True
    if message:
        await message.reply_text(
            f"{label.capitalize()} must be {limit} characters or fewer. Please send a shorter value."
        )
    return False


def _logo_prompt(profile) -> tuple[str, InlineKeyboardMarkup | None]:
    if profile.logo_url:
        return (
            "Saved. Send a new logo as a photo or PNG/JPG image, or keep the current one.",
            _skip_keyboard("profile_logo", label="Keep current logo"),
        )
    return (
        "Saved. Send your logo as a Telegram photo or a PNG/JPG file, or skip this for now.",
        _skip_keyboard("profile_logo", label="Skip logo"),
    )


def _is_image_document(document) -> bool:
    if not document:
        return False
    return (document.mime_type or "").lower() in ALLOWED_LOGO_MIME_TYPES


async def _store_profile_logo(message: Message | None, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> bool:
    if not message:
        return False

    document = message.document if _is_image_document(message.document) else None
    photo = message.photo[-1] if message.photo else None
    media = document or photo
    if not media:
        await message.reply_text("Send a photo or PNG/JPG image file for the logo, or use the skip button.")
        return False

    file_size = getattr(media, "file_size", 0) or 0
    if file_size > LOGO_MAX_FILE_SIZE:
        await message.reply_text("Logo images must be smaller than 5 MB. A normal phone photo or PNG should work fine.")
        return False

    telegram_file = await context.bot.get_file(media.file_id)
    buffer = BytesIO()
    await telegram_file.download_to_memory(out=buffer)
    raw_bytes = buffer.getvalue()

    try:
        with Image.open(BytesIO(raw_bytes)) as image:
            image.load()
            image_format = (image.format or "").upper()
            width, height = image.size
    except Exception:
        await message.reply_text("I couldn't read that image. Please send a normal JPG or PNG logo.")
        return False

    if image_format not in {"PNG", "JPEG", "JPG"}:
        await message.reply_text("Please send the logo as a PNG or JPG image.")
        return False
    if width < LOGO_MIN_WIDTH or height < LOGO_MIN_HEIGHT:
        await message.reply_text("That image is a bit too small. Please use one that is at least 120 x 60 pixels.")
        return False
    if width > LOGO_MAX_WIDTH or height > LOGO_MAX_HEIGHT:
        await message.reply_text("That image is too large. Please use one under 5000 x 5000 pixels.")
        return False

    aspect_ratio = width / max(height, 1)
    if aspect_ratio < 0.2 or aspect_ratio > 5.0:
        await message.reply_text("That logo shape is too extreme for the invoice header. Please use something closer to a normal logo image.")
        return False

    profile = _repo(context).get_or_create_profile(user_id)
    mime_type = "image/png" if image_format == "PNG" else "image/jpeg"
    profile.logo_url = f"data:{mime_type};base64,{base64.b64encode(raw_bytes).decode('ascii')}"
    _repo(context).save_profile(user_id, profile)
    context.user_data["mode"] = None
    await message.reply_text("Logo saved. It will be used on your invoice PDFs.")
    return True


async def _send_temporary_status(message: Message | None, text: str) -> Message | None:
    if not message:
        return None
    return await message.reply_text(text)


async def _validate_invoice_item_limit(message: Message | None, current_count: int, incoming_count: int) -> bool:
    if current_count + incoming_count <= MAX_INVOICE_ITEMS:
        return True
    if message:
        await message.reply_text(
            f"Invoices can have up to {MAX_INVOICE_ITEMS} items so the PDF stays within 2 clean pages. "
            f"You currently have {current_count} item(s)."
        )
    return False


async def _clear_temporary_status(message: Message | None) -> None:
    if not message:
        return
    try:
        await message.delete()
    except Exception:
        pass


def _voice_limit_keyboard(settings) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [[InlineKeyboardButton("Keep with text", callback_data="voice_continue_text")]]
    rows.append([InlineKeyboardButton("Unlock voice", callback_data="buy_voice_credits")])
    return InlineKeyboardMarkup(rows)


def _skip_keyboard(step: str, *, label: str = "Skip") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"skip_step:{step}")]])


def _item_line(item, index: int) -> str:
    return f"{index + 1}. {item.description}: {item.quantity:g} x ${item.unit_price_cents / 100:.2f}"


def _client_summary(client) -> str:
    if client.company:
        return f"{client.company} - {client.name}"
    return client.name


def _client_matches_query(client, query: str) -> bool:
    if not query:
        return True
    normalized = query.strip().lower()
    candidates = [client.name, client.company]
    for candidate in candidates:
        text = (candidate or "").lower()
        if text.startswith(normalized):
            return True
        if any(word.startswith(normalized) for word in text.split()):
            return True
    return False


def _filtered_clients(clients, query: str) -> list:
    return [client for client in clients if _client_matches_query(client, query)]


def _clients_keyboard(clients, *, page: int = 0, query: str = "") -> InlineKeyboardMarkup:
    filtered = _filtered_clients(clients, query)
    total_pages = max(1, (len(filtered) + CLIENTS_PAGE_SIZE - 1) // CLIENTS_PAGE_SIZE)
    safe_page = max(0, min(page, total_pages - 1))
    start = safe_page * CLIENTS_PAGE_SIZE
    visible_clients = filtered[start:start + CLIENTS_PAGE_SIZE]
    rows: list[list[InlineKeyboardButton]] = []
    for client in visible_clients:
        rows.append(
            [
                InlineKeyboardButton(f"Edit {client.name}", callback_data=f"client_edit:{client.id}"),
                InlineKeyboardButton(f"Delete {client.name}", callback_data=f"client_delete:{client.id}"),
            ]
        )
    navigation: list[InlineKeyboardButton] = []
    if safe_page > 0:
        navigation.append(InlineKeyboardButton("Prev", callback_data=f"clients_page:{safe_page - 1}"))
    if safe_page < total_pages - 1:
        navigation.append(InlineKeyboardButton("Next", callback_data=f"clients_page:{safe_page + 1}"))
    if navigation:
        rows.append(navigation)
    if query:
        rows.append([InlineKeyboardButton("Clear search", callback_data="clients_clear_search")])
    return InlineKeyboardMarkup(rows)


def _invoice_client_keyboard(clients) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index, client in enumerate(clients[:10]):
        rows.append([InlineKeyboardButton(f"{index + 1}. {client.name}", callback_data=f"pick_client:{client.id}")])
    rows.append([InlineKeyboardButton("Skip client", callback_data="skip_step:invoice_client_select")])
    return InlineKeyboardMarkup(rows)


def _client_edit_keyboard(client_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Name", callback_data=f"client_field:{client_id}:name"),
                InlineKeyboardButton("Company", callback_data=f"client_field:{client_id}:company"),
            ],
            [
                InlineKeyboardButton("Email", callback_data=f"client_field:{client_id}:email"),
                InlineKeyboardButton("Phone", callback_data=f"client_field:{client_id}:phone"),
            ],
            [InlineKeyboardButton("Address", callback_data=f"client_field:{client_id}:address")],
            [InlineKeyboardButton("Done", callback_data="client_edit_done")],
        ]
    )


async def _send_clients_list(message: Message | None, clients, *, page: int = 0, query: str = "") -> None:
    if not message:
        return
    if not clients:
        await message.reply_text("No saved clients yet. Use /newclient to add one.")
        return
    filtered = _filtered_clients(clients, query)
    if not filtered:
        await message.reply_text(
            f"No clients match `{query}`.\n\nSend at least 3 starting letters to search by name or company, or use the button below to clear the search.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Clear search", callback_data="clients_clear_search")]]),
        )
        return
    total_pages = max(1, (len(filtered) + CLIENTS_PAGE_SIZE - 1) // CLIENTS_PAGE_SIZE)
    safe_page = max(0, min(page, total_pages - 1))
    start = safe_page * CLIENTS_PAGE_SIZE
    visible_clients = filtered[start:start + CLIENTS_PAGE_SIZE]
    lines = "\n".join(f"{start + index + 1}. {_client_summary(client)}" for index, client in enumerate(visible_clients))
    header = f"Saved clients (page {safe_page + 1}/{total_pages})"
    if query:
        header += f"\nSearch: `{query}`"
    await message.reply_text(
        header
        + "\n\n"
        + lines
        + "\n\nSend at least 3 starting letters to search by client name or company.",
        parse_mode="Markdown",
        reply_markup=_clients_keyboard(clients, page=safe_page, query=query),
    )


def _draft_editor_keyboard(draft) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for index, item in enumerate(draft.items):
        rows.append(
            [
                InlineKeyboardButton(f"Edit {index + 1}", callback_data=f"edit_item:{index}"),
                InlineKeyboardButton(f"Delete {index + 1}", callback_data=f"delete_item:{index}"),
            ]
        )
    return InlineKeyboardMarkup(rows)


async def _send_draft_editor(message: Message | None, draft) -> None:
    if not message:
        return
    if not draft or not draft.items:
        await message.reply_text("There are no items in this draft yet.")
        return
    lines = "\n".join(_item_line(item, index) for index, item in enumerate(draft.items))
    await message.reply_text(
        "Choose an item to edit or delete:\n\n" + lines,
        reply_markup=_draft_editor_keyboard(draft),
    )


def _invoice_limit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Unlock 20 more invoices", callback_data="buy_invoice_credits")]])


async def _send_invoice_items_prompt(message: Message | None, prefix: str | None = None) -> None:
    if not message:
        return
    lead = f"{prefix}\n\n" if prefix else ""
    await message.reply_text(
        lead
        + "Now send line items like:\n"
        + "`Labour x 2 at $95`\n`Materials $45`\n\n"
        + "You can send multiple lines at once, then use /generate.",
        parse_mode="Markdown",
    )


def _checkout_return_urls(settings, purchase_type: str) -> tuple[str, str]:
    base_url = settings.marketing_site_url.strip().rstrip("/")
    if not base_url:
        raise ValueError("MARKETING_SITE_URL is not configured")
    return (
        f"{base_url}/pricing?checkout=success&type={purchase_type}",
        f"{base_url}/pricing?checkout=cancelled&type={purchase_type}",
    )


async def _send_checkout_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    purchase_type: str,
) -> None:
    repo = _repo(context)
    settings = context.application.bot_data["settings"]
    user_id = _user_key(update)

    if not settings.stripe_secret_key:
        raise ValueError("STRIPE_SECRET_KEY is not configured")

    if purchase_type == "voice":
        price_id = settings.stripe_voice_price_id
        credits_purchased = settings.paid_voice_block
        button_label = f"Pay NZD $5 for {credits_purchased} voice notes"
        body = (
            "Unlock more voice transcriptions with a secure Stripe checkout.\n\n"
            f"This purchase adds {credits_purchased} voice notes to your account."
        )
    else:
        price_id = settings.stripe_invoice_price_id
        credits_purchased = settings.paid_invoice_block
        button_label = f"Pay NZD $5 for {credits_purchased} invoices"
        body = (
            "Unlock more invoice credits with a secure Stripe checkout.\n\n"
            f"This purchase adds {credits_purchased} invoices to your account."
        )

    if not price_id:
        raise ValueError("Stripe price is not configured")

    success_url, cancel_url = _checkout_return_urls(settings, purchase_type)
    session = create_checkout_session(
        api_key=settings.stripe_secret_key,
        price_id=price_id,
        success_url=success_url,
        cancel_url=cancel_url,
        telegram_user_id=user_id,
        purchase_type=purchase_type,
        credits_purchased=credits_purchased,
        customer_id=repo.stripe_customer_id(user_id),
    )
    if isinstance(session.customer, str) and session.customer:
        repo.save_stripe_customer_id(user_id, session.customer)
    if not session.url:
        raise ValueError("Stripe did not return a checkout URL")

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(button_label, url=session.url)]])
    target_message = update.callback_query.message if update.callback_query else update.message
    if target_message:
        await target_message.reply_text(
            f"{body}\n\nAfter payment completes, come back here and continue in Telegram.",
            reply_markup=keyboard,
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    await update.message.reply_text(
        f"{DEVELOPMENT_NOTICE}\n\n"
        "InvoiceBot helps tradies create invoices from voice or text in Telegram.\n\n"
        "Use /profile to set up your business, /template to pick a layout, and /invoice to start a draft."
    )


async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(f"Your Telegram user ID is `{_user_key(update)}`.", parse_mode="Markdown")


async def mockclients_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    if not _is_admin_user(update, context):
        await _deny_admin(update, context)
        return

    settings = context.application.bot_data["settings"]
    if settings.environment == "production":
        await update.message.reply_text("Mock client seeding is disabled in production.")
        return

    repo = _repo(context)
    created = seed_mock_clients(repo, _user_key(update), count=50)
    await update.message.reply_text(f"Created {created} mock clients for this staging account.")


async def invoice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    repo = _repo(context)
    user_id = _user_key(update)
    draft = repo.create_draft(user_id)
    clients = repo.list_clients(user_id)
    if clients:
        context.user_data["mode"] = "invoice_client_select"
        context.user_data["client_options"] = {str(index + 1): client.id for index, client in enumerate(clients[:10])}
        client_lines = "\n".join(
            f"{index + 1}. {client.name} ({client.company or 'no company'})"
            for index, client in enumerate(clients[:10])
        )
        await update.message.reply_text(
            "Invoice draft started. Choose a saved client by number, or skip this for now.\n\n"
            f"{client_lines}",
            parse_mode="Markdown",
            reply_markup=_invoice_client_keyboard(clients),
        )
    else:
        context.user_data["mode"] = "invoice_items"
        await _send_invoice_items_prompt(update.message, "Invoice draft started. No saved clients found.")
    if not draft.items:
        return


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    repo = _repo(context)
    user_id = _user_key(update)
    draft = repo.get_draft(user_id)
    if not draft or not draft.items:
        await update.message.reply_text("Start with /invoice and add at least one line item first.")
        return
    client = repo.get_client(user_id, draft.client_id) if draft.client_id else None

    decision = evaluate_quota(
        invoice_count_this_month=repo.invoice_count_this_month(user_id),
        paid_credits=repo.paid_credits(user_id),
        free_limit=context.application.bot_data["settings"].free_invoice_limit,
        warning_threshold=context.application.bot_data["settings"].warning_threshold,
    )
    if decision.warning:
        await update.message.reply_text(decision.warning)
    if not decision.allowed:
        await update.message.reply_text(
            decision.message or "Payment required.",
            reply_markup=_invoice_limit_keyboard(),
        )
        return

    lines = "\n".join(
        f"- {item.description}: {item.quantity:g} x ${item.unit_price_cents / 100:.2f} = ${item.line_total_cents / 100:.2f}"
        for item in draft.items
    )
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Yes, generate PDF", callback_data="confirm_generate")],
         [InlineKeyboardButton("Edit draft", callback_data="edit_draft")]]
    )
    await update.message.reply_text(
        f"Please confirm this invoice:\n\n"
        f"Client: {client.name if client else 'No client selected'}\n\n"
        f"{lines}\n\n"
        f"Subtotal: ${draft.subtotal_cents / 100:.2f}\nGST: ${draft.gst_cents / 100:.2f}\nTotal: ${draft.total_cents / 100:.2f}",
        reply_markup=keyboard,
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    repo = _repo(context)
    profile = repo.get_or_create_profile(_user_key(update))
    context.user_data["mode"] = "profile_company_name"
    company_prompt = "Send your company name."
    keyboard = None
    if profile.company_name:
        company_prompt = "Send your company name, or keep the current one."
        keyboard = _skip_keyboard("profile_company_name", label="Keep current")
    await update.message.reply_text(
        "Let’s set up your business profile.\n"
        f"Current company name: {profile.company_name or 'not set'}\n"
        f"{company_prompt}",
        reply_markup=keyboard,
    )


def _profile_step_prompt(profile, field: str, label: str, next_text: str) -> str:
    current_value = getattr(profile, field)
    if current_value:
        return f"Saved. Current {label}: {current_value}\n{next_text}, or keep the current one."
    return f"Saved. {next_text}."


async def template_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    options = "\n".join(f"{index + 1}. {template.name} - {template.description}" for index, template in enumerate(TEMPLATES))
    context.user_data["mode"] = "template_select"
    await update.message.reply_text(
        "Choose your default template by sending a number:\n\n"
        f"{options}"
    )


async def new_client_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    context.user_data["mode"] = "client_name"
    await update.message.reply_text("Send the client name to add a new client.")


async def clients_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    repo = _repo(context)
    context.user_data["mode"] = "clients_search"
    context.user_data["clients_page"] = 0
    context.user_data["clients_query"] = ""
    clients = repo.list_clients(_user_key(update))
    await _send_clients_list(update.message, clients, page=0, query="")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    repo = _repo(context)
    history = repo.list_history(_user_key(update))
    if not history:
        await update.message.reply_text("No invoices generated yet.")
        return
    lines = [
        f"{index + 1}. {draft.items[0].description if draft.items else 'Invoice'} - ${draft.total_cents / 100:.2f}"
        for index, draft in enumerate(history[:10])
    ]
    await update.message.reply_text("Recent invoices:\n" + "\n".join(lines))


async def repeat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    repo = _repo(context)
    history = repo.list_history(_user_key(update))
    if not history:
        await update.message.reply_text("No recent invoices to repeat.")
        return
    new_draft = replace(history[0])
    repo.save_draft(new_draft)
    await update.message.reply_text("Loaded your most recent invoice as a new draft. Use /generate or send more items.")


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return
    context.user_data["mode"] = "support_type"
    await update.message.reply_text("Send a ticket type: Bug, Claim, Improvement, or Idea.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not _is_user_allowed(update, context):
        await _deny_access(update, context)
        return

    mode = context.user_data.get("mode")
    if mode == "profile_logo" and (update.message.photo or _is_image_document(update.message.document)):
        await _store_profile_logo(update.message, context, _user_key(update))
        return

    if update.message.voice or update.message.audio:
        await _handle_voice_message(update, context)
        return

    repo = _repo(context)
    user_id = _user_key(update)
    text = (update.message.text or update.message.caption or "").strip()
    if not text:
        await update.message.reply_text("Send text here, or use /profile if you want to upload a logo.")
        return

    if mode == "invoice_items":
        draft = repo.get_draft(user_id) or repo.create_draft(user_id)
        try:
            new_items = parse_line_items(text)
            if not await _validate_invoice_item_limit(update.message, len(draft.items), len(new_items)):
                return
            start_index = len(draft.items)
            draft.items.extend(new_items)
            repo.save_draft(draft)
            lines = "\n".join(
                _item_line(item, start_index + offset) for offset, item in enumerate(new_items)
            )
            await update.message.reply_text(
                f"Added {len(new_items)} item(s).\n\n{lines}\n\nYou now have {len(draft.items)} item(s) in this draft.",
                reply_markup=_draft_editor_keyboard(draft),
            )
        except ValueError as exc:
            await update.message.reply_text(str(exc))
        return

    if mode == "edit_draft_item":
        draft = repo.get_draft(user_id)
        item_index = context.user_data.get("edit_item_index")
        if draft is None or item_index is None or not (0 <= item_index < len(draft.items)):
            context.user_data["mode"] = "invoice_items"
            context.user_data.pop("edit_item_index", None)
            await update.message.reply_text("That draft item is no longer available. Use /invoice to continue.")
            return
        try:
            replacement_items = parse_line_items(text)
        except ValueError as exc:
            await update.message.reply_text(
                f"{exc}\n\nSend one replacement line item like:\n`Materials $45`",
                parse_mode="Markdown",
            )
            return
        if len(replacement_items) != 1:
            await update.message.reply_text(
                "Please send exactly one replacement line item, for example:\n`Labour x 2 at $95`",
                parse_mode="Markdown",
            )
            return
        draft.items[item_index] = replacement_items[0]
        repo.save_draft(draft)
        context.user_data["mode"] = "invoice_items"
        context.user_data.pop("edit_item_index", None)
        await update.message.reply_text(
            f"Updated item {item_index + 1}.\n\n{_item_line(replacement_items[0], item_index)}",
            reply_markup=_draft_editor_keyboard(draft),
        )
        return

    if mode == "invoice_client_select":
        draft = repo.get_draft(user_id) or repo.create_draft(user_id)
        if text.lower() == "skip":
            context.user_data["mode"] = "invoice_items"
            await _send_invoice_items_prompt(update.message, "No client selected.")
            return

        client_options = context.user_data.get("client_options", {})
        client_id = client_options.get(text)
        if not client_id:
            await update.message.reply_text("Send a listed client number, or type `skip` to continue without a client.", parse_mode="Markdown")
            return

        client = repo.get_client(user_id, client_id)
        if not client:
            await update.message.reply_text("I couldn't find that client anymore. Try again or type `skip`.")
            return

        draft.client_id = client.id
        repo.save_draft(draft)
        context.user_data["mode"] = "invoice_items"
        await _send_invoice_items_prompt(update.message, f"Selected client: {client.name}.")
        return

    if mode == "profile_company_name":
        profile = repo.get_or_create_profile(user_id)
        if text.lower() != "skip" and not await _validate_text_length(update.message, "company name", text):
            return
        if text.lower() != "skip" or not profile.company_name:
            profile.company_name = text
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = "profile_address"
        await update.message.reply_text(
            _profile_step_prompt(profile, "address", "business address", "Now send your business address"),
            parse_mode="Markdown",
            reply_markup=_skip_keyboard("profile_address", label="Keep current") if profile.address else None,
        )
        return

    if mode == "profile_address":
        profile = repo.get_or_create_profile(user_id)
        if text.lower() != "skip" and not await _validate_text_length(update.message, "business address", text):
            return
        if text.lower() != "skip" or not profile.address:
            profile.address = text
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = "profile_email"
        await update.message.reply_text(
            _profile_step_prompt(profile, "email", "email", "Now send your business email"),
            parse_mode="Markdown",
            reply_markup=_skip_keyboard("profile_email", label="Keep current") if profile.email else None,
        )
        return

    if mode == "profile_email":
        profile = repo.get_or_create_profile(user_id)
        if text.lower() != "skip" and not await _validate_text_length(update.message, "business email", text):
            return
        if text.lower() != "skip" or not profile.email:
            profile.email = text
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = "profile_phone"
        await update.message.reply_text(
            _profile_step_prompt(profile, "phone", "phone", "Now send your business phone"),
            parse_mode="Markdown",
            reply_markup=_skip_keyboard("profile_phone", label="Keep current") if profile.phone else None,
        )
        return

    if mode == "profile_phone":
        profile = repo.get_or_create_profile(user_id)
        if text.lower() != "skip" and not await _validate_text_length(update.message, "business phone", text):
            return
        if text.lower() != "skip" or not profile.phone:
            profile.phone = text
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = "profile_gst_number"
        await update.message.reply_text(
            _profile_step_prompt(profile, "gst_number", "GST number", "Now send your GST number"),
            parse_mode="Markdown",
            reply_markup=_skip_keyboard("profile_gst_number", label="Keep current") if profile.gst_number else None,
        )
        return

    if mode == "profile_gst_number":
        profile = repo.get_or_create_profile(user_id)
        if text.lower() != "skip" and not await _validate_text_length(update.message, "GST number", text):
            return
        if text.lower() != "skip" or not profile.gst_number:
            profile.gst_number = text
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = "profile_logo"
        logo_text, keyboard = _logo_prompt(profile)
        await update.message.reply_text(logo_text, reply_markup=keyboard)
        return

    if mode == "profile_logo":
        if text.lower() == "skip":
            context.user_data["mode"] = None
            await update.message.reply_text("Profile saved. Use /template to pick your default invoice layout.")
            return
        await update.message.reply_text("Send your logo as a photo or PNG/JPG file, or use the skip button.")
        return

    if mode == "template_select":
        try:
            template = TEMPLATES[int(text) - 1]
        except (ValueError, IndexError):
            await update.message.reply_text("Send a number from 1 to 5.")
            return
        profile = repo.get_or_create_profile(user_id)
        profile.default_template_id = template.id
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = None
        await update.message.reply_text(f"Saved {template.name} as your default template.")
        return

    if mode == "client_name":
        if not await _validate_text_length(update.message, "client name", text):
            return
        context.user_data["new_client_name"] = text
        context.user_data["mode"] = "client_company"
        await update.message.reply_text("Send the client company.", reply_markup=_skip_keyboard("client_company"))
        return

    if mode == "client_company":
        if text.lower() != "skip" and not await _validate_text_length(update.message, "client company", text):
            return
        context.user_data["new_client_company"] = "" if text.lower() == "skip" else text
        context.user_data["mode"] = "client_email"
        await update.message.reply_text("Send the client email.", reply_markup=_skip_keyboard("client_email"))
        return

    if mode == "client_email":
        if text.lower() != "skip" and not await _validate_text_length(update.message, "client email", text):
            return
        context.user_data["new_client_email"] = "" if text.lower() == "skip" else text
        context.user_data["mode"] = "client_phone"
        await update.message.reply_text("Send the client phone.", reply_markup=_skip_keyboard("client_phone"))
        return

    if mode == "client_phone":
        if text.lower() != "skip" and not await _validate_text_length(update.message, "client phone", text):
            return
        context.user_data["new_client_phone"] = "" if text.lower() == "skip" else text
        context.user_data["mode"] = "client_address"
        await update.message.reply_text("Send the client address.", reply_markup=_skip_keyboard("client_address"))
        return

    if mode == "client_address":
        if text.lower() != "skip" and not await _validate_text_length(update.message, "client address", text):
            return
        client = repo.add_client(
            user_id,
            name=context.user_data.pop("new_client_name", text),
            company=context.user_data.pop("new_client_company", ""),
            email=context.user_data.pop("new_client_email", ""),
            phone=context.user_data.pop("new_client_phone", ""),
            address="" if text.lower() == "skip" else text,
        )
        context.user_data["mode"] = None
        await update.message.reply_text(f"Saved client {_client_summary(client)}.")
        return

    if mode == "clients_search":
        if text.lower() in {"all", "clear"}:
            context.user_data["clients_query"] = ""
            context.user_data["clients_page"] = 0
            await _send_clients_list(update.message, repo.list_clients(user_id), page=0, query="")
            return
        if len(text) < 3:
            await update.message.reply_text(
                "Send at least 3 letters to search clients by name or company, or send `all` to show the full list again.",
                parse_mode="Markdown",
            )
            return
        context.user_data["clients_query"] = text
        context.user_data["clients_page"] = 0
        await _send_clients_list(update.message, repo.list_clients(user_id), page=0, query=text)
        return

    if mode == "edit_client_field":
        client_id = context.user_data.get("edit_client_id")
        field = context.user_data.get("edit_client_field")
        client = repo.get_client(user_id, client_id) if client_id else None
        if not client or field not in {"name", "company", "email", "phone", "address"}:
            context.user_data["mode"] = None
            context.user_data.pop("edit_client_id", None)
            context.user_data.pop("edit_client_field", None)
            await update.message.reply_text("That client is no longer available. Use /clients to refresh the list.")
            return
        value = "" if text.lower() == "remove" else text
        field_labels = {
            "name": "client name",
            "company": "client company",
            "email": "client email",
            "phone": "client phone",
            "address": "client address",
        }
        if value and not await _validate_text_length(update.message, field_labels[field], value):
            return
        setattr(client, field, value)
        repo.update_client(user_id, client)
        context.user_data["mode"] = None
        context.user_data.pop("edit_client_id", None)
        context.user_data.pop("edit_client_field", None)
        await update.message.reply_text(
            f"Updated {field} for {client.name}.",
            reply_markup=_client_edit_keyboard(client.id),
        )
        return

    if mode == "support_type":
        normalized = text.upper()
        if normalized not in {"BUG", "CLAIM", "IMPROVEMENT", "IDEA"}:
            await update.message.reply_text("Send one of: Bug, Claim, Improvement, Idea.")
            return
        context.user_data["support_type"] = normalized
        context.user_data["mode"] = "support_body"
        await update.message.reply_text("Describe the issue or idea.")
        return

    if mode == "support_body":
        ticket = SupportTicket(
            user_id=user_id,
            kind=context.user_data.get("support_type", "IDEA"),
            subject=f"{context.user_data.get('support_type', 'IDEA').title()} ticket",
            body=text,
        )
        repo.record_ticket(ticket)
        context.user_data["mode"] = None
        await update.message.reply_text("Ticket submitted. We’ll follow up in Telegram.")
        return

    await update.message.reply_text(
        "Use /invoice to start a draft, /profile to set up your business, or /support if you need help."
    )


async def _handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message:
        return

    mode = context.user_data.get("mode")
    if mode != "invoice_items":
        await message.reply_text("Voice notes are only supported while you are in an active /invoice draft.")
        return

    voice = message.voice or message.audio
    if not voice:
        await message.reply_text("Send a Telegram voice note or audio file during an invoice draft.")
        return

    settings = context.application.bot_data["settings"]
    repo = _repo(context)
    user_id = _user_key(update)

    if not settings.openai_api_key:
        await message.reply_text("Voice transcription is not enabled right now. Please type the line items instead.")
        return

    duration = getattr(voice, "duration", None) or 0
    if duration > settings.voice_note_max_seconds:
        await message.reply_text(
            f"Voice notes must be {settings.voice_note_max_seconds} seconds or shorter. Please send a shorter note or type the items."
        )
        return

    used = repo.voice_count_this_month(user_id)
    paid_voice_credits = repo.paid_voice_credits(user_id)
    if used >= settings.free_voice_transcriptions_per_month and paid_voice_credits <= 0:
        await message.reply_text(
            "You’ve used your free monthly voice transcriptions.\n\n"
            "You can keep going by typing the line items, or unlock more voice transcriptions to keep invoicing by voice.",
            reply_markup=_voice_limit_keyboard(settings),
        )
        return

    telegram_file = await context.bot.get_file(voice.file_id)
    loading_message = await _send_temporary_status(message, "Transcribing voice note...")
    with NamedTemporaryFile(suffix=".ogg", delete=True) as temp_file:
        try:
            await telegram_file.download_to_drive(custom_path=temp_file.name)
            transcript = await transcribe_audio_file(temp_file.name, settings.openai_api_key)
        except Exception:
            await message.reply_text("I couldn't transcribe that voice note. Please try again or type the items manually.")
            return
        finally:
            await _clear_temporary_status(loading_message)

    draft = repo.get_draft(user_id) or repo.create_draft(user_id)
    try:
        new_items = parse_line_items(transcript)
        if not await _validate_invoice_item_limit(message, len(draft.items), len(new_items)):
            return
        start_index = len(draft.items)
        draft.items.extend(new_items)
        repo.save_draft(draft)
        repo.increment_voice_usage(user_id)
        repo.consume_paid_voice_credit_if_needed(user_id, settings.free_voice_transcriptions_per_month)
        lines = "\n".join(
            _item_line(item, start_index + offset) for offset, item in enumerate(new_items)
        )
        await message.reply_text(
            "Voice note transcribed and added.\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"{lines}\n\n"
            f"You now have {len(draft.items)} item(s) in this draft.",
            reply_markup=_draft_editor_keyboard(draft),
        )
    except ValueError:
        await message.reply_text(
            "I transcribed the voice note, but couldn't turn it into invoice line items.\n\n"
            f"Transcript:\n{transcript}\n\n"
            "You are still in the same invoice draft. Send another voice note or type the item manually.\n\n"
            "Try phrases like:\n"
            "`Labour x 2 at $95`\n"
            "`Labour twice at $95`\n"
            "`Materials $45`",
            parse_mode="Markdown",
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _is_user_allowed(update, context):
        await query.edit_message_text(
            "This bot is currently locked to approved testers only.\n\n"
            "If you should have access, please contact the owner for beta access."
        )
        return
    repo = _repo(context)
    user_id = _user_key(update)

    if query.data == "edit_draft":
        draft = repo.get_draft(user_id)
        await query.edit_message_text("Draft still open. Use the controls below or send more line items.")
        await _send_draft_editor(query.message, draft)
        return

    if query.data == "client_edit_done":
        clients = repo.list_clients(user_id)
        await query.edit_message_text("Client edit finished.")
        await _send_clients_list(
            query.message,
            clients,
            page=context.user_data.get("clients_page", 0),
            query=context.user_data.get("clients_query", ""),
        )
        return

    if query.data.startswith("clients_page:"):
        page = int(query.data.split(":", 1)[1])
        context.user_data["clients_page"] = page
        await query.edit_message_text("Updated client list.")
        await _send_clients_list(
            query.message,
            repo.list_clients(user_id),
            page=page,
            query=context.user_data.get("clients_query", ""),
        )
        return

    if query.data == "clients_clear_search":
        context.user_data["clients_query"] = ""
        context.user_data["clients_page"] = 0
        await query.edit_message_text("Showing all saved clients.")
        await _send_clients_list(query.message, repo.list_clients(user_id), page=0, query="")
        return

    if query.data.startswith("skip_step:"):
        step = query.data.split(":", 1)[1]
        if step == "invoice_client_select":
            context.user_data["mode"] = "invoice_items"
            await query.edit_message_text("No client selected.")
            await _send_invoice_items_prompt(query.message)
            return
        if step == "profile_company_name":
            context.user_data["mode"] = "profile_address"
            profile = repo.get_or_create_profile(user_id)
            await query.edit_message_text("Keeping current company name.")
            await query.message.reply_text(
                _profile_step_prompt(profile, "address", "business address", "Now send your business address"),
                parse_mode="Markdown",
                reply_markup=_skip_keyboard("profile_address", label="Keep current") if profile.address else None,
            )
            return
        if step == "profile_address":
            context.user_data["mode"] = "profile_email"
            profile = repo.get_or_create_profile(user_id)
            await query.edit_message_text("Keeping current address.")
            await query.message.reply_text(
                _profile_step_prompt(profile, "email", "email", "Now send your business email"),
                parse_mode="Markdown",
                reply_markup=_skip_keyboard("profile_email", label="Keep current") if profile.email else None,
            )
            return
        if step == "profile_email":
            context.user_data["mode"] = "profile_phone"
            profile = repo.get_or_create_profile(user_id)
            await query.edit_message_text("Keeping current email.")
            await query.message.reply_text(
                _profile_step_prompt(profile, "phone", "phone", "Now send your business phone"),
                parse_mode="Markdown",
                reply_markup=_skip_keyboard("profile_phone", label="Keep current") if profile.phone else None,
            )
            return
        if step == "profile_phone":
            context.user_data["mode"] = "profile_gst_number"
            profile = repo.get_or_create_profile(user_id)
            await query.edit_message_text("Keeping current phone.")
            await query.message.reply_text(
                _profile_step_prompt(profile, "gst_number", "GST number", "Now send your GST number"),
                parse_mode="Markdown",
                reply_markup=_skip_keyboard("profile_gst_number", label="Keep current") if profile.gst_number else None,
            )
            return
        if step == "profile_gst_number":
            context.user_data["mode"] = "profile_logo"
            profile = repo.get_or_create_profile(user_id)
            await query.edit_message_text("Keeping current GST number.")
            logo_text, keyboard = _logo_prompt(profile)
            await query.message.reply_text(logo_text, reply_markup=keyboard)
            return
        if step == "profile_logo":
            context.user_data["mode"] = None
            await query.edit_message_text("Skipping logo upload for now.")
            await query.message.reply_text("Profile saved. Use /template to pick your default invoice layout.")
            return
        if step == "client_company":
            context.user_data["new_client_company"] = ""
            context.user_data["mode"] = "client_email"
            await query.edit_message_text("Skipping client company.")
            await query.message.reply_text("Send the client email.", reply_markup=_skip_keyboard("client_email"))
            return
        if step == "client_email":
            context.user_data["new_client_email"] = ""
            context.user_data["mode"] = "client_phone"
            await query.edit_message_text("Skipping client email.")
            await query.message.reply_text("Send the client phone.", reply_markup=_skip_keyboard("client_phone"))
            return
        if step == "client_phone":
            context.user_data["new_client_phone"] = ""
            context.user_data["mode"] = "client_address"
            await query.edit_message_text("Skipping client phone.")
            await query.message.reply_text("Send the client address.", reply_markup=_skip_keyboard("client_address"))
            return
        if step == "client_address":
            client = repo.add_client(
                user_id,
                name=context.user_data.pop("new_client_name", ""),
                company=context.user_data.pop("new_client_company", ""),
                email=context.user_data.pop("new_client_email", ""),
                phone=context.user_data.pop("new_client_phone", ""),
                address="",
            )
            context.user_data["mode"] = None
            await query.edit_message_text("Skipping client address.")
            await query.message.reply_text(f"Saved client {_client_summary(client)}.")
            return

    if query.data.startswith("pick_client:"):
        client_id = query.data.split(":", 1)[1]
        draft = repo.get_draft(user_id) or repo.create_draft(user_id)
        client = repo.get_client(user_id, client_id)
        if not client:
            await query.edit_message_text("That client is no longer available. Choose another client or skip.")
            return
        draft.client_id = client.id
        repo.save_draft(draft)
        context.user_data["mode"] = "invoice_items"
        await query.edit_message_text(f"Selected client: {client.name}.")
        await _send_invoice_items_prompt(query.message)
        return

    if query.data.startswith("client_edit:"):
        client_id = query.data.split(":", 1)[1]
        client = repo.get_client(user_id, client_id)
        if not client:
            await query.edit_message_text("That client is no longer available. Use /clients to refresh the list.")
            return
        await query.edit_message_text(
            f"Editing client: {_client_summary(client)}\n\nChoose a field to update.",
            reply_markup=_client_edit_keyboard(client.id),
        )
        return

    if query.data.startswith("client_field:"):
        _, client_id, field = query.data.split(":", 2)
        client = repo.get_client(user_id, client_id)
        if not client or field not in {"name", "company", "email", "phone", "address"}:
            await query.edit_message_text("That client is no longer available. Use /clients to refresh the list.")
            return
        context.user_data["mode"] = "edit_client_field"
        context.user_data["edit_client_id"] = client_id
        context.user_data["edit_client_field"] = field
        current_value = getattr(client, field)
        await query.edit_message_text(
            f"Current {field}: {current_value or 'not set'}\n\nSend the new {field}, or type `remove` to clear it.",
            parse_mode="Markdown",
        )
        return

    if query.data.startswith("client_delete:"):
        client_id = query.data.split(":", 1)[1]
        client = repo.get_client(user_id, client_id)
        if not client:
            await query.edit_message_text("That client is no longer available. Use /clients to refresh the list.")
            return
        repo.delete_client(user_id, client_id)
        await query.edit_message_text(f"Deleted client {client.name}.")
        await _send_clients_list(
            query.message,
            repo.list_clients(user_id),
            page=context.user_data.get("clients_page", 0),
            query=context.user_data.get("clients_query", ""),
        )
        return

    if query.data.startswith("edit_item:"):
        draft = repo.get_draft(user_id)
        item_index = int(query.data.split(":", 1)[1])
        if not draft or not (0 <= item_index < len(draft.items)):
            await query.edit_message_text("That item is no longer available. Use /invoice to continue.")
            return
        context.user_data["mode"] = "edit_draft_item"
        context.user_data["edit_item_index"] = item_index
        await query.edit_message_text(
            f"Send the replacement text for item {item_index + 1}:\n\n{_item_line(draft.items[item_index], item_index)}"
        )
        return

    if query.data.startswith("delete_item:"):
        draft = repo.get_draft(user_id)
        item_index = int(query.data.split(":", 1)[1])
        if not draft or not (0 <= item_index < len(draft.items)):
            await query.edit_message_text("That item is no longer available. Use /invoice to continue.")
            return
        removed_item = draft.items.pop(item_index)
        repo.save_draft(draft)
        if not draft.items:
            await query.edit_message_text(
                f"Deleted item {item_index + 1}: {removed_item.description}. The draft is now empty, so send a new line item."
            )
            return
        await query.edit_message_text(
            f"Deleted item {item_index + 1}: {removed_item.description}."
        )
        await _send_draft_editor(query.message, draft)
        return

    if query.data == "voice_continue_text":
        await query.edit_message_text(
            "Text mode is still available in this draft.\n\n"
            "Send line items like:\n"
            "Labour x 2 at $95\n"
            "Materials $45"
        )
        return

    if query.data == "buy_voice_credits":
        try:
            await _send_checkout_prompt(update, context, purchase_type="voice")
        except ValueError as exc:
            print(f"Voice checkout configuration error: {exc}")
            await query.edit_message_text(
                f"Voice checkout is not fully configured yet: {exc}"
            )
        except Exception:
            print("Voice checkout failed:")
            print(traceback.format_exc())
            await query.edit_message_text(
                "I couldn't create the voice checkout right now. Please try again in a moment or keep going with text."
            )
        else:
            await query.edit_message_text("Secure voice checkout ready below.")
        return

    if query.data == "buy_invoice_credits":
        try:
            await _send_checkout_prompt(update, context, purchase_type="invoice")
        except ValueError as exc:
            print(f"Invoice checkout configuration error: {exc}")
            await query.edit_message_text(
                f"Invoice checkout is not fully configured yet: {exc}"
            )
        except Exception:
            print("Invoice checkout failed:")
            print(traceback.format_exc())
            await query.edit_message_text(
                "I couldn't create the invoice checkout right now. Please try again in a moment."
            )
        else:
            await query.edit_message_text("Secure invoice checkout ready below.")
        return

    if query.data == "confirm_generate":
        draft = repo.get_draft(user_id)
        if not draft:
            await query.edit_message_text("Draft expired. Start again with /invoice.")
            return
        profile = repo.get_or_create_profile(user_id)
        client = repo.get_client(user_id, draft.client_id) if draft.client_id else None
        loading_message = await _send_temporary_status(query.message, "Generating invoice PDF...")
        try:
            pdf_bytes = render_invoice_pdf(profile, draft, client)
            repo.finalize_draft(user_id)
            repo.consume_paid_credit_if_needed(user_id, context.application.bot_data["settings"].free_invoice_limit)
            await query.edit_message_text("Invoice generated and sent below.")
            await query.message.reply_document(document=pdf_bytes, filename="invoice.pdf")
        finally:
            await _clear_temporary_status(loading_message)
