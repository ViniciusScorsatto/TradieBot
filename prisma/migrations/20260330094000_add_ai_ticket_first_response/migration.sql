ALTER TABLE "tickets"
ADD COLUMN IF NOT EXISTS "ai_first_response_sent_at" TIMESTAMPTZ;
