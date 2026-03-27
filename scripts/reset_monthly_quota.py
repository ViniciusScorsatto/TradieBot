"""Railway cron entrypoint for resetting monthly invoice counters."""

from __future__ import annotations

import os
from datetime import datetime, timezone


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    now = datetime.now(timezone.utc).isoformat()
    print(f"[{now}] Reset monthly quota job placeholder running against {database_url!r}")
    print("Implement DB update with your preferred adapter before production deploy.")


if __name__ == "__main__":
    main()
