CREATE TABLE IF NOT EXISTS "users" (
  "id" TEXT PRIMARY KEY,
  "telegram_user_id" TEXT UNIQUE NOT NULL,
  "telegram_handle" TEXT,
  "first_name" TEXT,
  "last_name" TEXT,
  "plan_tier" TEXT NOT NULL DEFAULT 'FREE',
  "stripe_customer_id" TEXT UNIQUE,
  "invoice_count_this_month" INTEGER NOT NULL DEFAULT 0,
  "voice_transcriptions_this_month" INTEGER NOT NULL DEFAULT 0,
  "paid_invoice_credits" INTEGER NOT NULL DEFAULT 0,
  "paid_voice_credits" INTEGER NOT NULL DEFAULT 0,
  "joined_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "profiles" (
  "id" TEXT PRIMARY KEY,
  "user_id" TEXT UNIQUE NOT NULL,
  "company_name" TEXT,
  "address" TEXT,
  "gst_number" TEXT,
  "email" TEXT,
  "phone" TEXT,
  "bank_details" TEXT,
  "logo_url" TEXT,
  "default_template_id" TEXT NOT NULL DEFAULT 'classic-blue',
  "invoice_prefix" TEXT NOT NULL DEFAULT 'INV',
  "next_invoice_number" INTEGER NOT NULL DEFAULT 1,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "clients" (
  "id" TEXT PRIMARY KEY,
  "user_id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "company" TEXT,
  "email" TEXT,
  "phone" TEXT,
  "address" TEXT,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "invoice_drafts" (
  "id" TEXT PRIMARY KEY,
  "user_id" TEXT NOT NULL,
  "client_id" TEXT,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "notes" TEXT,
  "subtotal_cents" INTEGER NOT NULL DEFAULT 0,
  "gst_cents" INTEGER NOT NULL DEFAULT 0,
  "total_cents" INTEGER NOT NULL DEFAULT 0,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "invoice_draft_items" (
  "id" TEXT PRIMARY KEY,
  "draft_id" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "quantity" DOUBLE PRECISION NOT NULL DEFAULT 1,
  "unit_price" INTEGER NOT NULL,
  "discount_cents" INTEGER NOT NULL DEFAULT 0,
  "discount_percent" DOUBLE PRECISION,
  "line_total" INTEGER NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "invoices" (
  "id" TEXT PRIMARY KEY,
  "user_id" TEXT NOT NULL,
  "client_id" TEXT,
  "profile_snapshot" JSONB NOT NULL,
  "invoice_number" TEXT NOT NULL,
  "template_id" TEXT NOT NULL,
  "subtotal_cents" INTEGER NOT NULL,
  "gst_cents" INTEGER NOT NULL,
  "total_cents" INTEGER NOT NULL,
  "notes" TEXT,
  "pdf_url" TEXT,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "invoice_items" (
  "id" TEXT PRIMARY KEY,
  "invoice_id" TEXT NOT NULL,
  "description" TEXT NOT NULL,
  "quantity" DOUBLE PRECISION NOT NULL,
  "unit_price" INTEGER NOT NULL,
  "discount_cents" INTEGER NOT NULL DEFAULT 0,
  "discount_percent" DOUBLE PRECISION,
  "line_total" INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS "tickets" (
  "id" TEXT PRIMARY KEY,
  "user_id" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'OPEN',
  "subject" TEXT NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "ticket_messages" (
  "id" TEXT PRIMARY KEY,
  "ticket_id" TEXT NOT NULL,
  "sender" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "payments" (
  "id" TEXT PRIMARY KEY,
  "user_id" TEXT NOT NULL,
  "stripe_session_id" TEXT UNIQUE,
  "stripe_payment_id" TEXT UNIQUE,
  "purchase_type" TEXT NOT NULL,
  "amount_cents" INTEGER NOT NULL,
  "credits_purchased" INTEGER NOT NULL DEFAULT 0,
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "admin_users" (
  "id" TEXT PRIMARY KEY,
  "email" TEXT UNIQUE NOT NULL,
  "password_hash" TEXT NOT NULL,
  "totp_secret" TEXT,
  "recovery_codes" JSONB,
  "failed_login_count" INTEGER NOT NULL DEFAULT 0,
  "locked_until" TIMESTAMPTZ,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "voice_transcriptions_this_month" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "paid_voice_credits" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "profiles" ADD COLUMN IF NOT EXISTS "address" TEXT;
ALTER TABLE "invoice_draft_items" ADD COLUMN IF NOT EXISTS "discount_cents" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "invoice_draft_items" ADD COLUMN IF NOT EXISTS "discount_percent" DOUBLE PRECISION;
ALTER TABLE "invoice_items" ADD COLUMN IF NOT EXISTS "discount_cents" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "invoice_items" ADD COLUMN IF NOT EXISTS "discount_percent" DOUBLE PRECISION;
ALTER TABLE "payments" ADD COLUMN IF NOT EXISTS "purchase_type" TEXT NOT NULL DEFAULT 'invoice';
ALTER TABLE "payments" ADD COLUMN IF NOT EXISTS "updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW();

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'profiles_user_id_fkey'
  ) THEN
    ALTER TABLE "profiles"
      ADD CONSTRAINT "profiles_user_id_fkey"
      FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'clients_user_id_fkey'
  ) THEN
    ALTER TABLE "clients"
      ADD CONSTRAINT "clients_user_id_fkey"
      FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'invoice_drafts_user_id_fkey'
  ) THEN
    ALTER TABLE "invoice_drafts"
      ADD CONSTRAINT "invoice_drafts_user_id_fkey"
      FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'invoice_drafts_client_id_fkey'
  ) THEN
    ALTER TABLE "invoice_drafts"
      ADD CONSTRAINT "invoice_drafts_client_id_fkey"
      FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE SET NULL ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'invoice_draft_items_draft_id_fkey'
  ) THEN
    ALTER TABLE "invoice_draft_items"
      ADD CONSTRAINT "invoice_draft_items_draft_id_fkey"
      FOREIGN KEY ("draft_id") REFERENCES "invoice_drafts"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'invoices_user_id_fkey'
  ) THEN
    ALTER TABLE "invoices"
      ADD CONSTRAINT "invoices_user_id_fkey"
      FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'invoices_client_id_fkey'
  ) THEN
    ALTER TABLE "invoices"
      ADD CONSTRAINT "invoices_client_id_fkey"
      FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE SET NULL ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'invoice_items_invoice_id_fkey'
  ) THEN
    ALTER TABLE "invoice_items"
      ADD CONSTRAINT "invoice_items_invoice_id_fkey"
      FOREIGN KEY ("invoice_id") REFERENCES "invoices"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'tickets_user_id_fkey'
  ) THEN
    ALTER TABLE "tickets"
      ADD CONSTRAINT "tickets_user_id_fkey"
      FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ticket_messages_ticket_id_fkey'
  ) THEN
    ALTER TABLE "ticket_messages"
      ADD CONSTRAINT "ticket_messages_ticket_id_fkey"
      FOREIGN KEY ("ticket_id") REFERENCES "tickets"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'payments_user_id_fkey'
  ) THEN
    ALTER TABLE "payments"
      ADD CONSTRAINT "payments_user_id_fkey"
      FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;
