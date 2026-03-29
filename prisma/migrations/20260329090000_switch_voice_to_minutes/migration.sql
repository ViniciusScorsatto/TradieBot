ALTER TABLE "users"
  ADD COLUMN IF NOT EXISTS "voice_seconds_this_month" INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS "paid_voice_seconds" INTEGER NOT NULL DEFAULT 0;

UPDATE "users"
SET "voice_seconds_this_month" = CASE
      WHEN "voice_seconds_this_month" = 0 AND COALESCE("voice_transcriptions_this_month", 0) > 0
        THEN COALESCE("voice_transcriptions_this_month", 0) * 60
      ELSE "voice_seconds_this_month"
    END,
    "paid_voice_seconds" = CASE
      WHEN "paid_voice_seconds" = 0 AND COALESCE("paid_voice_credits", 0) > 0
        THEN COALESCE("paid_voice_credits", 0) * 60
      ELSE "paid_voice_seconds"
    END;
