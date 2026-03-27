from __future__ import annotations

import re

from invoicebot.models import InvoiceItem


LINE_RE = re.compile(
    r"^\s*(?P<description>.+?)\s*(?:x|@)\s*(?P<quantity>\d+(?:\.\d+)?)\s*(?:at\s*)?\$?(?P<price>\d+(?:\.\d{1,2})?)\s*$",
    re.IGNORECASE,
)


def parse_line_items(text: str) -> list[InvoiceItem]:
    items: list[InvoiceItem] = []
    for raw_line in [line.strip("-• ").strip() for line in text.splitlines() if line.strip()]:
        match = LINE_RE.match(raw_line)
        if match:
            quantity = float(match.group("quantity"))
            unit_price_cents = int(round(float(match.group("price")) * 100))
            items.append(
                InvoiceItem(
                    description=match.group("description").strip(),
                    quantity=quantity,
                    unit_price_cents=unit_price_cents,
                )
            )
            continue

        if "$" in raw_line:
            description, price = raw_line.rsplit("$", 1)
            items.append(
                InvoiceItem(
                    description=description.strip(),
                    quantity=1,
                    unit_price_cents=int(round(float(price.strip()) * 100)),
                )
            )
            continue

        raise ValueError(f"Could not parse line item: {raw_line}")
    return items
