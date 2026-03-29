from __future__ import annotations

import re

from invoicebot.models import InvoiceItem


MAX_ITEM_DESCRIPTION_LENGTH = 80


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

COMPACT_PRICE_CHUNK_RE = re.compile(
    r"""
    (?P<description>[A-Za-z][A-Za-z0-9&'/+\-]*(?:\s+[A-Za-z][A-Za-z0-9&'/+\-]*)*)
    \s*,?\s*
    \$?(?P<price>\d+(?:\.\d{1,2})?)
    (?=
        \s+[A-Za-z]
        |\s*$
    )
    """,
    re.IGNORECASE | re.VERBOSE,
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
    if len(normalized_description) > MAX_ITEM_DESCRIPTION_LENGTH:
        raise ValueError(
            f"Item descriptions must be {MAX_ITEM_DESCRIPTION_LENGTH} characters or fewer."
        )
    return InvoiceItem(
        description=normalized_description,
        quantity=quantity,
        unit_price_cents=int(round(unit_price * 100)),
    )


def _parse_single_line_item(raw_line: str) -> InvoiceItem:
    normalized = _normalize_spoken_numbers(raw_line)

    for pattern in (QTY_FIRST_RE, QTY_COMMA_PRICE_RE, QTY_NATURAL_RE, EACH_RE, TIMES_BEFORE_QTY_RE):
        match = pattern.match(normalized)
        if match:
            return _build_item(
                description=match.group("description"),
                quantity=float(match.group("quantity")),
                unit_price=float(match.group("price")),
            )

    match = PRICE_ONLY_RE.match(normalized) or PRICE_COMMA_RE.match(normalized)
    if match:
        return _build_item(
            description=match.group("description"),
            quantity=1,
            unit_price=float(match.group("price")),
        )

    raise ValueError(f"Could not parse line item: {raw_line}")


def _parse_compact_price_chunks(raw_line: str) -> list[InvoiceItem] | None:
    normalized = _normalize_spoken_numbers(raw_line)
    if re.search(r"\b(?:x|times?|at|each)\b", normalized, flags=re.IGNORECASE):
        return None
    matches = list(COMPACT_PRICE_CHUNK_RE.finditer(normalized))
    if len(matches) < 2:
        return None

    consumed = " ".join(match.group(0).strip() for match in matches)
    if re.sub(r"\s+", " ", consumed).strip() != normalized:
        return None

    items: list[InvoiceItem] = []
    for match in matches:
        items.append(
            _build_item(
                description=match.group("description"),
                quantity=1,
                unit_price=float(match.group("price")),
            )
        )
    return items


def parse_line_items(text: str) -> list[InvoiceItem]:
    items: list[InvoiceItem] = []
    for raw_line in [line.strip("-• ").strip() for line in text.splitlines() if line.strip()]:
        compact_items = _parse_compact_price_chunks(raw_line)
        if compact_items:
            items.extend(compact_items)
            continue
        try:
            items.append(_parse_single_line_item(raw_line))
            continue
        except ValueError:
            raise

    return items
