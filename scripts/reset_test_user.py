"""Reset or set usage counters for a single test user."""

from __future__ import annotations

import argparse
import os

import psycopg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset or set invoice/voice usage and paid credits for one Telegram user."
    )
    parser.add_argument(
        "--telegram-user-id",
        required=True,
        help="Telegram user ID stored in users.telegram_user_id",
    )
    parser.add_argument(
        "--invoice-count",
        type=int,
        default=0,
        help="Value to set for invoice_count_this_month (default: 0)",
    )
    parser.add_argument(
        "--voice-count",
        type=int,
        default=0,
        help="Value to set for voice_transcriptions_this_month (default: 0)",
    )
    parser.add_argument(
        "--paid-invoice-credits",
        type=int,
        default=0,
        help="Value to set for paid_invoice_credits (default: 0)",
    )
    parser.add_argument(
        "--paid-voice-credits",
        type=int,
        default=0,
        help="Value to set for paid_voice_credits (default: 0)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET invoice_count_this_month = %s,
                voice_transcriptions_this_month = %s,
                paid_invoice_credits = %s,
                paid_voice_credits = %s,
                updated_at = NOW()
            WHERE telegram_user_id = %s
            RETURNING telegram_user_id, invoice_count_this_month, voice_transcriptions_this_month,
                      paid_invoice_credits, paid_voice_credits
            """,
            (
                args.invoice_count,
                args.voice_count,
                args.paid_invoice_credits,
                args.paid_voice_credits,
                args.telegram_user_id,
            ),
        )
        row = cur.fetchone()
        conn.commit()

    if not row:
        raise RuntimeError(f"No user found for telegram_user_id={args.telegram_user_id}")

    print("Updated test user:")
    print(f"  telegram_user_id: {row[0]}")
    print(f"  invoice_count_this_month: {row[1]}")
    print(f"  voice_transcriptions_this_month: {row[2]}")
    print(f"  paid_invoice_credits: {row[3]}")
    print(f"  paid_voice_credits: {row[4]}")


if __name__ == "__main__":
    main()
