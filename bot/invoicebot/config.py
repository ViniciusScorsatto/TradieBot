from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    telegram_token: str
    database_url: str
    openai_api_key: str
    stripe_secret_key: str
    stripe_price_id: str
    marketing_site_url: str
    warning_threshold: int = 8
    free_invoice_limit: int = 10
    paid_invoice_block: int = 10
    free_voice_transcriptions_per_month: int = 3
    voice_note_max_seconds: int = 90

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_token=os.getenv("TELEGRAM_TOKEN", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            stripe_price_id=os.getenv("STRIPE_PRICE_ID", ""),
            marketing_site_url=os.getenv("MARKETING_SITE_URL", ""),
            free_voice_transcriptions_per_month=int(os.getenv("FREE_VOICE_TRANSCRIPTIONS_PER_MONTH", "3")),
            voice_note_max_seconds=int(os.getenv("VOICE_NOTE_MAX_SECONDS", "90")),
        )
