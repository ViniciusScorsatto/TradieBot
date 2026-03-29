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
- `MAILJET_API_KEY`
- `MAILJET_SECRET_KEY`
- `EMAIL_FROM`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_INVOICE_PRICE_ID`
- `STRIPE_VOICE_PRICE_ID`
- `MARKETING_SITE_URL`
- `APP_ENV`
- `ALLOWED_TELEGRAM_USER_IDS`
- `ADMIN_TELEGRAM_USER_IDS`
- `WARNING_THRESHOLD`
- `FREE_INVOICE_LIMIT`
- `PAID_INVOICE_BLOCK`
- `INVOICE_BUNDLE_VOICE_MINUTES`
- `PAID_VOICE_MINUTES`
- `FREE_VOICE_MINUTES_PER_MONTH`
- `VOICE_NOTE_MAX_SECONDS`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD_HASH`
- `ADMIN_TOTP_SECRET`
- `INVOICEBOT_ENCRYPTION_KEY`

## Service-Specific Variables

### Bot

- `TELEGRAM_TOKEN`
- `OPENAI_API_KEY`
- `MAILJET_API_KEY`
- `MAILJET_SECRET_KEY`
- `EMAIL_FROM`
- `STRIPE_SECRET_KEY`
- `STRIPE_INVOICE_PRICE_ID`
- `STRIPE_VOICE_PRICE_ID`
- `MARKETING_SITE_URL`
- `APP_ENV`
- `ALLOWED_TELEGRAM_USER_IDS`
- `ADMIN_TELEGRAM_USER_IDS`
- `WARNING_THRESHOLD`
- `FREE_INVOICE_LIMIT`
- `PAID_INVOICE_BLOCK`
- `INVOICE_BUNDLE_VOICE_MINUTES`
- `PAID_VOICE_MINUTES`
- `FREE_VOICE_MINUTES_PER_MONTH`
- `VOICE_NOTE_MAX_SECONDS`
- `DATABASE_URL`

### Dashboard

- `DATABASE_URL`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `TELEGRAM_TOKEN`
- `FREE_INVOICE_LIMIT`
- `PAID_INVOICE_BLOCK`
- `INVOICE_BUNDLE_VOICE_MINUTES`
- `FREE_VOICE_MINUTES_PER_MONTH`
- `PAID_VOICE_MINUTES`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD_HASH`
- `ADMIN_TOTP_SECRET`

### Site

- `NEXT_PUBLIC_TELEGRAM_BOT_URL`

### Quota Reset

- `DATABASE_URL`

## Notes

- Railway scans root `.env.example` files and suggests variables for import, which is why the repository keeps a root example env file.
- Prisma migrations are the source of truth for database structure. Do not add new tables or columns via runtime application code.
- The dashboard service uses `preDeployCommand = "npm run prisma:deploy"` so schema migrations run before startup.
- When you change the database schema:
  1. update `/prisma/schema.prisma`
  2. create a migration
  3. deploy migrations before deploying bot code that depends on the new schema
- On Railway, the safest order is:
  1. deploy `invoicebot-dashboard` so `prisma:deploy` runs
  2. deploy `invoicebot-bot`
  3. deploy any other services that depend on the schema
- The site and dashboard expose `/api/health` for Railway health checks.
- The bot is a worker process, so it does not use an HTTP health check.
- To lock the bot to approved testers, set `ALLOWED_TELEGRAM_USER_IDS` on the bot service as a comma-separated list like `123456789,987654321`. Leave it empty to keep the bot publicly accessible.
- To grant Telegram admin privileges, set `ADMIN_TELEGRAM_USER_IDS` on the bot service as a comma-separated list like `123456789`.
- Set `APP_ENV=staging` on your staging bot and `APP_ENV=production` on production. The `/mockclients` command is automatically blocked in production.
