import Stripe from "stripe";
import { NextRequest, NextResponse } from "next/server";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY ?? "");

export async function POST(request: NextRequest) {
  const payload = await request.text();
  const signature = request.headers.get("stripe-signature");
  const secret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!signature || !secret) {
    return NextResponse.json({ error: "Missing Stripe signature configuration" }, { status: 400 });
  }

  try {
    const event = stripe.webhooks.constructEvent(payload, signature, secret);
    switch (event.type) {
      case "checkout.session.completed":
        return NextResponse.json({ ok: true, action: "unlock_credits" });
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
