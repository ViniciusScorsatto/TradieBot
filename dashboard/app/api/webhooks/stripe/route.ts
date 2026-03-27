import Stripe from "stripe";
import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { prisma } from "../../../../lib/prisma";

async function sendTelegramMessage(telegramUserId: string, text: string) {
  const token = process.env.TELEGRAM_TOKEN;
  if (!token) {
    return false;
  }

  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      chat_id: telegramUserId,
      text
    })
  });

  return response.ok;
}

async function ensureBillingSchema() {
  await prisma.$executeRawUnsafe(
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS paid_voice_credits INTEGER NOT NULL DEFAULT 0"
  );
  await prisma.$executeRawUnsafe(`
    CREATE TABLE IF NOT EXISTS payments (
      id TEXT PRIMARY KEY,
      user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      stripe_session_id TEXT UNIQUE,
      stripe_payment_id TEXT UNIQUE,
      purchase_type TEXT NOT NULL,
      amount_cents INTEGER NOT NULL,
      credits_purchased INTEGER NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'PENDING',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
  `);
}

async function ensureUser(telegramUserId: string, stripeCustomerId?: string | null) {
  const existing = await prisma.$queryRaw<{ id: string }[]>`
    SELECT id
    FROM users
    WHERE telegram_user_id = ${telegramUserId}
    LIMIT 1
  `;

  if (existing[0]?.id) {
    if (stripeCustomerId) {
      await prisma.$executeRaw`
        UPDATE users
        SET stripe_customer_id = COALESCE(stripe_customer_id, ${stripeCustomerId}),
            updated_at = NOW()
        WHERE id = ${existing[0].id}
      `;
    }
    return existing[0].id;
  }

  const userId = randomUUID();
  await prisma.$executeRaw`
    INSERT INTO users (id, telegram_user_id, stripe_customer_id)
    VALUES (${userId}, ${telegramUserId}, ${stripeCustomerId ?? null})
  `;
  return userId;
}

async function fulfillCheckout(session: Stripe.Checkout.Session) {
  const telegramUserId = session.metadata?.telegram_user_id ?? session.client_reference_id;
  const purchaseType = session.metadata?.purchase_type ?? "invoice";
  const creditsPurchased = Number(session.metadata?.credits_purchased ?? "0");

  if (!telegramUserId || !creditsPurchased) {
    return { ok: true, action: "ignored" };
  }

  await ensureBillingSchema();
  const userId = await ensureUser(
    String(telegramUserId),
    typeof session.customer === "string" ? session.customer : null
  );

  const inserted = await prisma.$executeRaw`
    INSERT INTO payments (
      id,
      user_id,
      stripe_session_id,
      stripe_payment_id,
      purchase_type,
      amount_cents,
      credits_purchased,
      status
    )
    VALUES (
      ${randomUUID()},
      ${userId},
      ${session.id},
      ${typeof session.payment_intent === "string" ? session.payment_intent : null},
      ${purchaseType},
      ${session.amount_total ?? 0},
      ${creditsPurchased},
      ${"SUCCEEDED"}
    )
    ON CONFLICT (stripe_session_id) DO NOTHING
  `;

  if (Number(inserted) === 0) {
    return { ok: true, action: "already_processed" };
  }

  if (purchaseType === "voice") {
    await prisma.$executeRaw`
      UPDATE users
      SET paid_voice_credits = paid_voice_credits + ${creditsPurchased},
          plan_tier = 'PAID',
          updated_at = NOW()
      WHERE id = ${userId}
    `;
    await sendTelegramMessage(
      String(telegramUserId),
      `Payment received. ${creditsPurchased} voice notes have been added to your account. You can keep invoicing by voice now.`
    );
    return { ok: true, action: "unlock_voice_credits" };
  }

  await prisma.$executeRaw`
    UPDATE users
    SET paid_invoice_credits = paid_invoice_credits + ${creditsPurchased},
        plan_tier = 'PAID',
        updated_at = NOW()
    WHERE id = ${userId}
  `;
  await sendTelegramMessage(
    String(telegramUserId),
    `Payment received. ${creditsPurchased} invoice credits have been added to your account. You can keep generating invoices now.`
  );
  return { ok: true, action: "unlock_invoice_credits" };
}

export async function POST(request: NextRequest) {
  const payload = await request.text();
  const signature = request.headers.get("stripe-signature");
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  const apiKey = process.env.STRIPE_SECRET_KEY;

  if (!signature || !secret || !apiKey) {
    return NextResponse.json({ error: "Missing Stripe configuration" }, { status: 400 });
  }

  try {
    const stripe = new Stripe(apiKey);
    const event = stripe.webhooks.constructEvent(payload, signature, secret);
    switch (event.type) {
      case "checkout.session.completed":
        return NextResponse.json(await fulfillCheckout(event.data.object as Stripe.Checkout.Session));
      case "payment_intent.payment_failed":
        return NextResponse.json({ ok: true, action: "notify_admin" });
      default:
        return NextResponse.json({ ok: true, action: "ignored" });
    }
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Webhook validation failed" },
      { status: 400 }
    );
  }
}
