from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import DefaultDict
from uuid import uuid4

from invoicebot.models import Client, InvoiceDraft, Profile, SupportTicket


class InMemoryRepository:
    """A lightweight repository so the project runs before DB wiring is complete."""

    def __init__(self) -> None:
        self.profiles: dict[str, Profile] = {}
        self.drafts: dict[str, InvoiceDraft] = {}
        self.clients: DefaultDict[str, list[Client]] = defaultdict(list)
        self.history: DefaultDict[str, list[InvoiceDraft]] = defaultdict(list)
        self.invoice_counts: DefaultDict[str, int] = defaultdict(int)
        self.credits: DefaultDict[str, int] = defaultdict(int)
        self.tickets: DefaultDict[str, list[SupportTicket]] = defaultdict(list)

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
        return self.clients[user_id]

    def list_history(self, user_id: str) -> list[InvoiceDraft]:
        return self.history[user_id]

    def record_ticket(self, ticket: SupportTicket) -> None:
        self.tickets[ticket.user_id].append(ticket)

    def available_quota(self, user_id: str, free_limit: int) -> int:
        free_remaining = max(free_limit - self.invoice_counts[user_id], 0)
        return free_remaining + self.credits[user_id]

    def consume_paid_credit_if_needed(self, user_id: str, free_limit: int) -> None:
        if self.invoice_counts[user_id] >= free_limit and self.credits[user_id] > 0:
            self.credits[user_id] -= 1

