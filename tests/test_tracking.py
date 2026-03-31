import unittest

from invoicebot.models import Profile
from invoicebot.services.storage import InMemoryRepository
from invoicebot.services.tracking import build_tracked_item, round_tracked_hours


class TrackingTests(unittest.TestCase):
    def test_round_tracked_hours_uses_tenth_hours(self) -> None:
        self.assertEqual(round_tracked_hours(29 * 60), 0.5)
        self.assertEqual(round_tracked_hours(61 * 60), 1.0)

    def test_round_tracked_hours_has_minimum_tenth(self) -> None:
        self.assertEqual(round_tracked_hours(60), 0.1)

    def test_build_tracked_item_uses_profile_rate(self) -> None:
        item = build_tracked_item(elapsed_seconds=90 * 60, hourly_rate_cents=9500)

        self.assertEqual(item.description, "Tracked labour")
        self.assertEqual(item.quantity, 1.5)
        self.assertEqual(item.unit_price_cents, 9500)
        self.assertEqual(item.line_total_cents, 14250)

    def test_repository_stores_default_hourly_rate(self) -> None:
        repo = InMemoryRepository()
        profile = Profile(default_hourly_rate_cents=9500)

        repo.save_profile("user-1", profile)

        self.assertEqual(repo.get_or_create_profile("user-1").default_hourly_rate_cents, 9500)

    def test_repository_start_and_stop_tracking_session(self) -> None:
        repo = InMemoryRepository()

        session = repo.start_tracking("user-1", "draft-1")

        self.assertEqual(repo.get_active_tracking("user-1").draft_id, "draft-1")
        stopped = repo.stop_tracking("user-1")
        self.assertIsNotNone(stopped)
        assert stopped is not None
        self.assertEqual(stopped.draft_id, "draft-1")
        self.assertIsNone(repo.get_active_tracking("user-1"))


if __name__ == "__main__":
    unittest.main()
