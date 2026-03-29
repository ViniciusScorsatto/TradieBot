from datetime import UTC, datetime
import importlib.util
import unittest

from invoicebot.models import Client, InvoiceDraft, InvoiceItem, Profile

REPORTLAB_AVAILABLE = importlib.util.find_spec("reportlab") is not None

if REPORTLAB_AVAILABLE:
    from invoicebot.services.pdf import render_invoice_pdf


@unittest.skipUnless(REPORTLAB_AVAILABLE, "reportlab is not installed in this environment")
class InvoicePdfSmokeTests(unittest.TestCase):
    def test_render_invoice_pdf_smoke_includes_key_invoice_text(self) -> None:
        profile = Profile(
            company_name="Tradies NZ",
            address="1 Test Street, Auckland",
            gst_number="123-456-789",
            email="hello@example.com",
            phone="+64 21 123 4567",
            bank_details="Bank: Your Bank, Account Name: Your Business, Account: 00-0000-0000000-00",
        )
        client = Client(
            id="client-1",
            name="Sophie Taylor",
            company="Taylor Services",
            email="sophie@example.com",
            phone="+64 21 555 0000",
            address="2 Client Road, Wellington",
        )
        draft = InvoiceDraft(
            user_id="user-1",
            items=[
                InvoiceItem(description="Garden tidy", quantity=2, unit_price_cents=9500),
                InvoiceItem(description="Materials", quantity=1, unit_price_cents=4500),
            ],
            client_id=client.id,
            created_at=datetime(2026, 3, 29, 10, 0, tzinfo=UTC),
        )

        pdf_bytes = render_invoice_pdf(profile, draft, client)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertIn(b"Payment details", pdf_bytes)
        self.assertIn(b"Invoice Summary", pdf_bytes)


if __name__ == "__main__":
    unittest.main()
