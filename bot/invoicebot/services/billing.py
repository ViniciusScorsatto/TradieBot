from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BillingDecision:
    allowed: bool
    message: str | None = None
    warning: str | None = None


def evaluate_quota(invoice_count_this_month: int, paid_credits: int, free_limit: int, warning_threshold: int) -> BillingDecision:
    if invoice_count_this_month >= free_limit and paid_credits <= 0:
        return BillingDecision(
            allowed=False,
            message="You have used your 10 free invoices this month. Pay NZD $5 to unlock another block of 10 invoices.",
        )
    if invoice_count_this_month == warning_threshold:
        return BillingDecision(
            allowed=True,
            warning="You have 2 free invoices left this month. After 10, the bot will send a Stripe payment link.",
        )
    return BillingDecision(allowed=True)
