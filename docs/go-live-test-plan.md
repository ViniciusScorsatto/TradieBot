# InvoiceBot Go-Live Test Plan

This is the living source of truth for pre-launch validation, manual signoff, and final release readiness. Update it as features close, blockers are removed, or launch risks change.

## Current Status

- Last updated: `2026-03-30`
- Ready:
  - Core Telegram invoice flow is implemented
  - Stripe billing, webhook fulfillment, and rollover behavior are implemented
  - Invoice email sending is implemented
  - Admin dashboard auth, billing, tickets, invoices, and user actions are implemented
  - AI bug-triage first response is implemented behind KB/config setup
  - Automated smoke coverage exists for parser, PDF smoke, compliance rules, retention logic, AI support service, and Stripe fulfillment
- Blocked:
  - Legal review of privacy policy and terms before public launch
  - Legal review of promotions consent and unsubscribe wording before public launch
  - Full manual staging signoff pass still needs to be completed and recorded here
- Open risks:
  - Promotions should be treated as launch-risk until legal review explicitly clears them
  - Admin auth uses seeded credentials/TOTP rather than a full self-serve admin security flow
  - Automated coverage is solid for smoke tests, but the final launch decision still depends on manual end-to-end testing

## Severity Labels

- `Launch blocker`: must be complete before public production launch
- `Must test manually`: required staging or production-readiness validation
- `Nice to have`: useful hardening, not required for initial public release

## Recommended Execution Order

1. Run automated checks
2. Complete the full staging manual run in this document
3. Verify production configuration and deploy order
4. Review launch blockers and decide go / no-go

## Preflight

### Environment and deploy readiness

- `Launch blocker` Confirm Railway production env vars are present and current:
  - `DATABASE_URL`
  - `TELEGRAM_TOKEN`
  - `OPENAI_API_KEY`
  - `MAILJET_API_KEY`
  - `MAILJET_SECRET_KEY`
  - `EMAIL_FROM`
  - `STRIPE_SECRET_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - `STRIPE_INVOICE_PRICE_ID`
  - `STRIPE_VOICE_PRICE_ID`
  - `NEXTAUTH_SECRET`
  - `NEXTAUTH_URL`
  - `ADMIN_EMAIL`
  - `ADMIN_PASSWORD_HASH`
  - `ADMIN_TOTP_SECRET`
  - `INVOICEBOT_ENCRYPTION_KEY`
- `Launch blocker` Confirm Railway runtime uses Node `20.19+` or `22.12+` for Prisma 7 compatibility.
- `Launch blocker` Confirm production deploy order when schema changes are involved:
  1. deploy `invoicebot-dashboard`
  2. deploy `invoicebot-bot`
  3. deploy any other dependent service
- `Launch blocker` Confirm Stripe production products, prices, and webhook endpoint are live-mode values only.
- `Launch blocker` Confirm Mailjet sender/domain is verified for the production sender in `EMAIL_FROM`.
- `Must test manually` Confirm `MARKETING_SITE_URL`, `NEXTAUTH_URL`, and `NEXT_PUBLIC_TELEGRAM_BOT_URL` use production domains, not staging domains.
- `Must test manually` Confirm `APP_ENV=production` on production bot and staging-only commands are blocked.
- `Must test manually` Confirm `ALLOWED_TELEGRAM_USER_IDS` is set correctly for launch stance:
  - empty for public bot
  - populated if still running a gated beta

### Feature flags and optional systems

- `Must test manually` If AI bug triage should be live, confirm:
  - `OPENAI_SUPPORT_MODEL`
  - `OPENAI_SUPPORT_VECTOR_STORE_ID`
  - `OPENAI_SUPPORT_DAILY_LIMIT`
  - support KB synced from `docs/support-kb/bugs`
- `Launch blocker` Decide promotions launch stance:
  - launch enabled only if legal review clears consent/unsubscribe flow
  - otherwise launch with promotions operationally off
- `Must test manually` Confirm retention env vars are set on quota-reset service:
  - `DRAFT_RETENTION_DAYS`
  - `CLOSED_TICKET_RETENTION_DAYS`
  - `PROMOTION_DELIVERY_RETENTION_DAYS`

## Automated Checks

Run these before every serious staging signoff and before production promotion:

```bash
npm test
python3 -m compileall bot/invoicebot scripts
```

### Current automated coverage

- `Must test manually` `npm run test:dashboard`
  - Stripe fulfillment mapping
  - Stripe webhook DB write path
  - duplicate-session idempotency
- `Must test manually` `npm run test:bot`
  - parser behavior for text and voice phrasing
  - invoice PDF smoke
  - NZ invoice compliance rules
  - AI support service fallback/success behavior
  - retention policy helper behavior
  - promotions consent state behavior
- `Nice to have` Add broader UI/browser automation later; it is not the current release gate.

### Still not fully covered by automation

- `Must test manually` Telegram bot end-to-end conversational flows
- `Must test manually` real Stripe Checkout redirect + webhook round trip in staging
- `Must test manually` Mailjet delivery with real sender config
- `Must test manually` dashboard login and page rendering in deployed environment
- `Must test manually` promotions consent, unsubscribe, and admin send flow in deployed environment

## Manual Test Matrix

Use this table format when recording results:

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|

### A. Bot / onboarding

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|
| BOT-01 | `/start` | Production-like staging bot | Send `/start` | Development/beta language is appropriate for current launch stance and commands are visible | Pending | |
| BOT-02 | `/profile` | Fresh test user | Run `/profile` and fill company, address, email, phone, GST, payment details, logo | Profile saves cleanly and keep/skip buttons work | Pending | |
| BOT-03 | `/template` | Saved profile exists | Run `/template`, pick a template | Default template changes and stays selected | Pending | |
| BOT-04 | `/newclient` | Fresh draft not required | Run `/newclient` with company/email/phone/address combinations including skips | Client saves correctly and optional-field skip buttons work | Pending | |
| BOT-05 | `/clients` | At least 12 clients | Run `/clients`, paginate, search by 3+ starting letters, edit a field, delete a client | Search/pagination/edit/delete all work and list refreshes correctly | Pending | |
| BOT-06 | `/history` and `/repeat` | At least one generated invoice exists | Run `/history`, then `/repeat` | Recent invoice appears and can be loaded as a new draft | Pending | |
| BOT-07 | `/promotions` | Test user with no prior consent | Run `/promotions`, opt in, pick categories, unsubscribe, re-enable | Consent gate works, category selection only appears after consent, unsubscribe clears preferences | Pending | |

### B. Invoice drafting and editing

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|
| INV-01 | `/invoice` with client picker | 12+ saved clients | Run `/invoice`, paginate/search/select a client | Client picker works and selected client is attached to draft | Pending | |
| INV-02 | Skip client | Client picker available | Run `/invoice`, choose skip | Draft continues without a client | Pending | |
| INV-03 | Text item entry | Active draft | Add one item, then multiple items in one message | Items parse correctly and draft count updates | Pending | |
| INV-04 | Edit/delete item | Draft with 3 items | Use inline item controls and draft editor | Items can be edited or deleted without corrupting order | Pending | |
| INV-05 | Per-line discount | Draft with priced item | Apply discount `%` and `$`, then remove with `0` | Discount never exceeds line value and summary updates correctly | Pending | |
| INV-06 | Item limits | Draft with 14 items | Try to add a 15th item | Bot blocks the addition with the two-page guardrail message | Pending | |

### C. Voice transcription and recovery

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|
| VOICE-01 | Normal voice add | Active draft with voice quota available | Send a short voice note with one item | Transcript becomes one item and usage decreases | Pending | |
| VOICE-02 | Multi-item voice parsing | Active draft with voice quota available | Say `Wood 45. Service 100. Materials 45.` | Transcript becomes 3 items, not one long line | Pending | |
| VOICE-03 | Over-length rejection | Active draft | Send a voice note over 60 seconds | Bot rejects it cleanly before transcription | Pending | |
| VOICE-04 | Free-tier exhaustion | Test user near free voice cap | Exhaust free voice minutes | Bot offers paid voice/text fallback and keeps text path usable | Pending | |
| VOICE-05 | Paid rollover use | User with paid voice minutes | Consume voice beyond free allowance | Paid rollover minutes are consumed correctly | Pending | |
| VOICE-06 | Failed transcription recovery | Use a malformed/unreadable audio or force failure | Send voice note that fails transcription | Bot keeps the draft open and shows retry/text fallback controls | Pending | |
| VOICE-07 | Parse-failure recovery | Use a transcript that cannot become an item | Send voice note that transcribes but cannot parse | Bot shows retry/text/examples fallback without breaking the draft | Pending | |

### D. Invoice generation, PDF, GST, and email

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|
| PDF-01 | 1-item invoice | Valid profile and client | Generate invoice with 1 item | PDF looks correct and totals are accurate | Pending | |
| PDF-02 | 7-item invoice | Valid profile and client | Generate invoice with 7 items | Stays on one page cleanly | Pending | |
| PDF-03 | 8-item invoice | Valid profile and client | Generate invoice with 8 items | Splits to two pages cleanly | Pending | |
| PDF-04 | 14-item invoice | Valid profile and client | Generate invoice with 14 items | Two-page PDF still renders correctly | Pending | |
| PDF-05 | GST off | Profile without GST number | Generate invoice | GST line is not applied and labels remain correct | Pending | |
| PDF-06 | GST on | Profile with GST number | Generate invoice | GST is calculated and shown correctly | Pending | |
| PDF-07 | NZ taxable-supply guardrails | GST-charging invoice above NZD 1,000 with missing client identifiers | Try to generate invoice | Bot blocks generation and tells user what is missing | Pending | |
| PDF-08 | Payment details and logo | Profile has both | Generate invoice | Logo and payment details render properly in PDF | Pending | |
| PDF-09 | Email to client | Client has email and Mailjet config is valid | Generate invoice and tap `Email to client` | Email sends successfully and user gets confirmation | Pending | |
| PDF-10 | Invoice history record | At least one emailed invoice | Open admin invoices page | Email status and sent metadata appear correctly | Pending | |

### E. Billing and quota behavior

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|
| BILL-01 | Invoice bundle checkout | User near invoice limit | Trigger invoice paywall and complete Stripe checkout | Purchase succeeds, webhook fulfills, invoice credits and bundled voice minutes are added | Pending | |
| BILL-02 | Voice add-on checkout | User near voice limit | Trigger voice paywall and complete Stripe checkout | Purchase succeeds and extra voice minutes are added | Pending | |
| BILL-03 | Webhook idempotency | Completed Stripe session | Replay same event/session in staging-safe manner | No duplicate crediting occurs | Pending | |
| BILL-04 | Telegram payment confirmation | Successful purchase | Complete checkout | Bot sends payment confirmation into Telegram | Pending | |
| BILL-05 | Admin quota visibility | Completed purchase exists | Open `/users` | Used/free/paid quota values reflect the purchase | Pending | |
| BILL-06 | Admin reset/add-credit actions | Admin logged in | Add credits, reset usage, verify banner states | Admin actions work and UI confirms completion | Pending | |

### F. Dashboard

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|
| DASH-01 | Login/logout | Admin credentials available | Open dashboard, log in, sign out | Auth gate works and protected pages require login | Pending | |
| DASH-02 | Overview | Live staging data exists | Open overview page | Live metrics, invoices, tickets, and payment snapshots render | Pending | |
| DASH-03 | Users roster | At least one active user | Open `/users` and use controls | User detail, export, delete, add-credit, and reset controls work | Pending | |
| DASH-04 | Billing page | Payment data exists | Open `/billing` | Recent payment activity is live and accurate | Pending | |
| DASH-05 | Invoices page | Generated invoices exist | Open `/invoices` | Recent invoice activity displays correctly with minimized exposure | Pending | |
| DASH-06 | Tickets page | At least one support ticket exists | Open `/tickets`, change status, send reply | Ticket thread updates and Telegram reply is sent | Pending | |
| DASH-07 | Promotions page | At least one consented user exists | Open `/promotions`, send test campaign | Only consented/opted-in users receive it and counts look right | Pending | |

### G. Support and AI bug triage

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|
| SUP-01 | Standard support ticket | AI can be on or off | Create a non-bug ticket from Telegram | Ticket is created without AI triage and appears in admin | Pending | |
| SUP-02 | AI bug triage success | AI KB synced and env vars set | Create a bug ticket matching KB content | User receives one grounded AI first response and ticket stays open | Pending | |
| SUP-03 | AI bug triage no-match | AI enabled | Create a bug ticket with no strong KB match | User gets queued-for-review fallback and no fake AI answer is stored | Pending | |
| SUP-04 | Human follow-up after AI | Existing bug ticket with AI reply | Reply from admin dashboard | User receives human reply and thread remains coherent | Pending | |

### H. Privacy, compliance, and operations

| ID | Area | Setup | Steps | Expected result | Status | Notes |
|---|---|---|---|---|---|---|
| OPS-01 | Privacy page | Site deployed | Open `/privacy` | Page is live and reachable from nav/footer | Pending | |
| OPS-02 | Terms page | Site deployed | Open `/terms` | Page is live and reachable from nav/footer | Pending | |
| OPS-03 | Export/delete | Admin logged in with a staging user | Export one user, then delete one test user | Export returns a file and delete removes the record safely | Pending | |
| OPS-04 | Retention config | Quota-reset service configured | Check env vars and cron config | Retention vars are set and cleanup job is wired | Pending | |
| OPS-05 | Breach response docs | Repo/docs available | Review doc links before launch | Internal breach-response playbook is accessible to operator | Pending | |
| OPS-06 | Promotions legal gate | Promotions implemented | Verify legal review state | If legal review is incomplete, promotions are treated as blocked or disabled for launch | Pending | |

## Launch Gates

### Launch blockers

- Legal review of [privacy policy](/Users/viniciusscorsatto/Desktop/AI%20Projects/Nz%20Fuel/site/app/privacy/page.tsx) and [terms](/Users/viniciusscorsatto/Desktop/AI%20Projects/Nz%20Fuel/site/app/terms/page.tsx)
- Legal review of promotions consent/unsubscribe flow before commercial campaigns are sent
- Full staging manual signoff for all `Must test manually` scenarios above
- Production env verification complete
- Stripe live-mode configuration verified
- Mailjet sender/domain verified
- Final migration/deploy order confirmed and tested

### Recommended before launch

- Review [docs/retention-policy.md](/Users/viniciusscorsatto/Desktop/AI%20Projects/Nz%20Fuel/docs/retention-policy.md) against real business needs
- Review [docs/breach-response.md](/Users/viniciusscorsatto/Desktop/AI%20Projects/Nz%20Fuel/docs/breach-response.md) and assign a named incident owner
- Confirm AI bug-triage KB freshness if AI support will be live

### Nice to have

- Full admin 2FA enrollment flow with QR and recovery codes
- Broader browser/UI automation
- More formal subprocessors register

## Maintenance Workflow

- Treat this file as the single living checklist for launch readiness.
- After each meaningful feature close-out, update:
  - `Current Status`
  - affected manual scenarios
  - blockers or risks
- Keep a dated note in `Notes` when an item is completed rather than removing the scenario.
- If a feature changes a critical path, update the matching scenario in the same code change or deploy prep pass.

## Launch With Promotions Off Fallback

If legal review of promotions is still incomplete at launch time:

1. Do not send real campaigns from the admin promotions page
2. Keep the feature operationally disabled for public use
3. Launch the core invoicing product without promotions
4. Re-run the promotions section of this checklist after legal signoff
