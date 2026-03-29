import Stripe from "stripe";
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "../../../../lib/prisma";
import { sendTelegramMessage } from "../../../../lib/telegram";
import { fulfillCheckoutWithDatabase } from "../../../../lib/stripe-webhook-fulfillment";

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
        return NextResponse.json(
          await fulfillCheckoutWithDatabase(event.data.object as Stripe.Checkout.Session, {
            prisma,
            sendTelegramMessage,
          }),
        );
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
