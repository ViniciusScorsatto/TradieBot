from __future__ import annotations

import base64
from email.utils import parseaddr

import httpx


async def send_invoice_email(
    *,
    mailjet_api_key: str,
    mailjet_secret_key: str,
    email_from: str,
    to_email: str,
    subject: str,
    body_text: str,
    pdf_bytes: bytes,
    filename: str,
    reply_to: str | None = None,
) -> None:
    if not mailjet_api_key:
        raise ValueError("MAILJET_API_KEY is not configured")
    if not mailjet_secret_key:
        raise ValueError("MAILJET_SECRET_KEY is not configured")
    if not email_from:
        raise ValueError("EMAIL_FROM is not configured")

    from_name, from_email = parseaddr(email_from)
    if not from_email:
        raise ValueError("EMAIL_FROM must include a valid email address")

    payload: dict[str, object] = {
        "Messages": [
            {
                "From": {
                    "Email": from_email,
                    "Name": from_name or from_email,
                },
                "To": [{"Email": to_email}],
                "Subject": subject,
                "TextPart": body_text,
                "Attachments": [
                    {
                        "ContentType": "application/pdf",
                        "Filename": filename,
                        "Base64Content": base64.b64encode(pdf_bytes).decode("ascii"),
                    }
                ],
            }
        ]
    }
    if reply_to:
        _, reply_to_email = parseaddr(reply_to)
        if reply_to_email:
            payload["Messages"][0]["ReplyTo"] = {"Email": reply_to_email}

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            "https://api.mailjet.com/v3.1/send",
            auth=(mailjet_api_key, mailjet_secret_key),
            headers={"Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
