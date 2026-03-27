from __future__ import annotations

from dataclasses import replace

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from invoicebot.models import SupportTicket
from invoicebot.services.billing import evaluate_quota
from invoicebot.services.parser import parse_line_items
from invoicebot.services.pdf import render_invoice_pdf
from invoicebot.services.storage import InMemoryRepository
from invoicebot.services.template_catalog import TEMPLATES


def _user_key(update: Update) -> str:
    user = update.effective_user
    return str(user.id if user else "unknown")


def _repo(context: ContextTypes.DEFAULT_TYPE) -> InMemoryRepository:
    return context.application.bot_data["repo"]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "InvoiceBot helps tradies create invoices from voice or text in Telegram.\n\n"
        "Use /profile to set up your business, /template to pick a layout, and /invoice to start a draft."
    )


async def invoice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo = _repo(context)
    user_id = _user_key(update)
    draft = repo.create_draft(user_id)
    context.user_data["mode"] = "invoice_items"
    await update.message.reply_text(
        "Invoice draft started. Send line items like:\n"
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

    decision = evaluate_quota(
        invoice_count_this_month=repo.invoice_counts[user_id],
        paid_credits=repo.credits[user_id],
        free_limit=context.application.bot_data["settings"].free_invoice_limit,
        warning_threshold=context.application.bot_data["settings"].warning_threshold,
    )
    if decision.warning:
        await update.message.reply_text(decision.warning)
    if not decision.allowed:
        await update.message.reply_text(decision.message or "Payment required.")
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
        f"Please confirm this invoice:\n\n{lines}\n\n"
        f"Subtotal: ${draft.subtotal_cents / 100:.2f}\nGST: ${draft.gst_cents / 100:.2f}\nTotal: ${draft.total_cents / 100:.2f}",
        reply_markup=keyboard,
    )


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    repo = _repo(context)
    profile = repo.get_or_create_profile(_user_key(update))
    context.user_data["mode"] = "profile_company_name"
    await update.message.reply_text(
        "Let’s set up your business profile.\n"
        f"Current company name: {profile.company_name or 'not set'}\n"
        "Send your company name."
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
    if not update.message or not update.message.text:
        await update.message.reply_text("Text messages are supported in this scaffold. Voice transcription hooks can be added next.")
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

    if mode == "profile_company_name":
        profile = repo.get_or_create_profile(user_id)
        profile.company_name = text
        repo.save_profile(user_id, profile)
        context.user_data["mode"] = "profile_gst_number"
        await update.message.reply_text("Saved. Now send your GST number, or type `skip`.", parse_mode="Markdown")
        return

    if mode == "profile_gst_number":
        profile = repo.get_or_create_profile(user_id)
        profile.gst_number = "" if text.lower() == "skip" else text
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


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    repo = _repo(context)
    user_id = _user_key(update)

    if query.data == "edit_draft":
        await query.edit_message_text("Draft still open. Send more line items and run /generate again.")
        return

    if query.data == "confirm_generate":
        draft = repo.get_draft(user_id)
        if not draft:
            await query.edit_message_text("Draft expired. Start again with /invoice.")
            return
        profile = repo.get_or_create_profile(user_id)
        pdf_bytes = render_invoice_pdf(profile, draft, None)
        repo.finalize_draft(user_id)
        repo.consume_paid_credit_if_needed(user_id, context.application.bot_data["settings"].free_invoice_limit)
        await query.edit_message_text("Invoice generated and sent below.")
        await query.message.reply_document(document=pdf_bytes, filename="invoice.pdf")
