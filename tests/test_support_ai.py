import unittest
from unittest.mock import patch
from types import SimpleNamespace

from invoicebot.services.support_ai import BugSupportRequest, _extract_output_text, generate_bug_triage_reply


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return _FakeResponse(self.payload)


class SupportAITests(unittest.IsolatedAsyncioTestCase):
    def test_extract_output_text_prefers_top_level_field(self) -> None:
        self.assertEqual(_extract_output_text({"output_text": "Hello"}), "Hello")

    def test_extract_output_text_falls_back_to_output_content(self) -> None:
        payload = {
            "output": [
                {
                    "content": [
                        {"text": "Step 1"},
                        {"text": "Step 2"},
                    ]
                }
            ]
        }
        self.assertEqual(_extract_output_text(payload), "Step 1\nStep 2")

    async def test_returns_none_for_no_match(self) -> None:
        with patch(
            "invoicebot.services.support_ai.httpx",
            new=SimpleNamespace(AsyncClient=lambda **kwargs: _FakeClient({"output_text": "NO_MATCH"})),
        ):
            result = await generate_bug_triage_reply(
                api_key="test",
                model="gpt-4.1-mini",
                vector_store_id="vs_test",
                request=BugSupportRequest(subject="Bug", body="It failed"),
            )
        self.assertIsNone(result)

    async def test_returns_answer_for_grounded_reply(self) -> None:
        with patch(
            "invoicebot.services.support_ai.httpx",
            new=SimpleNamespace(
                AsyncClient=lambda **kwargs: _FakeClient(
                    {"output_text": "Try /profile again.\n\nA human can still review this ticket if you need more help."}
                )
            ),
        ):
            result = await generate_bug_triage_reply(
                api_key="test",
                model="gpt-4.1-mini",
                vector_store_id="vs_test",
                request=BugSupportRequest(subject="Bug", body="It failed"),
            )
        self.assertIn("A human can still review this ticket", result or "")


if __name__ == "__main__":
    unittest.main()
