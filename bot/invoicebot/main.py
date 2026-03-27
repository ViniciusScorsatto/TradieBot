from __future__ import annotations

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from invoicebot.config import Settings
from invoicebot.handlers.commands import (
    clients_command,
    generate_command,
    handle_callback,
    handle_message,
    history_command,
    invoice_command,
    new_client_command,
    profile_command,
    repeat_command,
    start_command,
    support_command,
    template_command,
)
from invoicebot.services.storage import InMemoryRepository


logging.basicConfig(level=logging.INFO)


def build_application() -> Application:
    settings = Settings.from_env()
    application = Application.builder().token(settings.telegram_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["repo"] = InMemoryRepository()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("invoice", invoice_command))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("template", template_command))
    application.add_handler(CommandHandler("newclient", new_client_command))
    application.add_handler(CommandHandler("clients", clients_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("repeat", repeat_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application


def main() -> None:
    application = build_application()
    application.run_polling()


if __name__ == "__main__":
    main()
