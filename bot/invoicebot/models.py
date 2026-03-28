from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


TemplateId = Literal[
    "classic-blue",
    "trade-orange",
    "forest-ledger",
    "graphite-pro",
    "sunset-statement",
]


@dataclass(slots=True)
class InvoiceItem:
    description: str
    quantity: float
    unit_price_cents: int

    @property
    def line_total_cents(self) -> int:
        return int(round(self.quantity * self.unit_price_cents))


@dataclass(slots=True)
class Profile:
    company_name: str = ""
    address: str = ""
    gst_number: str = ""
    email: str = ""
    phone: str = ""
    bank_details: str = ""
    logo_url: str = ""
    default_template_id: TemplateId = "classic-blue"
    invoice_prefix: str = "INV"
    next_invoice_number: int = 1


@dataclass(slots=True)
class Client:
    id: str
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""


@dataclass(slots=True)
class InvoiceDraft:
    user_id: str
    items: list[InvoiceItem] = field(default_factory=list)
    client_id: str | None = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def subtotal_cents(self) -> int:
        return sum(item.line_total_cents for item in self.items)

    @property
    def gst_cents(self) -> int:
        return int(round(self.subtotal_cents * 0.15))

    @property
    def total_cents(self) -> int:
        return self.subtotal_cents + self.gst_cents


@dataclass(slots=True)
class SupportTicket:
    user_id: str
    kind: Literal["BUG", "CLAIM", "IMPROVEMENT", "IDEA"]
    subject: str
    body: str
