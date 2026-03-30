ALTER TABLE "profiles"
ADD COLUMN IF NOT EXISTS "quote_prefix" TEXT NOT NULL DEFAULT 'QUO',
ADD COLUMN IF NOT EXISTS "next_quote_number" INTEGER NOT NULL DEFAULT 1;

ALTER TABLE "invoice_drafts"
ADD COLUMN IF NOT EXISTS "document_type" TEXT NOT NULL DEFAULT 'INVOICE',
ADD COLUMN IF NOT EXISTS "source_quote_id" TEXT;

ALTER TABLE "invoices"
ADD COLUMN IF NOT EXISTS "source_quote_id" TEXT;

CREATE TABLE IF NOT EXISTS "quotes" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "client_id" TEXT,
    "profile_snapshot" JSONB NOT NULL,
    "quote_number" TEXT NOT NULL,
    "template_id" TEXT NOT NULL,
    "subtotal_cents" INTEGER NOT NULL,
    "gst_cents" INTEGER NOT NULL,
    "total_cents" INTEGER NOT NULL,
    "notes" TEXT,
    "emailed_to" TEXT,
    "emailed_at" TIMESTAMP(3),
    "converted_invoice_id" TEXT,
    "converted_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "quotes_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "quote_items" (
    "id" TEXT NOT NULL,
    "quote_id" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "quantity" DOUBLE PRECISION NOT NULL,
    "unit_price" INTEGER NOT NULL,
    "discount_cents" INTEGER NOT NULL DEFAULT 0,
    "discount_percent" DOUBLE PRECISION,
    "line_total" INTEGER NOT NULL,
    CONSTRAINT "quote_items_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "quotes_user_id_quote_number_key" ON "quotes"("user_id", "quote_number");
CREATE INDEX IF NOT EXISTS "quotes_user_id_created_at_idx" ON "quotes"("user_id", "created_at" DESC);
CREATE INDEX IF NOT EXISTS "quote_items_quote_id_idx" ON "quote_items"("quote_id");

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'quotes_user_id_fkey'
    ) THEN
        ALTER TABLE "quotes"
        ADD CONSTRAINT "quotes_user_id_fkey"
        FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'quotes_client_id_fkey'
    ) THEN
        ALTER TABLE "quotes"
        ADD CONSTRAINT "quotes_client_id_fkey"
        FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE SET NULL ON UPDATE CASCADE;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'quote_items_quote_id_fkey'
    ) THEN
        ALTER TABLE "quote_items"
        ADD CONSTRAINT "quote_items_quote_id_fkey"
        FOREIGN KEY ("quote_id") REFERENCES "quotes"("id") ON DELETE CASCADE ON UPDATE CASCADE;
    END IF;
END $$;
