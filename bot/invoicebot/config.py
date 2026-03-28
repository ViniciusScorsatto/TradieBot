from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    telegram_token: str
    database_url: str
    openai_api_key: str
    stripe_secret_key: str
    stripe_invoice_price_id: str
    stripe_voice_price_id: str
    marketing_site_url: str
    allowed_telegram_user_ids: tuple[str, ...]
    warning_threshold: int = 8
    free_invoice_limit: int = 10
    paid_invoice_block: int = 20
    paid_voice_block: int = 100
    free_voice_transcriptions_per_month: int = 20
    voice_note_max_seconds: int = 60

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_token=os.getenv("TELEGRAM_TOKEN", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            stripe_invoice_price_id=os.getenv("STRIPE_INVOICE_PRICE_ID", ""),
            stripe_voice_price_id=os.getenv("STRIPE_VOICE_PRICE_ID", ""),
            marketing_site_url=os.getenv("MARKETING_SITE_URL", ""),
            allowed_telegram_user_ids=tuple(
                value.strip()
                for value in os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").split(",")
                if value.strip()
            ),
            warning_threshold=int(os.getenv("WARNING_THRESHOLD", "8")),
            free_invoice_limit=int(os.getenv("FREE_INVOICE_LIMIT", "10")),
            paid_invoice_block=int(os.getenv("PAID_INVOICE_BLOCK", "20")),
            paid_voice_block=int(os.getenv("PAID_VOICE_BLOCK", "100")),
            free_voice_transcriptions_per_month=int(os.getenv("FREE_VOICE_TRANSCRIPTIONS_PER_MONTH", "20")),
            voice_note_max_seconds=int(os.getenv("VOICE_NOTE_MAX_SECONDS", "60")),
        )
