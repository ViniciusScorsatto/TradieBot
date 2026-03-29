import unittest

from invoicebot.models import Client, InvoiceDraft, InvoiceItem, Profile
from invoicebot.services.compliance import taxable_supply_gaps


class TaxableSupplyComplianceTests(unittest.TestCase):
    def test_requires_business_name_and_address(self) -> None:
        profile = Profile()
        draft = InvoiceDraft(
            user_id="user-1",
            items=[InvoiceItem(description="Service", quantity=1, unit_price_cents=10000)],
        )

        gaps = taxable_supply_gaps(profile, draft, None)

        self.assertIn("Add your business name in /profile.", gaps)
        self.assertIn("Add your business address in /profile.", gaps)

    def test_requires_client_for_gst_invoice(self) -> None:
        profile = Profile(company_name="Tradies NZ", address="1 Test Street", gst_number="123-456-789")
        draft = InvoiceDraft(
            user_id="user-1",
            items=[InvoiceItem(description="Service", quantity=1, unit_price_cents=10000)],
        )

        gaps = taxable_supply_gaps(profile, draft, None)

        self.assertIn("Select a client before generating a GST invoice.", gaps)

    def test_requires_extra_recipient_identifier_for_large_gst_invoice(self) -> None:
        profile = Profile(company_name="Tradies NZ", address="1 Test Street", gst_number="123-456-789")
        client = Client(id="c1", name="Sophie Taylor")
        draft = InvoiceDraft(
            user_id="user-1",
            items=[InvoiceItem(description="Project work", quantity=1, unit_price_cents=100000)],
            client_id=client.id,
        )

        gaps = taxable_supply_gaps(profile, draft, client)

        self.assertIn(
            "For invoices of NZD $1,000 or more, add at least one client identifier such as address, email, phone, or company in /clients.",
            gaps,
        )

    def test_accepts_large_gst_invoice_with_extra_client_identifier(self) -> None:
        profile = Profile(company_name="Tradies NZ", address="1 Test Street", gst_number="123-456-789")
        client = Client(id="c1", name="Sophie Taylor", email="sophie@example.com")
        draft = InvoiceDraft(
            user_id="user-1",
            items=[InvoiceItem(description="Project work", quantity=1, unit_price_cents=100000)],
            client_id=client.id,
        )

        gaps = taxable_supply_gaps(profile, draft, client)

        self.assertEqual(gaps, [])


if __name__ == "__main__":
    unittest.main()
