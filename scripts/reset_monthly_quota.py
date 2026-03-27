"""Railway cron entrypoint for resetting monthly invoice counters."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import psycopg


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    now_utc = datetime.now(timezone.utc)
    auckland = now_utc.astimezone(ZoneInfo("Pacific/Auckland"))

    print(f"[{now_utc.isoformat()}] Quota reset job invoked. Auckland time is {auckland.isoformat()}.")

    if auckland.day != 1:
        print("Not the first day of the month in Pacific/Auckland. Skipping quota reset.")
        return

    if not database_url:
        raise RuntimeError("DATABASE_URL is required for the quota reset job")

    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET invoice_count_this_month = 0, updated_at = NOW()
            WHERE invoice_count_this_month <> 0
            """
        )
        updated = cur.rowcount
        conn.commit()
    print(f"Reset monthly quota counters for {updated} user(s).")


if __name__ == "__main__":
    main()
