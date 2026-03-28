from __future__ import annotations

import base64

import httpx


async def send_invoice_email(
    *,
    resend_api_key: str,
    email_from: str,
    to_email: str,
    subject: str,
    body_text: str,
    pdf_bytes: bytes,
    filename: str,
    reply_to: str | None = None,
) -> None:
    if not resend_api_key:
        raise ValueError("RESEND_API_KEY is not configured")
    if not email_from:
        raise ValueError("EMAIL_FROM is not configured")

    payload: dict[str, object] = {
        "from": email_from,
        "to": [to_email],
        "subject": subject,
        "text": body_text,
        "attachments": [
            {
                "filename": filename,
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
            }
        ],
    }
    if reply_to:
        payload["reply_to"] = [reply_to]

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
