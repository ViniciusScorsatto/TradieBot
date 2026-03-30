import unittest

from invoicebot.models import InvoiceDraft, InvoiceItem, Profile
from invoicebot.services.storage import InMemoryRepository


class QuoteRepositoryTests(unittest.TestCase):
    def test_quote_finalize_does_not_increment_invoice_count(self) -> None:
        repo = InMemoryRepository()
        repo.save_profile("user-1", Profile())
        draft = InvoiceDraft(
            user_id="user-1",
            document_type="QUOTE",
            items=[InvoiceItem(description="Garden tidy", quantity=1, unit_price_cents=5000)],
        )
        repo.save_draft(draft)

        repo.finalize_draft("user-1")

        self.assertEqual(repo.invoice_count_this_month("user-1"), 0)
        self.assertEqual(len(repo.list_quotes("user-1")), 1)
        self.assertEqual(repo.get_or_create_profile("user-1").next_quote_number, 2)

    def test_convert_quote_creates_invoice_draft(self) -> None:
        repo = InMemoryRepository()
        profile = Profile()
        repo.save_profile("user-1", profile)
        draft = InvoiceDraft(
            user_id="user-1",
            document_type="QUOTE",
            client_id="client-1",
            notes="Quote notes",
            items=[InvoiceItem(description="Materials", quantity=2, unit_price_cents=4500)],
        )
        repo.save_draft(draft)
        repo.finalize_draft("user-1")

        converted = repo.convert_quote_to_invoice_draft("user-1", "QUO-0001")

        self.assertIsNotNone(converted)
        assert converted is not None
        self.assertEqual(converted.document_type, "INVOICE")
        self.assertEqual(converted.client_id, "client-1")
        self.assertEqual(converted.notes, "Quote notes")
        self.assertEqual(len(converted.items), 1)
        self.assertEqual(converted.items[0].description, "Materials")


if __name__ == "__main__":
    unittest.main()
