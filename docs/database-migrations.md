# Database Migrations Playbook

Use this whenever the database schema needs to change.

## Source Of Truth

- `/prisma/schema.prisma` is the source of truth.
- Do not add tables or columns through runtime application code.

## Normal Change Flow

1. Update `/prisma/schema.prisma`
2. Create a migration locally
3. Review the generated SQL
4. Commit:
   - schema changes
   - migration files
   - app code that depends on the new schema
5. Deploy `invoicebot-dashboard` first so `npm run prisma:deploy` runs
6. Deploy `invoicebot-bot`
7. Deploy any other dependent services

## Local Commands

Use Node `20.19+` or `22.12+` before running Prisma 7 commands. This repo includes [`.nvmrc`](/Users/viniciusscorsatto/Desktop/AI%20Projects/Nz%20Fuel/.nvmrc) to make the expected version obvious.

Create a migration locally:

```bash
npm run prisma:migrate -- --name your_change_name
```

Regenerate Prisma client if needed:

```bash
npm run prisma:generate
```

Apply committed migrations in a deployed environment:

```bash
npm run prisma:deploy
```

## Railway Order

1. Deploy dashboard
2. Confirm migration completed
3. Deploy bot
4. Deploy other services

## Safety Rules

- Never deploy bot code that requires a new column/table before the migration is applied.
- Keep migrations additive when possible.
- For risky data changes, make a backup first.
- If a schema change touches billing, tickets, or invoice generation, test it in staging first.
