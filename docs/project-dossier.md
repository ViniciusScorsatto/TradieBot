# InvoiceBot Project Dossier

Generated: 2026-03-29

## Project Summary

InvoiceBot is a Telegram-first invoicing product for New Zealand small businesses and independent operators. The product lets a user create invoices by text or voice inside Telegram, generate branded PDF invoices, and optionally email them to clients. It includes a private admin dashboard, Stripe-powered paid top-ups, support ticket handling, and preference-based affiliate promotions.

Core surfaces:

- `bot/` Python Telegram bot
- `dashboard/` internal Next.js admin dashboard
- `site/` public marketing website
- `prisma/` shared PostgreSQL schema and migrations

## Core Product Features Implemented

### Telegram Bot

- `/start` onboarding with development notice and command guidance
- `/invoice` flow with saved client selection, search, pagination, and skip support
- text-based line item entry
- voice transcription with OpenAI
- multi-item parsing from single voice notes or text messages
- item editing, deletion, and per-line discounts
- `/generate` PDF confirmation and PDF generation
- `/profile` business setup flow including:
  - company name
  - address
  - email
  - phone
  - GST number
  - payment details
  - logo upload
- `/template` invoice template selection
- `/newclient` client creation
- `/clients` searchable, paginated client management with edit/delete
- `/history` and `/repeat`
- `/support` support ticket creation
- `/promotions` affiliate marketing preference selection

### Invoice Output

- branded multi-template PDF invoices
- one-page layout for up to 7 items
- two-page layout for 8 to 14 items
- GST-aware totals
- payment details block
- business logo support
- item-level discount display
- invoice summary with subtotal, discounts, GST, and total

### Billing

- Stripe checkout for invoice bundle purchases
- Stripe checkout for standalone voice top-ups
- webhook fulfillment into PostgreSQL
- Telegram confirmation after successful payment
- paid credit rollover

Current pricing model in code:

- free tier: `10` invoices per month
- free tier: `5` voice minutes per month
- invoice bundle: `20` invoices plus `10` bundled voice minutes
- standalone voice add-on: `10` voice minutes
- voice note cap: `60` seconds

### Email

- generated invoices can be emailed to the selected client
- Mailjet integration for sending PDF attachments
- email send history is tracked on invoices

### Admin Dashboard

- authenticated dashboard access
- sign-in and sign-out
- overview metrics from live database data
- billing page with live payment activity
- users page with:
  - quota visibility
  - add credits
  - reset usage
  - export user data
  - delete user data
- invoices page with recent invoice activity
- tickets page with live support queue and reply flow
- promotions page for affiliate campaign targeting

## Security Measures Implemented

- admin dashboard access is protected by login
- TOTP-capable admin authentication via seeded env configuration
- bot allowlist support through `ALLOWED_TELEGRAM_USER_IDS`
- bot admin privilege support through `ADMIN_TELEGRAM_USER_IDS`
- environment-based staging safeguards via `APP_ENV`
- production blocking of staging-only mock data command
- secrets stored via environment variables
- dedicated encryption key configured via `INVOICEBOT_ENCRYPTION_KEY`
- authenticated admin export route for user data exports
- destructive user deletion is limited to the admin dashboard
- database schema changes are migration-driven through Prisma
- runtime schema drift protections were removed in favor of migrations

## Privacy / Compliance Measures Implemented

### Public-Facing

- privacy policy page
- terms page
- privacy contact route on the site

### Administrative Controls

- user data export tooling
- user data deletion tooling
- minimized invoice activity exposure in admin list views
- masked client names in invoice history list
- hidden recipient email addresses in invoice history list view

### Documentation

- GDPR checklist
- Railway deployment guide
- database migration playbook

## Compliance Notes

This project is not automatically “certified compliant,” but it has a solid baseline for GDPR-style privacy controls:

- authenticated access to admin data
- data minimisation improvements in overview/list views
- user export and deletion tooling
- privacy and terms pages
- documented subprocessor usage
- documented migration and deployment process

Still recommended before broad public scale:

- full admin 2FA enrollment flow with QR setup and recovery codes
- retention schedule and cleanup jobs for stale/non-essential data
- formal subprocessors register section
- documented internal breach-response process
- role-based access control if more than one operator will use the dashboard
- legal review of privacy policy / terms before public launch, especially for New Zealand Privacy Act 2020 obligations
- legal review of affiliate / promotion consent flows before public launch under the Unsolicited Electronic Messages Act 2007

## Infrastructure

- Railway for deployment
- PostgreSQL as primary database
- Prisma schema and migrations as database source of truth
- Python Telegram bot worker
- Next.js dashboard and site
- OpenAI for transcription
- Stripe for payments
- Mailjet for invoice email delivery

## Operational Notes

- safest schema deploy order:
  1. deploy dashboard so Prisma migrations run
  2. deploy bot
  3. deploy other dependent services
- paid credits roll over; monthly reset only clears free usage counters
- staging can use different free-tier env values for testing
- the bot can be locked to approved testers

## Important Environment Variables

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
- `ALLOWED_TELEGRAM_USER_IDS`
- `ADMIN_TELEGRAM_USER_IDS`

## Status Snapshot

The product has a functioning end-to-end loop:

- create invoice in Telegram
- generate branded PDF
- email invoice to client
- handle payments through Stripe
- manage users, billing, tickets, invoice history, and promotions from the admin dashboard

This is now a strong MVP / early production candidate with meaningful operational, billing, privacy, and support foundations in place.

## Legal Caveats Before Public Launch

- Privacy policy and terms still require legal review. Self-drafted policies are helpful operationally, but they should not be treated as final legal documents for public launch.
- The affiliate and promotions feature should not be treated as legally launch-ready just because users can choose categories in the bot. New Zealand anti-spam rules for commercial electronic messages require a defensible consent model, sender identification, and unsubscribe handling.
- Promotion preferences in the bot are a good product foundation, but the consent wording, records, unsubscribe flow, and campaign rules should be legally reviewed before sending real commercial campaigns at scale.
