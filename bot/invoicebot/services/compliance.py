from __future__ import annotations

from invoicebot.models import Client, InvoiceDraft, Profile
from invoicebot.services.tax import total_cents


NZ_RECIPIENT_DETAILS_THRESHOLD_CENTS = 100_000


def taxable_supply_gaps(profile: Profile, draft: InvoiceDraft, client: Client | None) -> list[str]:
    gaps: list[str] = []

    if not profile.company_name.strip():
        gaps.append("Add your business name in /profile.")

    if not profile.address.strip():
        gaps.append("Add your business address in /profile.")

    if profile.gst_number.strip():
        if not client:
            gaps.append("Select a client before generating a GST invoice.")
        elif total_cents(draft, profile) >= NZ_RECIPIENT_DETAILS_THRESHOLD_CENTS and not _has_extra_recipient_identifier(client):
            gaps.append(
                "For invoices of NZD $1,000 or more, add at least one client identifier such as address, email, phone, or company in /clients."
            )

    return gaps


def _has_extra_recipient_identifier(client: Client) -> bool:
    return any(
        value.strip()
        for value in (
            client.address,
            client.email,
            client.phone,
            client.company,
        )
    )
