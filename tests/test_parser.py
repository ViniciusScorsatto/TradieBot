import unittest

from invoicebot.services.parser import parse_line_items


class ParseLineItemsTests(unittest.TestCase):
    def test_supports_quantity_syntax(self) -> None:
        items = parse_line_items("Labour x 2 at $95\nMaterials $45")

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].description, "Labour")
        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(items[0].unit_price_cents, 9500)
        self.assertEqual(items[1].description, "Materials")
        self.assertEqual(items[1].line_total_cents, 4500)

    def test_supports_natural_voice_phrasing(self) -> None:
        items = parse_line_items("Labor two times at $95 each")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].description, "Labor")
        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(items[0].unit_price_cents, 9500)
        self.assertEqual(items[0].line_total_cents, 19000)

    def test_supports_price_without_dollar_symbol(self) -> None:
        items = parse_line_items("Materials 45 dollars")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].description, "Materials")
        self.assertEqual(items[0].quantity, 1)
        self.assertEqual(items[0].unit_price_cents, 4500)

    def test_supports_comma_price_shorthand(self) -> None:
        items = parse_line_items("materials,50")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].description, "Materials")
        self.assertEqual(items[0].quantity, 1)
        self.assertEqual(items[0].unit_price_cents, 5000)

    def test_supports_twice_and_trailing_punctuation(self) -> None:
        items = parse_line_items("Labor twice, $95.")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].description, "Labor")
        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(items[0].unit_price_cents, 9500)

    def test_supports_times_before_quantity(self) -> None:
        items = parse_line_items("Labor times two, ninety-five dollars.")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].description, "Labor")
        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(items[0].unit_price_cents, 9500)

    def test_supports_compact_multi_item_voice_phrasing(self) -> None:
        items = parse_line_items("wood 50 service 100 materials 45")

        self.assertEqual(len(items), 3)
        self.assertEqual([item.description for item in items], ["Wood", "Service", "Materials"])
        self.assertEqual([item.unit_price_cents for item in items], [5000, 10000, 4500])

    def test_supports_comma_separated_multi_item_voice_phrasing(self) -> None:
        items = parse_line_items("Wood 50, Surface 100, Materials 45")

        self.assertEqual(len(items), 3)
        self.assertEqual([item.description for item in items], ["Wood", "Surface", "Materials"])
        self.assertEqual([item.unit_price_cents for item in items], [5000, 10000, 4500])

    def test_supports_sentence_separated_multi_item_voice_phrasing(self) -> None:
        items = parse_line_items("Wood 45. Service 100. Materials 45.")

        self.assertEqual(len(items), 3)
        self.assertEqual([item.description for item in items], ["Wood", "Service", "Materials"])
        self.assertEqual([item.unit_price_cents for item in items], [4500, 10000, 4500])

    def test_rejects_long_descriptions(self) -> None:
        long_description = "A" * 81

        with self.assertRaisesRegex(ValueError, "80 characters or fewer"):
            parse_line_items(f"{long_description} $50")


if __name__ == "__main__":
    unittest.main()
