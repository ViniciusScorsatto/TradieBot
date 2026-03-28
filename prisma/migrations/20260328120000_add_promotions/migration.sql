CREATE TABLE IF NOT EXISTS "promotion_preferences" (
  "id" TEXT PRIMARY KEY,
  "user_id" TEXT NOT NULL,
  "category" TEXT NOT NULL,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT "promotion_preferences_user_id_category_key" UNIQUE ("user_id", "category")
);

CREATE TABLE IF NOT EXISTS "promotion_campaigns" (
  "id" TEXT PRIMARY KEY,
  "category" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "body" TEXT NOT NULL,
  "affiliate_url" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'DRAFT',
  "created_by" TEXT,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  "sent_at" TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS "promotion_deliveries" (
  "id" TEXT PRIMARY KEY,
  "campaign_id" TEXT NOT NULL,
  "user_id" TEXT NOT NULL,
  "telegram_user_id" TEXT NOT NULL,
  "status" TEXT NOT NULL DEFAULT 'PENDING',
  "error_message" TEXT,
  "delivered_at" TIMESTAMPTZ,
  "created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'promotion_preferences_user_id_fkey'
  ) THEN
    ALTER TABLE "promotion_preferences"
      ADD CONSTRAINT "promotion_preferences_user_id_fkey"
      FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'promotion_deliveries_campaign_id_fkey'
  ) THEN
    ALTER TABLE "promotion_deliveries"
      ADD CONSTRAINT "promotion_deliveries_campaign_id_fkey"
      FOREIGN KEY ("campaign_id") REFERENCES "promotion_campaigns"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'promotion_deliveries_user_id_fkey'
  ) THEN
    ALTER TABLE "promotion_deliveries"
      ADD CONSTRAINT "promotion_deliveries_user_id_fkey"
      FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
  END IF;
END $$;
