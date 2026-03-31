from __future__ import annotations

import logging

from telegram import BotCommand
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from invoicebot.config import Settings
from invoicebot.handlers.commands import (
    clients_command,
    generatequote_command,
    generate_command,
    handle_callback,
    handle_message,
    history_command,
    invoice_command,
    mockclients_command,
    myid_command,
    new_client_command,
    profile_command,
    promotions_command,
    quote_command,
    quotes_command,
    repeat_command,
    start_command,
    support_command,
    template_command,
    tracking_command,
)
from invoicebot.services.storage import InMemoryRepository, PostgresRepository


logging.basicConfig(level=logging.INFO)


def _bot_commands(settings: Settings) -> list[BotCommand]:
    commands = [
        BotCommand("start", "Start InvoiceBot"),
        BotCommand("invoice", "Start a new invoice"),
        BotCommand("tracking", "Start or stop tracked labour"),
        BotCommand("generate", "Generate the invoice PDF"),
        BotCommand("history", "View recent invoices"),
        BotCommand("repeat", "Repeat your latest invoice"),
        BotCommand("quote", "Start a new quote"),
        BotCommand("generatequote", "Generate the quote PDF"),
        BotCommand("quotes", "View recent quotes"),
        BotCommand("profile", "Set up your business details"),
        BotCommand("template", "Choose your invoice template"),
        BotCommand("newclient", "Add a new client"),
        BotCommand("clients", "View or edit saved clients"),
        BotCommand("support", "Send a bug or improvement ticket"),
    ]
    if settings.promotions_enabled:
        commands.append(BotCommand("promotions", "Choose affiliate promo preferences"))
    return commands


async def _post_init(application: Application) -> None:
    settings: Settings = application.bot_data["settings"]
    await application.bot.set_my_commands(_bot_commands(settings))


def build_application() -> Application:
    settings = Settings.from_env()
    application = Application.builder().token(settings.telegram_token).post_init(_post_init).build()
    application.bot_data["settings"] = settings
    application.bot_data["repo"] = PostgresRepository(settings.database_url) if settings.database_url else InMemoryRepository()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("myid", myid_command))
    application.add_handler(CommandHandler("mockclients", mockclients_command))
    application.add_handler(CommandHandler("invoice", invoice_command))
    application.add_handler(CommandHandler("tracking", tracking_command))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CommandHandler("quote", quote_command))
    application.add_handler(CommandHandler("generatequote", generatequote_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("template", template_command))
    application.add_handler(CommandHandler("newclient", new_client_command))
    application.add_handler(CommandHandler("clients", clients_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("quotes", quotes_command))
    application.add_handler(CommandHandler("repeat", repeat_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("promotions", promotions_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(
        MessageHandler((filters.TEXT | filters.VOICE | filters.AUDIO | filters.PHOTO | filters.Document.IMAGE) & ~filters.COMMAND, handle_message)
    )
    return application


def main() -> None:
    application = build_application()
    application.run_polling()


if __name__ == "__main__":
    main()
