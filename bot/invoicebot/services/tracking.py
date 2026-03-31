from __future__ import annotations

from invoicebot.models import InvoiceItem


def round_tracked_hours(seconds: int) -> float:
    hours = max(seconds, 0) / 3600
    return max(0.1, round(hours * 10) / 10)


def build_tracked_item(*, elapsed_seconds: int, hourly_rate_cents: int, description: str = "Tracked labour") -> InvoiceItem:
    return InvoiceItem(
        description=description,
        quantity=round_tracked_hours(elapsed_seconds),
        unit_price_cents=hourly_rate_cents,
    )
