from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    telegram_token: str
    database_url: str
    openai_api_key: str
    openai_support_model: str
    openai_support_vector_store_id: str
    openai_support_daily_limit: int
    mailjet_api_key: str
    mailjet_secret_key: str
    email_from: str
    stripe_secret_key: str
    stripe_invoice_price_id: str
    stripe_voice_price_id: str
    marketing_site_url: str
    environment: str
    promotions_enabled: bool
    allowed_telegram_user_ids: tuple[str, ...]
    admin_telegram_user_ids: tuple[str, ...]
    warning_threshold: int = 8
    free_invoice_limit: int = 10
    paid_invoice_block: int = 20
    invoice_bundle_voice_minutes: int = 10
    paid_voice_minutes: int = 10
    free_voice_minutes_per_month: int = 5
    voice_note_max_seconds: int = 60

    @classmethod
    def from_env(cls) -> "Settings":
        promotions_raw = os.getenv("ENABLE_PROMOTIONS", "false").strip().lower()
        return cls(
            telegram_token=os.getenv("TELEGRAM_TOKEN", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_support_model=os.getenv("OPENAI_SUPPORT_MODEL", "gpt-4.1-mini"),
            openai_support_vector_store_id=os.getenv("OPENAI_SUPPORT_VECTOR_STORE_ID", ""),
            openai_support_daily_limit=int(os.getenv("OPENAI_SUPPORT_DAILY_LIMIT", "3")),
            mailjet_api_key=os.getenv("MAILJET_API_KEY", ""),
            mailjet_secret_key=os.getenv("MAILJET_SECRET_KEY", ""),
            email_from=os.getenv("EMAIL_FROM", ""),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            stripe_invoice_price_id=os.getenv("STRIPE_INVOICE_PRICE_ID", ""),
            stripe_voice_price_id=os.getenv("STRIPE_VOICE_PRICE_ID", ""),
            marketing_site_url=os.getenv("MARKETING_SITE_URL", ""),
            environment=os.getenv("APP_ENV", "production").strip().lower() or "production",
            promotions_enabled=promotions_raw in {"1", "true", "yes", "on"},
            allowed_telegram_user_ids=tuple(
                value.strip()
                for value in os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").split(",")
                if value.strip()
            ),
            admin_telegram_user_ids=tuple(
                value.strip()
                for value in os.getenv("ADMIN_TELEGRAM_USER_IDS", "").split(",")
                if value.strip()
            ),
            warning_threshold=int(os.getenv("WARNING_THRESHOLD", "8")),
            free_invoice_limit=int(os.getenv("FREE_INVOICE_LIMIT", "10")),
            paid_invoice_block=int(os.getenv("PAID_INVOICE_BLOCK", "20")),
            invoice_bundle_voice_minutes=int(os.getenv("INVOICE_BUNDLE_VOICE_MINUTES", "10")),
            paid_voice_minutes=int(os.getenv("PAID_VOICE_MINUTES", os.getenv("PAID_VOICE_BLOCK", "10"))),
            free_voice_minutes_per_month=int(
                os.getenv("FREE_VOICE_MINUTES_PER_MONTH", os.getenv("FREE_VOICE_TRANSCRIPTIONS_PER_MONTH", "5"))
            ),
            voice_note_max_seconds=int(os.getenv("VOICE_NOTE_MAX_SECONDS", "60")),
        )
