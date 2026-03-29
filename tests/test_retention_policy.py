import unittest
from datetime import datetime, timezone

from scripts.reset_monthly_quota import should_run_monthly_reset


class RetentionPolicyTests(unittest.TestCase):
    def test_monthly_reset_runs_on_first_day_in_auckland(self) -> None:
        self.assertTrue(should_run_monthly_reset(datetime(2026, 4, 1, 0, 5, tzinfo=timezone.utc)))

    def test_monthly_reset_skips_non_first_day_in_auckland(self) -> None:
        self.assertFalse(should_run_monthly_reset(datetime(2026, 4, 2, 0, 5, tzinfo=timezone.utc)))


if __name__ == "__main__":
    unittest.main()
