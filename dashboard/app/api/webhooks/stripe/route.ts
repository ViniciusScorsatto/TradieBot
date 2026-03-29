import Stripe from "stripe";
import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { prisma } from "../../../../lib/prisma";
import { sendTelegramMessage } from "../../../../lib/telegram";
import { getInvoiceBundleVoiceMinutes, resolveCheckoutFulfillment } from "../../../../lib/stripe-fulfillment";

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
  const fulfillment = resolveCheckoutFulfillment(session, getInvoiceBundleVoiceMinutes());
  if (!fulfillment) {
    return { ok: true, action: "ignored" };
  }

  const userId = await ensureUser(
    fulfillment.telegramUserId,
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
      ${fulfillment.purchaseType},
      ${session.amount_total ?? 0},
      ${fulfillment.creditsPurchased},
      ${"SUCCEEDED"}
    )
    ON CONFLICT (stripe_session_id) DO NOTHING
  `;

  if (Number(inserted) === 0) {
    return { ok: true, action: "already_processed" };
  }

  if (fulfillment.purchaseType === "voice") {
    await prisma.$executeRaw`
      UPDATE users
      SET paid_voice_seconds = paid_voice_seconds + ${fulfillment.voiceSecondsToAdd},
          plan_tier = 'PAID',
          updated_at = NOW()
      WHERE id = ${userId}
    `;
    await sendTelegramMessage(
      fulfillment.telegramUserId,
      fulfillment.message
    );
    return { ok: true, action: fulfillment.action };
  }

  await prisma.$executeRaw`
    UPDATE users
    SET paid_invoice_credits = paid_invoice_credits + ${fulfillment.invoiceCreditsToAdd},
        paid_voice_seconds = paid_voice_seconds + ${fulfillment.voiceSecondsToAdd},
        plan_tier = 'PAID',
        updated_at = NOW()
    WHERE id = ${userId}
  `;
  await sendTelegramMessage(
    fulfillment.telegramUserId,
    fulfillment.message
  );
  return { ok: true, action: fulfillment.action };
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
