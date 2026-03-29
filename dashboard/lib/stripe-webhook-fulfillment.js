import { randomUUID as cryptoRandomUUID } from "crypto";
import { getInvoiceBundleVoiceMinutes, resolveCheckoutFulfillment } from "./stripe-fulfillment.js";

async function ensureUser(prisma, telegramUserId, stripeCustomerId, randomUUID = cryptoRandomUUID) {
  const existing = await prisma.user.findFirst({
    where: { telegramUserId },
    select: { id: true, stripeCustomerId: true },
  });

  if (existing?.id) {
    if (stripeCustomerId && !existing.stripeCustomerId) {
      await prisma.user.update({
        where: { id: existing.id },
        data: { stripeCustomerId },
      });
    }
    return existing.id;
  }

  const created = await prisma.user.create({
    data: {
      id: randomUUID(),
      telegramUserId,
      stripeCustomerId: stripeCustomerId ?? null,
    },
    select: { id: true },
  });

  return created.id;
}

export async function fulfillCheckoutWithDatabase(
  session,
  {
    prisma,
    sendTelegramMessage,
    randomUUID = cryptoRandomUUID,
    invoiceBundleVoiceMinutes = getInvoiceBundleVoiceMinutes(),
  },
) {
  const fulfillment = resolveCheckoutFulfillment(session, invoiceBundleVoiceMinutes);
  if (!fulfillment) {
    return { ok: true, action: "ignored" };
  }

  const existingPayment = await prisma.payment.findFirst({
    where: { stripeSessionId: session.id },
    select: { id: true },
  });
  if (existingPayment?.id) {
    return { ok: true, action: "already_processed" };
  }

  const userId = await ensureUser(
    prisma,
    fulfillment.telegramUserId,
    typeof session.customer === "string" ? session.customer : null,
    randomUUID,
  );

  await prisma.payment.create({
    data: {
      id: randomUUID(),
      userId,
      stripeSessionId: session.id,
      stripePaymentId: typeof session.payment_intent === "string" ? session.payment_intent : null,
      purchaseType: fulfillment.purchaseType,
      amountCents: session.amount_total ?? 0,
      creditsPurchased: fulfillment.creditsPurchased,
      status: "SUCCEEDED",
    },
  });

  if (fulfillment.purchaseType === "voice") {
    await prisma.user.update({
      where: { id: userId },
      data: {
        paidVoiceSeconds: { increment: fulfillment.voiceSecondsToAdd },
        planTier: "PAID",
      },
    });
  } else {
    await prisma.user.update({
      where: { id: userId },
      data: {
        paidInvoiceCredits: { increment: fulfillment.invoiceCreditsToAdd },
        paidVoiceSeconds: { increment: fulfillment.voiceSecondsToAdd },
        planTier: "PAID",
      },
    });
  }

  await sendTelegramMessage(fulfillment.telegramUserId, fulfillment.message);
  return { ok: true, action: fulfillment.action };
}
