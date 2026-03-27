# Railway Deployment Setup

This repository is a mixed monorepo:

- `bot/` is an isolated Python service.
- `dashboard/` and `site/` are shared JavaScript workspaces that depend on root config and `packages/shared/`.
- `scripts/reset_monthly_quota.py` is a scheduled job.

Because Railway config-as-code applies to a single service per file, each deployable surface has its own config file:

- `/bot/railway.toml`
- `/dashboard/railway.toml`
- `/site/railway.toml`
- `/scripts/railway-quota-reset.toml`

## Create Railway Services

Create four Railway services in one project:

1. `invoicebot-bot`
2. `invoicebot-dashboard`
3. `invoicebot-site`
4. `invoicebot-quota-reset`

## Recommended Service Settings

### `invoicebot-bot`

- Root Directory: `/bot`
- Config as Code file: `/bot/railway.toml`
- Source repo: this GitHub repository

### `invoicebot-dashboard`

- Root Directory: `/`
- Config as Code file: `/dashboard/railway.toml`
- Exposed port: leave automatic
- Domain: attach your admin domain here

The dashboard builds from the monorepo root so Railway can install workspace dependencies and shared packages.

### `invoicebot-site`

- Root Directory: `/`
- Config as Code file: `/site/railway.toml`
- Exposed port: leave automatic
- Domain: attach your public marketing domain here

### `invoicebot-quota-reset`

- Root Directory: `/`
- Config as Code file: `/scripts/railway-quota-reset.toml`

This is a cron service. It should run and exit. Railway schedules cron jobs in UTC, so this repo runs the job daily at `12:05 UTC`, then the script itself checks whether it is the first day of the month in `Pacific/Auckland` before resetting quotas. That keeps the behavior aligned with New Zealand time across daylight saving changes.

## Managed Services

Add the following Railway-managed resources:

- PostgreSQL
- Redis (optional for launch)

## Shared Variables

Set these at the project level if multiple services need them:

- `DATABASE_URL`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`
- `TELEGRAM_TOKEN`
- `TELEGRAM_BOT_URL`
- `NEXT_PUBLIC_TELEGRAM_BOT_URL`
- `OPENAI_API_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD_HASH`
- `ADMIN_TOTP_SECRET`
- `INVOICEBOT_ENCRYPTION_KEY`

## Service-Specific Variables

### Bot

- `TELEGRAM_TOKEN`
- `OPENAI_API_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_PRICE_ID`
- `DATABASE_URL`

### Dashboard

- `DATABASE_URL`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD_HASH`
- `ADMIN_TOTP_SECRET`

### Site

- `NEXT_PUBLIC_TELEGRAM_BOT_URL`

### Quota Reset

- `DATABASE_URL`

## Notes

- Railway scans root `.env.example` files and suggests variables for import, which is why the repository keeps a root example env file.
- The dashboard service uses `preDeployCommand = "npm run prisma:deploy"` so schema migrations run before startup.
- The site and dashboard expose `/api/health` for Railway health checks.
- The bot is a worker process, so it does not use an HTTP health check.
