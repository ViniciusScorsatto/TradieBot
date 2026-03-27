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
    warning_threshold: int = 8
    free_invoice_limit: int = 10
    paid_invoice_block: int = 10

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_token=os.getenv("TELEGRAM_TOKEN", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", ""),
            stripe_price_id=os.getenv("STRIPE_PRICE_ID", ""),
        )
