ALTER TABLE "users"
ADD COLUMN IF NOT EXISTS "promotion_consent_at" TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS "promotion_consent_source" TEXT,
ADD COLUMN IF NOT EXISTS "promotion_opt_out_at" TIMESTAMPTZ;
