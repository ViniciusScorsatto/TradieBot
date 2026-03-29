from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, DefaultDict, Protocol
from uuid import uuid4

from invoicebot.models import Client, InvoiceDraft, InvoiceItem, Profile, SupportTicket
from invoicebot.services.tax import gst_cents, subtotal_cents, total_cents


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Repository(Protocol):
    def get_or_create_profile(self, user_id: str) -> Profile: ...
    def save_profile(self, user_id: str, profile: Profile) -> Profile: ...
    def create_draft(self, user_id: str) -> InvoiceDraft: ...
    def get_draft(self, user_id: str) -> InvoiceDraft | None: ...
    def save_draft(self, draft: InvoiceDraft) -> InvoiceDraft: ...
    def finalize_draft(self, user_id: str) -> InvoiceDraft | None: ...
    def add_client(self, user_id: str, name: str, company: str = "", email: str = "", phone: str = "", address: str = "") -> Client: ...
    def list_clients(self, user_id: str) -> list[Client]: ...
    def get_client(self, user_id: str, client_id: str) -> Client | None: ...
    def update_client(self, user_id: str, client: Client) -> Client | None: ...
    def delete_client(self, user_id: str, client_id: str) -> bool: ...
    def list_history(self, user_id: str) -> list[InvoiceDraft]: ...
    def record_ticket(self, ticket: SupportTicket) -> None: ...
    def list_promotion_preferences(self, user_id: str) -> list[str]: ...
    def save_promotion_preferences(self, user_id: str, categories: list[str]) -> None: ...
    def invoice_count_this_month(self, user_id: str) -> int: ...
    def paid_credits(self, user_id: str) -> int: ...
    def paid_voice_seconds(self, user_id: str) -> int: ...
    def voice_seconds_this_month(self, user_id: str) -> int: ...
    def increment_voice_usage(self, user_id: str, seconds: int) -> None: ...
    def consume_paid_credit_if_needed(self, user_id: str, free_limit: int) -> None: ...
    def consume_paid_voice_credit_if_needed(self, user_id: str, free_limit_seconds: int, seconds_used: int) -> None: ...
    def stripe_customer_id(self, user_id: str) -> str | None: ...
    def save_stripe_customer_id(self, user_id: str, customer_id: str) -> None: ...


class InMemoryRepository:
    """Fallback repository for local development when DATABASE_URL is not set."""

    def __init__(self) -> None:
        self.profiles: dict[str, Profile] = {}
        self.drafts: dict[str, InvoiceDraft] = {}
        self.clients: DefaultDict[str, list[Client]] = defaultdict(list)
        self.history: DefaultDict[str, list[InvoiceDraft]] = defaultdict(list)
        self.invoice_counts: DefaultDict[str, int] = defaultdict(int)
        self.credits: DefaultDict[str, int] = defaultdict(int)
        self.voice_seconds_credits: DefaultDict[str, int] = defaultdict(int)
        self.voice_usage_seconds: DefaultDict[str, int] = defaultdict(int)
        self.stripe_customers: dict[str, str] = {}
        self.tickets: DefaultDict[str, list[SupportTicket]] = defaultdict(list)
        self.promotion_preferences: DefaultDict[str, set[str]] = defaultdict(set)

    def get_or_create_profile(self, user_id: str) -> Profile:
        profile = self.profiles.get(user_id)
        if not profile:
            profile = Profile()
            self.profiles[user_id] = profile
        return profile

    def save_profile(self, user_id: str, profile: Profile) -> Profile:
        self.profiles[user_id] = profile
        return profile

    def create_draft(self, user_id: str) -> InvoiceDraft:
        draft = InvoiceDraft(user_id=user_id)
        self.drafts[user_id] = draft
        return draft

    def get_draft(self, user_id: str) -> InvoiceDraft | None:
        return self.drafts.get(user_id)

    def save_draft(self, draft: InvoiceDraft) -> InvoiceDraft:
        self.drafts[draft.user_id] = draft
        return draft

    def finalize_draft(self, user_id: str) -> InvoiceDraft | None:
        draft = self.drafts.pop(user_id, None)
        if draft:
            self.history[user_id].insert(0, replace(draft))
            self.invoice_counts[user_id] += 1
        return draft

    def add_client(self, user_id: str, name: str, company: str = "", email: str = "", phone: str = "", address: str = "") -> Client:
        client = Client(id=str(uuid4()), name=name, company=company, email=email, phone=phone, address=address)
        self.clients[user_id].append(client)
        return client

    def list_clients(self, user_id: str) -> list[Client]:
        return sorted(
            self.clients[user_id],
            key=lambda client: (
                (client.company or "").strip().lower(),
                client.name.strip().lower(),
            ),
        )

    def get_client(self, user_id: str, client_id: str) -> Client | None:
        for client in self.clients[user_id]:
            if client.id == client_id:
                return client
        return None

    def update_client(self, user_id: str, client: Client) -> Client | None:
        for index, existing in enumerate(self.clients[user_id]):
            if existing.id == client.id:
                self.clients[user_id][index] = client
                return client
        return None

    def delete_client(self, user_id: str, client_id: str) -> bool:
        before = len(self.clients[user_id])
        self.clients[user_id] = [client for client in self.clients[user_id] if client.id != client_id]
        return len(self.clients[user_id]) != before

    def list_history(self, user_id: str) -> list[InvoiceDraft]:
        return self.history[user_id]

    def record_ticket(self, ticket: SupportTicket) -> None:
        self.tickets[ticket.user_id].append(ticket)

    def list_promotion_preferences(self, user_id: str) -> list[str]:
        return sorted(self.promotion_preferences[user_id])

    def save_promotion_preferences(self, user_id: str, categories: list[str]) -> None:
        self.promotion_preferences[user_id] = set(categories)

    def invoice_count_this_month(self, user_id: str) -> int:
        return self.invoice_counts[user_id]

    def paid_credits(self, user_id: str) -> int:
        return self.credits[user_id]

    def paid_voice_seconds(self, user_id: str) -> int:
        return self.voice_seconds_credits[user_id]

    def voice_seconds_this_month(self, user_id: str) -> int:
        return self.voice_usage_seconds[user_id]

    def increment_voice_usage(self, user_id: str, seconds: int) -> None:
        self.voice_usage_seconds[user_id] += max(seconds, 0)

    def consume_paid_credit_if_needed(self, user_id: str, free_limit: int) -> None:
        if self.invoice_counts[user_id] > free_limit and self.credits[user_id] > 0:
            self.credits[user_id] -= 1

    def consume_paid_voice_credit_if_needed(self, user_id: str, free_limit_seconds: int, seconds_used: int) -> None:
        total_used = self.voice_usage_seconds[user_id]
        newly_chargeable = max(total_used - free_limit_seconds, 0) - max(total_used - max(seconds_used, 0) - free_limit_seconds, 0)
        if newly_chargeable > 0 and self.voice_seconds_credits[user_id] > 0:
            self.voice_seconds_credits[user_id] = max(self.voice_seconds_credits[user_id] - newly_chargeable, 0)

    def stripe_customer_id(self, user_id: str) -> str | None:
        return self.stripe_customers.get(user_id)

    def save_stripe_customer_id(self, user_id: str, customer_id: str) -> None:
        self.stripe_customers[user_id] = customer_id


class PostgresRepository:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL", "")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required for PostgresRepository")
        self.ensure_schema()

    def _connect(self) -> Any:
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(self.database_url, row_factory=dict_row)

    def ensure_schema(self) -> None:
        required_columns = {
            "users": {"id", "telegram_user_id", "invoice_count_this_month", "voice_seconds_this_month", "paid_invoice_credits", "paid_voice_seconds"},
            "profiles": {"id", "user_id", "address", "default_template_id", "next_invoice_number"},
            "clients": {"id", "user_id", "name", "address"},
            "invoice_drafts": {"id", "user_id", "client_id", "status", "subtotal_cents", "gst_cents", "total_cents"},
            "invoice_draft_items": {"id", "draft_id", "description", "quantity", "unit_price", "discount_cents", "discount_percent", "line_total"},
            "invoices": {"id", "user_id", "client_id", "profile_snapshot", "invoice_number", "template_id", "subtotal_cents", "gst_cents", "total_cents"},
            "invoice_items": {"id", "invoice_id", "description", "quantity", "unit_price", "discount_cents", "discount_percent", "line_total"},
            "tickets": {"id", "user_id", "type", "status", "subject"},
            "ticket_messages": {"id", "ticket_id", "sender", "body"},
            "payments": {"id", "user_id", "stripe_session_id", "stripe_payment_id", "purchase_type", "amount_cents", "credits_purchased", "status"},
            "promotion_preferences": {"id", "user_id", "category", "created_at"},
            "promotion_campaigns": {"id", "category", "title", "body", "affiliate_url", "status", "created_at"},
            "promotion_deliveries": {"id", "campaign_id", "user_id", "telegram_user_id", "status", "created_at"},
        }
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                """
            )
            rows = cur.fetchall()

        columns_by_table: dict[str, set[str]] = {}
        for row in rows:
            columns_by_table.setdefault(row["table_name"], set()).add(row["column_name"])

        missing_tables = sorted(table for table in required_columns if table not in columns_by_table)
        missing_columns = {
            table: sorted(expected - columns_by_table.get(table, set()))
            for table, expected in required_columns.items()
            if expected - columns_by_table.get(table, set())
        }

        if missing_tables or missing_columns:
            details: list[str] = []
            if missing_tables:
                details.append("missing tables: " + ", ".join(missing_tables))
            if missing_columns:
                details.append(
                    "missing columns: "
                    + "; ".join(f"{table}({', '.join(columns)})" for table, columns in missing_columns.items())
                )
            raise RuntimeError(
                "Database schema is not ready for InvoiceBot. "
                "Run Prisma migrations first with `npm run prisma:deploy` from the repo root. "
                + "Detected "
                + " | ".join(details)
            )

    def _ensure_user(self, user_id: str) -> dict:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE telegram_user_id = %s", (user_id,))
            user = cur.fetchone()
            if user:
                return user
            user_row = {
                "id": str(uuid4()),
                "telegram_user_id": user_id,
            }
            cur.execute(
                """
                INSERT INTO users (id, telegram_user_id)
                VALUES (%s, %s)
                RETURNING *
                """,
                (user_row["id"], user_row["telegram_user_id"]),
            )
            created = cur.fetchone()
            conn.commit()
            return created

    def _row_to_profile(self, row: dict | None) -> Profile:
        if not row:
            return Profile()
        return Profile(
            company_name=row.get("company_name") or "",
            address=row.get("address") or "",
            gst_number=row.get("gst_number") or "",
            email=row.get("email") or "",
            phone=row.get("phone") or "",
            bank_details=row.get("bank_details") or "",
            logo_url=row.get("logo_url") or "",
            default_template_id=row.get("default_template_id") or "classic-blue",
            invoice_prefix=row.get("invoice_prefix") or "INV",
            next_invoice_number=row.get("next_invoice_number") or 1,
        )

    def _row_to_client(self, row: dict) -> Client:
        return Client(
            id=row["id"],
            name=row["name"],
            company=row.get("company") or "",
            email=row.get("email") or "",
            phone=row.get("phone") or "",
            address=row.get("address") or "",
        )

    def _active_draft_row(self, cur: Any, user_db_id: str) -> dict | None:
        cur.execute(
            """
            SELECT * FROM invoice_drafts
            WHERE user_id = %s AND status = 'ACTIVE'
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_db_id,),
        )
        return cur.fetchone()

    def _load_draft_items(self, cur: Any, draft_id: str) -> list[InvoiceItem]:
        cur.execute(
            """
            SELECT description, quantity, unit_price, discount_cents, discount_percent
            FROM invoice_draft_items
            WHERE draft_id = %s
            ORDER BY created_at ASC
            """,
            (draft_id,),
        )
        return [
            InvoiceItem(
                description=row["description"],
                quantity=float(row["quantity"]),
                unit_price_cents=int(row["unit_price"]),
                discount_cents=int(row.get("discount_cents") or 0),
                discount_percent=float(row["discount_percent"]) if row.get("discount_percent") is not None else None,
            )
            for row in cur.fetchall()
        ]

    def get_or_create_profile(self, user_id: str) -> Profile:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM profiles WHERE user_id = %s", (user["id"],))
            profile = cur.fetchone()
            if profile:
                return self._row_to_profile(profile)

            cur.execute(
                """
                INSERT INTO profiles (id, user_id)
                VALUES (%s, %s)
                RETURNING *
                """,
                (str(uuid4()), user["id"]),
            )
            created = cur.fetchone()
            conn.commit()
            return self._row_to_profile(created)

    def save_profile(self, user_id: str, profile: Profile) -> Profile:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT id FROM profiles WHERE user_id = %s", (user["id"],))
            profile_row = cur.fetchone()
            if profile_row:
                cur.execute(
                    """
                    UPDATE profiles
                    SET company_name = %s,
                        address = %s,
                        gst_number = %s,
                        email = %s,
                        phone = %s,
                        bank_details = %s,
                        logo_url = %s,
                        default_template_id = %s,
                        invoice_prefix = %s,
                        next_invoice_number = %s,
                        updated_at = NOW()
                    WHERE user_id = %s
                    """,
                    (
                        profile.company_name,
                        profile.address,
                        profile.gst_number,
                        profile.email,
                        profile.phone,
                        profile.bank_details,
                        profile.logo_url,
                        profile.default_template_id,
                        profile.invoice_prefix,
                        profile.next_invoice_number,
                        user["id"],
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO profiles (
                        id, user_id, company_name, address, gst_number, email, phone,
                        bank_details, logo_url, default_template_id, invoice_prefix, next_invoice_number
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        user["id"],
                        profile.company_name,
                        profile.address,
                        profile.gst_number,
                        profile.email,
                        profile.phone,
                        profile.bank_details,
                        profile.logo_url,
                        profile.default_template_id,
                        profile.invoice_prefix,
                        profile.next_invoice_number,
                    ),
                )
            conn.commit()
        return profile

    def create_draft(self, user_id: str) -> InvoiceDraft:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            existing = self._active_draft_row(cur, user["id"])
            if existing:
                cur.execute("DELETE FROM invoice_draft_items WHERE draft_id = %s", (existing["id"],))
                cur.execute(
                    """
                    UPDATE invoice_drafts
                    SET client_id = NULL, notes = '', subtotal_cents = 0, gst_cents = 0, total_cents = 0, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (existing["id"],),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO invoice_drafts (id, user_id)
                    VALUES (%s, %s)
                    """,
                    (str(uuid4()), user["id"]),
                )
            conn.commit()
        return InvoiceDraft(user_id=user_id)

    def get_draft(self, user_id: str) -> InvoiceDraft | None:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            draft = self._active_draft_row(cur, user["id"])
            if not draft:
                return None
            items = self._load_draft_items(cur, draft["id"])
            return InvoiceDraft(
                user_id=user_id,
                items=items,
                client_id=draft.get("client_id"),
                notes=draft.get("notes") or "",
                created_at=draft.get("created_at") or _utcnow(),
            )

    def save_draft(self, draft: InvoiceDraft) -> InvoiceDraft:
        user = self._ensure_user(draft.user_id)
        profile = self.get_or_create_profile(draft.user_id)
        draft_subtotal = subtotal_cents(draft)
        draft_gst = gst_cents(draft, profile)
        draft_total = total_cents(draft, profile)
        with self._connect() as conn, conn.cursor() as cur:
            draft_row = self._active_draft_row(cur, user["id"])
            draft_id = draft_row["id"] if draft_row else str(uuid4())
            if draft_row:
                cur.execute(
                    """
                    UPDATE invoice_drafts
                    SET client_id = %s, notes = %s, subtotal_cents = %s, gst_cents = %s, total_cents = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        draft.client_id,
                        draft.notes,
                        draft_subtotal,
                        draft_gst,
                        draft_total,
                        draft_id,
                    ),
                )
                cur.execute("DELETE FROM invoice_draft_items WHERE draft_id = %s", (draft_id,))
            else:
                cur.execute(
                    """
                    INSERT INTO invoice_drafts (
                        id, user_id, client_id, notes, subtotal_cents, gst_cents, total_cents
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        draft_id,
                        user["id"],
                        draft.client_id,
                        draft.notes,
                        draft_subtotal,
                        draft_gst,
                        draft_total,
                    ),
                )
            for item in draft.items:
                cur.execute(
                    """
                    INSERT INTO invoice_draft_items (
                        id, draft_id, description, quantity, unit_price, discount_cents, discount_percent, line_total
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        draft_id,
                        item.description,
                        item.quantity,
                        item.unit_price_cents,
                        item.discount_cents,
                        item.discount_percent,
                        item.line_total_cents,
                    ),
                )
            conn.commit()
        return draft

    def finalize_draft(self, user_id: str) -> InvoiceDraft | None:
        user = self._ensure_user(user_id)
        profile = self.get_or_create_profile(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            draft_row = self._active_draft_row(cur, user["id"])
            if not draft_row:
                return None
            items = self._load_draft_items(cur, draft_row["id"])
            draft = InvoiceDraft(
                user_id=user_id,
                items=items,
                client_id=draft_row.get("client_id"),
                notes=draft_row.get("notes") or "",
                created_at=draft_row.get("created_at") or _utcnow(),
            )
            invoice_id = str(uuid4())
            invoice_number = f"{profile.invoice_prefix}-{profile.next_invoice_number:04d}"
            draft_subtotal = subtotal_cents(draft)
            draft_gst = gst_cents(draft, profile)
            draft_total = total_cents(draft, profile)
            cur.execute(
                """
                INSERT INTO invoices (
                    id, user_id, client_id, profile_snapshot, invoice_number, template_id,
                    subtotal_cents, gst_cents, total_cents, notes
                )
                VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
                """,
                (
                    invoice_id,
                    user["id"],
                    draft.client_id,
                    json.dumps(
                        {
                            "company_name": profile.company_name,
                            "address": profile.address,
                            "gst_number": profile.gst_number,
                            "email": profile.email,
                            "phone": profile.phone,
                            "bank_details": profile.bank_details,
                            "default_template_id": profile.default_template_id,
                        }
                    ),
                    invoice_number,
                    profile.default_template_id,
                    draft_subtotal,
                    draft_gst,
                    draft_total,
                    draft.notes,
                ),
            )
            for item in items:
                cur.execute(
                    """
                    INSERT INTO invoice_items (
                        id, invoice_id, description, quantity, unit_price, discount_cents, discount_percent, line_total
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        invoice_id,
                        item.description,
                        item.quantity,
                        item.unit_price_cents,
                        item.discount_cents,
                        item.discount_percent,
                        item.line_total_cents,
                    ),
                )
            cur.execute("UPDATE invoice_drafts SET status = 'GENERATED', updated_at = NOW() WHERE id = %s", (draft_row["id"],))
            cur.execute("UPDATE users SET invoice_count_this_month = invoice_count_this_month + 1, updated_at = NOW() WHERE id = %s", (user["id"],))
            cur.execute(
                """
                UPDATE profiles
                SET next_invoice_number = next_invoice_number + 1, updated_at = NOW()
                WHERE user_id = %s
                """,
                (user["id"],),
            )
            conn.commit()
            return draft

    def add_client(self, user_id: str, name: str, company: str = "", email: str = "", phone: str = "", address: str = "") -> Client:
        user = self._ensure_user(user_id)
        client = Client(id=str(uuid4()), name=name, company=company, email=email, phone=phone, address=address)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO clients (id, user_id, name, company, email, phone, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (client.id, user["id"], client.name, client.company, client.email, client.phone, client.address),
            )
            conn.commit()
        return client

    def list_clients(self, user_id: str) -> list[Client]:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, company, email, phone, address
                FROM clients
                WHERE user_id = %s
                ORDER BY LOWER(COALESCE(company, '')), LOWER(name), created_at DESC
                """,
                (user["id"],),
            )
            return [self._row_to_client(row) for row in cur.fetchall()]

    def get_client(self, user_id: str, client_id: str) -> Client | None:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, company, email, phone, address
                FROM clients
                WHERE user_id = %s AND id = %s
                LIMIT 1
                """,
                (user["id"], client_id),
            )
            row = cur.fetchone()
            return self._row_to_client(row) if row else None

    def update_client(self, user_id: str, client: Client) -> Client | None:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE clients
                SET name = %s,
                    company = %s,
                    email = %s,
                    phone = %s,
                    address = %s,
                    updated_at = NOW()
                WHERE user_id = %s AND id = %s
                RETURNING id, name, company, email, phone, address
                """,
                (client.name, client.company, client.email, client.phone, client.address, user["id"], client.id),
            )
            row = cur.fetchone()
            conn.commit()
            return self._row_to_client(row) if row else None

    def delete_client(self, user_id: str, client_id: str) -> bool:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM clients
                WHERE user_id = %s AND id = %s
                """,
                (user["id"], client_id),
            )
            deleted = cur.rowcount > 0
            conn.commit()
            return deleted

    def list_history(self, user_id: str) -> list[InvoiceDraft]:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, client_id, notes, created_at
                FROM invoices
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (user["id"],),
            )
            invoices = cur.fetchall()
            history: list[InvoiceDraft] = []
            for invoice in invoices:
                cur.execute(
                    """
                    SELECT description, quantity, unit_price, discount_cents, discount_percent
                    FROM invoice_items
                    WHERE invoice_id = %s
                    ORDER BY id ASC
                    """,
                    (invoice["id"],),
                )
                items = [
                    InvoiceItem(
                        description=row["description"],
                        quantity=float(row["quantity"]),
                        unit_price_cents=int(row["unit_price"]),
                        discount_cents=int(row.get("discount_cents") or 0),
                        discount_percent=float(row["discount_percent"]) if row.get("discount_percent") is not None else None,
                    )
                    for row in cur.fetchall()
                ]
                history.append(
                    InvoiceDraft(
                        user_id=user_id,
                        items=items,
                        client_id=invoice.get("client_id"),
                        notes=invoice.get("notes") or "",
                        created_at=invoice.get("created_at") or _utcnow(),
                    )
                )
            return history

    def record_ticket(self, ticket: SupportTicket) -> None:
        user = self._ensure_user(ticket.user_id)
        ticket_id = str(uuid4())
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tickets (id, user_id, type, subject)
                VALUES (%s, %s, %s, %s)
                """,
                (ticket_id, user["id"], ticket.kind, ticket.subject),
            )
            cur.execute(
                """
                INSERT INTO ticket_messages (id, ticket_id, sender, body)
                VALUES (%s, %s, %s, %s)
                """,
                (str(uuid4()), ticket_id, "telegram_user", ticket.body),
            )
            conn.commit()

    def list_promotion_preferences(self, user_id: str) -> list[str]:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT category
                FROM promotion_preferences
                WHERE user_id = %s
                ORDER BY category ASC
                """,
                (user["id"],),
            )
            return [row["category"] for row in cur.fetchall()]

    def save_promotion_preferences(self, user_id: str, categories: list[str]) -> None:
        user = self._ensure_user(user_id)
        unique_categories = sorted({category for category in categories if category})
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM promotion_preferences WHERE user_id = %s", (user["id"],))
            for category in unique_categories:
                cur.execute(
                    """
                    INSERT INTO promotion_preferences (id, user_id, category)
                    VALUES (%s, %s, %s)
                    """,
                    (str(uuid4()), user["id"], category),
                )
            conn.commit()

    def invoice_count_this_month(self, user_id: str) -> int:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT invoice_count_this_month FROM users WHERE id = %s", (user["id"],))
            row = cur.fetchone()
            return int(row["invoice_count_this_month"]) if row else 0

    def paid_credits(self, user_id: str) -> int:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT paid_invoice_credits FROM users WHERE id = %s", (user["id"],))
            row = cur.fetchone()
            return int(row["paid_invoice_credits"]) if row else 0

    def paid_voice_seconds(self, user_id: str) -> int:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT paid_voice_seconds FROM users WHERE id = %s", (user["id"],))
            row = cur.fetchone()
            return int(row["paid_voice_seconds"]) if row else 0

    def voice_seconds_this_month(self, user_id: str) -> int:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT voice_seconds_this_month FROM users WHERE id = %s", (user["id"],))
            row = cur.fetchone()
            return int(row["voice_seconds_this_month"]) if row else 0

    def increment_voice_usage(self, user_id: str, seconds: int) -> None:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET voice_seconds_this_month = voice_seconds_this_month + %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (max(seconds, 0), user["id"]),
            )
            conn.commit()

    def consume_paid_credit_if_needed(self, user_id: str, free_limit: int) -> None:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT invoice_count_this_month, paid_invoice_credits FROM users WHERE id = %s",
                (user["id"],),
            )
            row = cur.fetchone()
            if row and int(row["invoice_count_this_month"]) > free_limit and int(row["paid_invoice_credits"]) > 0:
                cur.execute(
                    """
                    UPDATE users
                    SET paid_invoice_credits = paid_invoice_credits - 1, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (user["id"],),
                )
                conn.commit()

    def consume_paid_voice_credit_if_needed(self, user_id: str, free_limit_seconds: int, seconds_used: int) -> None:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT voice_seconds_this_month, paid_voice_seconds FROM users WHERE id = %s",
                (user["id"],),
            )
            row = cur.fetchone()
            if row:
                total_used = int(row["voice_seconds_this_month"])
                available_paid = int(row["paid_voice_seconds"])
                newly_chargeable = max(total_used - free_limit_seconds, 0) - max(
                    total_used - max(seconds_used, 0) - free_limit_seconds, 0
                )
            else:
                newly_chargeable = 0
                available_paid = 0
            if newly_chargeable > 0 and available_paid > 0:
                cur.execute(
                    """
                    UPDATE users
                    SET paid_voice_seconds = GREATEST(paid_voice_seconds - %s, 0), updated_at = NOW()
                    WHERE id = %s
                    """,
                    (newly_chargeable, user["id"]),
                )
                conn.commit()

    def stripe_customer_id(self, user_id: str) -> str | None:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT stripe_customer_id FROM users WHERE id = %s", (user["id"],))
            row = cur.fetchone()
            return str(row["stripe_customer_id"]) if row and row.get("stripe_customer_id") else None

    def save_stripe_customer_id(self, user_id: str, customer_id: str) -> None:
        user = self._ensure_user(user_id)
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET stripe_customer_id = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (customer_id, user["id"]),
            )
            conn.commit()

    def reset_monthly_quota(self) -> int:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET invoice_count_this_month = 0,
                    voice_seconds_this_month = 0,
                    updated_at = NOW()
                WHERE invoice_count_this_month <> 0 OR voice_seconds_this_month <> 0
                """
            )
            updated = cur.rowcount
            conn.commit()
            return updated
