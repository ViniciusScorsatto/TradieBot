import unittest

from invoicebot.services.storage import InMemoryRepository


class PromotionsConsentTests(unittest.TestCase):
    def test_consent_starts_disabled(self) -> None:
        repo = InMemoryRepository()

        state = repo.promotion_consent_state("user-1")

        self.assertEqual(state, {"consented": False, "opted_out": False})

    def test_grant_consent_enables_promotions_without_opt_out(self) -> None:
        repo = InMemoryRepository()

        repo.grant_promotion_consent("user-1", source="telegram_bot")

        self.assertEqual(
            repo.promotion_consent_state("user-1"),
            {"consented": True, "opted_out": False},
        )

    def test_revoke_consent_marks_opt_out_and_clears_preferences(self) -> None:
        repo = InMemoryRepository()
        repo.grant_promotion_consent("user-1", source="telegram_bot")
        repo.save_promotion_preferences("user-1", ["fuel", "software"])

        repo.revoke_promotion_consent("user-1")

        self.assertEqual(
            repo.promotion_consent_state("user-1"),
            {"consented": False, "opted_out": True},
        )
        self.assertEqual(repo.list_promotion_preferences("user-1"), [])


if __name__ == "__main__":
    unittest.main()
