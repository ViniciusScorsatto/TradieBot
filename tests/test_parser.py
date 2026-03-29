from invoicebot.services.parser import parse_line_items
import pytest


def test_parse_line_items_supports_quantity_syntax() -> None:
    items = parse_line_items("Labour x 2 at $95\nMaterials $45")

    assert len(items) == 2
    assert items[0].description == "Labour"
    assert items[0].quantity == 2
    assert items[0].unit_price_cents == 9500
    assert items[1].description == "Materials"
    assert items[1].line_total_cents == 4500


def test_parse_line_items_supports_natural_voice_phrasing() -> None:
    items = parse_line_items("Labor two times at $95 each")

    assert len(items) == 1
    assert items[0].description == "Labor"
    assert items[0].quantity == 2
    assert items[0].unit_price_cents == 9500
    assert items[0].line_total_cents == 19000


def test_parse_line_items_supports_price_without_dollar_symbol() -> None:
    items = parse_line_items("Materials 45 dollars")

    assert len(items) == 1
    assert items[0].description == "Materials"
    assert items[0].quantity == 1
    assert items[0].unit_price_cents == 4500


def test_parse_line_items_supports_comma_price_shorthand() -> None:
    items = parse_line_items("materials,50")

    assert len(items) == 1
    assert items[0].description == "Materials"
    assert items[0].quantity == 1
    assert items[0].unit_price_cents == 5000


def test_parse_line_items_supports_twice_and_trailing_punctuation() -> None:
    items = parse_line_items("Labor twice, $95.")

    assert len(items) == 1
    assert items[0].description == "Labor"
    assert items[0].quantity == 2
    assert items[0].unit_price_cents == 9500


def test_parse_line_items_supports_times_before_quantity() -> None:
    items = parse_line_items("Labor times two, ninety-five dollars.")

    assert len(items) == 1
    assert items[0].description == "Labor"
    assert items[0].quantity == 2
    assert items[0].unit_price_cents == 9500


def test_parse_line_items_supports_compact_multi_item_voice_phrasing() -> None:
    items = parse_line_items("wood 50 service 100 materials 45")

    assert len(items) == 3
    assert [item.description for item in items] == ["Wood", "Service", "Materials"]
    assert [item.unit_price_cents for item in items] == [5000, 10000, 4500]


def test_parse_line_items_supports_comma_separated_multi_item_voice_phrasing() -> None:
    items = parse_line_items("Wood 50, Surface 100, Materials 45")

    assert len(items) == 3
    assert [item.description for item in items] == ["Wood", "Surface", "Materials"]
    assert [item.unit_price_cents for item in items] == [5000, 10000, 4500]


def test_parse_line_items_supports_sentence_separated_multi_item_voice_phrasing() -> None:
    items = parse_line_items("Wood 45. Service 100. Materials 45.")

    assert len(items) == 3
    assert [item.description for item in items] == ["Wood", "Service", "Materials"]
    assert [item.unit_price_cents for item in items] == [4500, 10000, 4500]


def test_parse_line_items_rejects_long_descriptions() -> None:
    long_description = "A" * 81

    with pytest.raises(ValueError, match="80 characters or fewer"):
        parse_line_items(f"{long_description} $50")
