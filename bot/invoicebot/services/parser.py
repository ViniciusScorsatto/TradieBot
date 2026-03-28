from __future__ import annotations

import re

from invoicebot.models import InvoiceItem


NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}

TENS_WORDS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

QTY_FIRST_RE = re.compile(
    r"^\s*(?P<description>.+?)\s*(?:x|×)\s*(?P<quantity>\d+(?:\.\d+)?)\s*(?:at\s*)?\$?(?P<price>\d+(?:\.\d{1,2})?)\s*$",
    re.IGNORECASE,
)

QTY_NATURAL_RE = re.compile(
    r"^\s*(?P<description>.+?)\s+(?P<quantity>\d+(?:\.\d+)?)\s*(?:x|times?)\s*(?:at\s*)?\$?(?P<price>\d+(?:\.\d{1,2})?)(?:\s*(?:dollars?)?\s*(?:each)?)?\s*$",
    re.IGNORECASE,
)

QTY_COMMA_PRICE_RE = re.compile(
    r"^\s*(?P<description>.+?)\s*(?:x|×)\s*(?P<quantity>\d+(?:\.\d+)?)\s*,\s*\$?(?P<price>\d+(?:\.\d{1,2})?)\s*$",
    re.IGNORECASE,
)

EACH_RE = re.compile(
    r"^\s*(?P<description>.+?)\s+(?P<quantity>\d+(?:\.\d+)?)\s*(?:times?)\s*(?:at\s*)?\$?(?P<price>\d+(?:\.\d{1,2})?)\s*(?:dollars?)?\s*(?:each)?\s*$",
    re.IGNORECASE,
)

TIMES_BEFORE_QTY_RE = re.compile(
    r"^\s*(?P<description>.+?)\s+times\s+(?P<quantity>\d+(?:\.\d+)?)\s*,?\s*\$?(?P<price>\d+(?:\.\d{1,2})?)(?:\s*(?:dollars?)?)?\s*$",
    re.IGNORECASE,
)

PRICE_ONLY_RE = re.compile(
    r"^\s*(?P<description>.+?)\s+\$?(?P<price>\d+(?:\.\d{1,2})?)\s*(?:dollars?)?\s*$",
    re.IGNORECASE,
)

PRICE_COMMA_RE = re.compile(
    r"^\s*(?P<description>.+?)\s*,\s*\$?(?P<price>\d+(?:\.\d{1,2})?)\s*$",
    re.IGNORECASE,
)


def _normalize_spoken_numbers(text: str) -> str:
    normalized = text
    normalized = re.sub(r"\bonce\b", "x 1", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\btwice\b", "x 2", normalized, flags=re.IGNORECASE)
    for word, base in TENS_WORDS.items():
        normalized = re.sub(
            rf"\b{word}(?:[-\s]+(one|two|three|four|five|six|seven|eight|nine))\b",
            lambda match: str(base + int(NUMBER_WORDS[match.group(1).lower()])),
            normalized,
            flags=re.IGNORECASE,
        )
        normalized = re.sub(rf"\b{word}\b", str(base), normalized, flags=re.IGNORECASE)
    for word, value in NUMBER_WORDS.items():
        normalized = re.sub(rf"\b{word}\b", value, normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\b(\d+)\s+times\b", r"\1 x", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\btimes\s+(\d+)\b", r"x \1", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bx\s+(\d+)\s*,\s*\$?(\d+(?:\.\d{1,2})?)\b", r"x \1 at $\2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\beach\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bdollars?\b", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"[.!?]+$", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _build_item(description: str, quantity: float, unit_price: float) -> InvoiceItem:
    cleaned_description = description.strip(" ,.-")
    normalized_description = (
        cleaned_description[:1].upper() + cleaned_description[1:]
        if cleaned_description
        else cleaned_description
    )
    return InvoiceItem(
        description=normalized_description,
        quantity=quantity,
        unit_price_cents=int(round(unit_price * 100)),
    )


def parse_line_items(text: str) -> list[InvoiceItem]:
    items: list[InvoiceItem] = []
    for raw_line in [line.strip("-• ").strip() for line in text.splitlines() if line.strip()]:
        normalized = _normalize_spoken_numbers(raw_line)

        for pattern in (QTY_FIRST_RE, QTY_COMMA_PRICE_RE, QTY_NATURAL_RE, EACH_RE, TIMES_BEFORE_QTY_RE):
            match = pattern.match(normalized)
            if match:
                items.append(
                    _build_item(
                        description=match.group("description"),
                        quantity=float(match.group("quantity")),
                        unit_price=float(match.group("price")),
                    )
                )
                break
        else:
            match = PRICE_ONLY_RE.match(normalized) or PRICE_COMMA_RE.match(normalized)
            if match:
                items.append(
                    _build_item(
                        description=match.group("description"),
                        quantity=1,
                        unit_price=float(match.group("price")),
                    )
                )
                continue

            raise ValueError(f"Could not parse line item: {raw_line}")

    return items
