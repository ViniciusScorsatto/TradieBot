"""Railway cron entrypoint for resetting monthly invoice counters."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    now_utc = datetime.now(timezone.utc)
    auckland = now_utc.astimezone(ZoneInfo("Pacific/Auckland"))

    print(f"[{now_utc.isoformat()}] Quota reset job invoked. Auckland time is {auckland.isoformat()}.")

    if auckland.day != 1:
        print("Not the first day of the month in Pacific/Auckland. Skipping quota reset.")
        return

    print(f"Would reset monthly quota counters against {database_url!r}.")
    print("Replace this placeholder with a real database update before production launch.")


if __name__ == "__main__":
    main()
