from __future__ import annotations

from dataclasses import replace
from tempfile import NamedTemporaryFile
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import ContextTypes

from invoicebot.models import SupportTicket
from invoicebot.services.billing import evaluate_quota
from invoicebot.services.checkout import create_checkout_session
from invoicebot.services.parser import parse_line_items
from invoicebot.services.pdf import render_invoice_pdf
from invoicebot.services.storage import Repository
from invoicebot.services.template_catalog import TEMPLATES
from invoicebot.services.transcription import transcribe_audio_file


def _user_key(update: Update) -> str:
    user = update.effective_user
    return str(user.id if user else "unknown")


def _repo(context: ContextTypes.DEFAULT_TYPE) -> Repository:
    return context.application.bot_data["repo"]


async def _send_temporary_status(message: Message | None, text: str) -> Message | None:
    if not message:
        return None
    return await message.reply_text(text)


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


def _invoice_limit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Unlock 20 more invoices", callback_data="buy_invoice_credits")]])


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
    await update.message.reply_text(
        "InvoiceBot helps tradies create invoices from voice or text in Telegram.\n\n"
        "Use /profile to set up your business, /template to pick a layout, and /invoice to start a draft."
    )


async def invoice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            "Invoice draft started. Choose a saved client by number, or type `skip` to continue without one.\n\n"
            f"{client_lines}",
            parse_mode="Markdown",
        )
    else:
        context.user_data["mode"] = "invoice_items"
        await update.message.reply_text(
            "Invoice draft started. No saved clients found, so we’ll start with line items.\n\n"
            "Send line items like:\n"
            "`Labour x 2 at $95`\n`Materials $45`\n\n"
            "You can send multiple lines at once, then use /generate.",
            parse_mode="Markdown",
        )
    if not draft.items:
        return


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    repo = _repo(context)
    profile = repo.get_or_create_profile(_user_key(update))
    context.user_data["mode"] = "profile_company_name"
    company_prompt = "Send your company name."
    if profile.company_name:
        company_prompt = "Send your company name, or type `skip` to keep it."
    await update.message.reply_text(
        "Let’s set up your business profile.\n"
        f"Current company name: {profile.company_name or 'not set'}\n"
        f"{company_prompt}",
        parse_mode="Markdown",
    )


async def template_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    options = "\n".join(f"{index + 1}. {template.name} - {template.description}" for index, template in enumerate(TEMPLATES))
    context.user_data["mode"] = "template_select"
    await update.message.reply_text(
        "Choose your default template by sending a number:\n\n"
        f"{options}"
    )


async def new_client_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "client_name"
    await update.message.reply_text("Send the client name to add a new client.")


async def clients_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo = _repo(context)
    clients = repo.list_clients(_user_key(update))
    if not clients:
        await update.message.reply_text("No saved clients yet. Use /newclient to add one.")
        return
    await update.message.reply_text("\n".join(f"- {client.name} ({client.company or 'no company'})" for client in clients))


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    repo = _repo(context)
    history = repo.list_history(_user_key(update))
    if not history:
        await update.message.reply_text("No recent invoices to repeat.")
        return
    new_draft = replace(history[0])
    repo.save_draft(new_draft)
    await update.message.reply_text("Loaded your most recent invoice as a new draft. Use /generate or send more items.")


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "support_type"
    await update.message.reply_text("Send a ticket type: Bug, Claim, Improvement, or Idea.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if update.message.voice or update.message.audio:
        await _handle_voice_message(update, context)
        return

    repo = _repo(context)
    user_id = _user_key(update)
    mode = context.user_data.get("mode")
    text = update.message.text.strip()

    if mode == "invoice_items":
        draft = repo.get_draft(user_id) or repo.create_draft(user_id)
        try:
            draft.items.extend(parse_line_items(text))
            repo.save_draft(draft)
            await update.message.reply_text(f"Added {len(draft.items)} item(s) so far. Use /generate when ready.")
        except ValueError as exc:
            await update.message.reply_text(str(exc))
        return

    if mode == "invoice_client_select":
        draft = repo.get_draft(user_id) or repo.create_draft(user_id)
        if text.lower() == "skip":
            context.user_data["mode"] = "invoice_items"
            await update.message.reply_text(
                "No client selected. Now send line items like:\n"
                "`Labour x 2 at $95`\n`Materials $45`\n\n"
                "You can send multiple lines at once, then use /generate.",
                parse_mode="Markdown",
            )
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
        await update.message.reply_text(
            f"Selected client: {client.name}.\n\n"
            "Now send line items like:\n"
            "`Labour x 2 at $95`\n`Materials $45`\n\n"
            "You can send multiple lines at once, then use /generate.",
            parse_mode="Markdown",
        )
        return

    if mode == "profile_company_name":
        profile = repo.get_or_create_profile(user_id)
        if text.lower() != "skip" or not profile.company_name:
            profile.company_name = text
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = "profile_gst_number"
        gst_prompt = (
            "Saved. Now send your GST number."
            if not profile.gst_number
            else f"Saved. Current GST number: {profile.gst_number}\nSend your GST number, or type `skip` to keep it."
        )
        await update.message.reply_text(gst_prompt, parse_mode="Markdown")
        return

    if mode == "profile_gst_number":
        profile = repo.get_or_create_profile(user_id)
        if text.lower() != "skip" or not profile.gst_number:
            profile.gst_number = text
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = None
        await update.message.reply_text("Profile saved. Use /template to pick your default invoice layout.")
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
        client = repo.add_client(user_id, name=text)
        context.user_data["mode"] = None
        await update.message.reply_text(f"Saved client {client.name}.")
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
        draft.items.extend(parse_line_items(transcript))
        repo.save_draft(draft)
        repo.increment_voice_usage(user_id)
        repo.consume_paid_voice_credit_if_needed(user_id, settings.free_voice_transcriptions_per_month)
        await message.reply_text(
            "Voice note transcribed and added.\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"You now have {len(draft.items)} item(s) in this draft."
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
    repo = _repo(context)
    user_id = _user_key(update)

    if query.data == "edit_draft":
        await query.edit_message_text("Draft still open. Send more line items and run /generate again.")
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
