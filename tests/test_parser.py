from invoicebot.services.parser import parse_line_items


def test_parse_line_items_supports_quantity_syntax() -> None:
    items = parse_line_items("Labour x 2 at $95\nMaterials $45")

    assert len(items) == 2
    assert items[0].description == "Labour"
    assert items[0].quantity == 2
    assert items[0].unit_price_cents == 9500
    assert items[1].description == "Materials"
    assert items[1].line_total_cents == 4500
