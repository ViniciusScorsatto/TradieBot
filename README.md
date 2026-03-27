# InvoiceBot

Telegram-first invoicing product for tradies with:

- `bot/` Python Telegram bot
- `dashboard/` internal Next.js admin dashboard
- `site/` public marketing website
- `prisma/` shared schema for Railway PostgreSQL

## Stack

- Railway for app and managed services
- PostgreSQL via Prisma schema
- Python `python-telegram-bot` bot runtime
- Next.js 14 for admin and site
- Stripe for billing

## Quick Start

1. Copy `.env.example` to `.env`.
2. Install web dependencies with `npm install`.
3. Create a Python virtualenv in `bot/` and install `requirements.txt`.
4. Run Prisma migrations or `prisma db push`.
5. Start each app with the scripts below.

## Scripts

- `npm run dev:dashboard`
- `npm run dev:site`
- `npm run prisma:generate`
- `npm run prisma:migrate`
- `python -m invoicebot.main` from `bot/`

## Project Shape

- `bot/` Telegram command handlers, invoice parser, PDF rendering, and service layer
- `dashboard/` admin metrics, users, billing, tickets, and Stripe webhook
- `site/` launch-ready public marketing site
- `packages/shared/` template catalog and shared app constants
- `scripts/reset_monthly_quota.py` Railway cron job target
