from __future__ import annotations

from dataclasses import dataclass

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover - local test fallback
    httpx = None


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"

SYSTEM_PROMPT = """You are InvoiceBot's bug triage assistant.

You help with product bug tickets only. Use only the retrieved support knowledge.

Rules:
- Answer only from the provided knowledge base.
- Do not invent product behavior, fixes, policies, or settings.
- Do not answer billing, refund, legal, privacy, tax, or account-access issues.
- If the knowledge does not clearly support a helpful answer, respond with exactly: NO_MATCH
- Keep answers concise and actionable.
- End helpful answers with: "A human can still review this ticket if you need more help."
"""


@dataclass(slots=True)
class BugSupportRequest:
    subject: str
    body: str
    business_name: str = ""


def _extract_output_text(payload: dict) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text_value = content.get("text")
            if isinstance(text_value, str) and text_value.strip():
                parts.append(text_value.strip())
    return "\n".join(parts).strip()


async def generate_bug_triage_reply(
    *,
    api_key: str,
    model: str,
    vector_store_id: str,
    request: BugSupportRequest,
) -> str | None:
    if not api_key or not vector_store_id:
        return None

    user_prompt = (
        "Review this bug ticket and provide a short first troubleshooting reply if the knowledge base clearly supports it.\n\n"
        f"Business: {request.business_name or 'Unknown business'}\n"
        f"Subject: {request.subject}\n"
        f"Details: {request.body}"
    )

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
        "tools": [{"type": "file_search", "vector_store_ids": [vector_store_id]}],
        "max_output_tokens": 280,
    }

    if httpx is None:
        raise RuntimeError("httpx is required for AI support responses")

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            OPENAI_RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        text = _extract_output_text(response.json())

    if not text:
        return None
    normalized = text.strip()
    if normalized == "NO_MATCH" or normalized.startswith("NO_MATCH"):
        return None
    return normalized
