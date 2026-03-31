ALTER TABLE "profiles"
ADD COLUMN IF NOT EXISTS "default_hourly_rate_cents" INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS "time_tracking_sessions" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "draft_id" TEXT NOT NULL,
    "started_at" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "time_tracking_sessions_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "time_tracking_sessions_user_id_key" ON "time_tracking_sessions"("user_id");

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'time_tracking_sessions_user_id_fkey'
    ) THEN
        ALTER TABLE "time_tracking_sessions"
        ADD CONSTRAINT "time_tracking_sessions_user_id_fkey"
        FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
    END IF;
END $$;
