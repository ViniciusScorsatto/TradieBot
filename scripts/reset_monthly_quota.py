"""Railway cron entrypoint for monthly quota resets and daily retention cleanup."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def _retention_days(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer number of days") from exc
    return max(value, 0)


def should_run_monthly_reset(now_utc: datetime) -> bool:
    return now_utc.astimezone(ZoneInfo("Pacific/Auckland")).day == 1


def run_retention_cleanup(conn: psycopg.Connection) -> dict[str, int]:
    draft_retention_days = _retention_days("DRAFT_RETENTION_DAYS", 30)
    closed_ticket_retention_days = _retention_days("CLOSED_TICKET_RETENTION_DAYS", 365)
    promotion_delivery_retention_days = _retention_days("PROMOTION_DELIVERY_RETENTION_DAYS", 90)

    deleted: dict[str, int] = {}

    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM invoice_drafts
            WHERE status = 'ACTIVE'
              AND updated_at < NOW() - (%s || ' days')::interval
            """,
            (draft_retention_days,),
        )
        deleted["invoice_drafts"] = cur.rowcount

        cur.execute(
            """
            DELETE FROM tickets
            WHERE status = 'CLOSED'
              AND updated_at < NOW() - (%s || ' days')::interval
            """,
            (closed_ticket_retention_days,),
        )
        deleted["closed_tickets"] = cur.rowcount

        cur.execute(
            """
            DELETE FROM promotion_deliveries
            WHERE created_at < NOW() - (%s || ' days')::interval
            """,
            (promotion_delivery_retention_days,),
        )
        deleted["promotion_deliveries"] = cur.rowcount

    return deleted


def main() -> None:
    import psycopg

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
        if should_run_monthly_reset(now_utc):
            cur.execute(
                """
                UPDATE users
                SET invoice_count_this_month = 0,
                    voice_seconds_this_month = 0,
                    updated_at = NOW()
                WHERE invoice_count_this_month <> 0
                   OR voice_seconds_this_month <> 0
                """
            )
            updated = cur.rowcount
            print(f"Reset monthly quota counters for {updated} user(s).")
        else:
            print("Not the first day of the month in Pacific/Auckland. Skipping quota reset.")

        deleted = run_retention_cleanup(conn)
        conn.commit()

    print(
        "Retention cleanup finished: "
        + ", ".join(f"{table}={count}" for table, count in deleted.items())
    )


if __name__ == "__main__":
    main()
