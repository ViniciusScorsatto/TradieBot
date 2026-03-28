from __future__ import annotations

from invoicebot.models import InvoiceDraft, Profile


GST_RATE = 0.15


def is_gst_registered(profile: Profile) -> bool:
    return bool(profile.gst_number.strip())


def subtotal_cents(draft: InvoiceDraft) -> int:
    return sum(item.line_total_cents for item in draft.items)


def gross_subtotal_cents(draft: InvoiceDraft) -> int:
    return sum(item.gross_total_cents for item in draft.items)


def discount_total_cents(draft: InvoiceDraft) -> int:
    return sum(item.discount_cents for item in draft.items)


def gst_cents(draft: InvoiceDraft, profile: Profile) -> int:
    if not is_gst_registered(profile):
        return 0
    return int(round(subtotal_cents(draft) * GST_RATE))


def total_cents(draft: InvoiceDraft, profile: Profile) -> int:
    return subtotal_cents(draft) + gst_cents(draft, profile)


def gst_label(profile: Profile) -> str:
    return "15%" if is_gst_registered(profile) else "-"


def gst_summary_label(profile: Profile) -> str:
    return "GST (15%)" if is_gst_registered(profile) else "GST"
