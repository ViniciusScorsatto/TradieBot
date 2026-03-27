# Product Roadmap Notes

## Current Product Shape

- `10` free invoices per month
- `NZD 5` unlocks another block of `10` invoices
- `5` curated invoice templates included for all users
- Telegram-first workflow with admin dashboard and marketing site

## Voice Invoicing Direction

Voice is a core differentiator, but it should not be an unlimited free feature.

### Near-term launch stance

- Keep text invoicing available as the default path
- Launch voice support with OpenAI transcription
- Include a small free monthly voice allowance
- Apply hard guardrails to prevent abuse and cost spikes

### Recommended guardrails

- Only allow transcription during an active invoice session
- Cap each voice note to `90` seconds
- Reject oversized or unsupported audio uploads
- Rate-limit voice transcriptions per user
- Track monthly voice usage separately from invoice quota
- Surface voice usage in the admin dashboard

### Billing direction

- Free users get a limited monthly voice allowance
- Paid usage should unlock more voice capacity
- Voice should be billed separately from the base invoice quota or bundled into a higher-value paid tier

## Suggested First Numbers

- `3` free voice transcriptions per month
- `90` seconds maximum per voice note
- Text entry remains available even when voice allowance is exhausted
