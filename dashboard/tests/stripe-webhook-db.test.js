import test from "node:test";
import assert from "node:assert/strict";
import { fulfillCheckoutWithDatabase } from "../lib/stripe-webhook-fulfillment.js";

function createFakePrisma() {
  const state = {
    users: [],
    payments: [],
  };

  const prisma = {
    user: {
      async findFirst({ where, select }) {
        const user = state.users.find((entry) => entry.telegramUserId === where.telegramUserId) ?? null;
        if (!user || !select) {
          return user;
        }
        return Object.fromEntries(Object.keys(select).map((key) => [key, user[key]]));
      },
      async update({ where, data }) {
        const user = state.users.find((entry) => entry.id === where.id);
        if (!user) {
          throw new Error("User not found");
        }
        if (data.stripeCustomerId !== undefined) {
          user.stripeCustomerId = data.stripeCustomerId;
        }
        if (data.planTier !== undefined) {
          user.planTier = data.planTier;
        }
        if (data.paidInvoiceCredits?.increment) {
          user.paidInvoiceCredits += data.paidInvoiceCredits.increment;
        }
        if (data.paidVoiceSeconds?.increment) {
          user.paidVoiceSeconds += data.paidVoiceSeconds.increment;
        }
        return user;
      },
      async create({ data, select }) {
        const user = {
          id: data.id,
          telegramUserId: data.telegramUserId,
          stripeCustomerId: data.stripeCustomerId ?? null,
          planTier: "FREE",
          paidInvoiceCredits: 0,
          paidVoiceSeconds: 0,
        };
        state.users.push(user);
        if (!select) {
          return user;
        }
        return Object.fromEntries(Object.keys(select).map((key) => [key, user[key]]));
      },
    },
    payment: {
      async findFirst({ where, select }) {
        const payment = state.payments.find((entry) => entry.stripeSessionId === where.stripeSessionId) ?? null;
        if (!payment || !select) {
          return payment;
        }
        return Object.fromEntries(Object.keys(select).map((key) => [key, payment[key]]));
      },
      async create({ data }) {
        state.payments.push({ ...data });
        return data;
      },
    },
  };

  return { prisma, state };
}

test("creates user, records payment, and increments invoice + bundled voice credits", async () => {
  const sent = [];
  const { prisma, state } = createFakePrisma();

  const result = await fulfillCheckoutWithDatabase(
    {
      id: "cs_invoice_1",
      customer: "cus_123",
      payment_intent: "pi_123",
      amount_total: 500,
      metadata: {
        telegram_user_id: "123456",
        purchase_type: "invoice",
        credits_purchased: "20",
      },
    },
    {
      prisma,
      sendTelegramMessage: async (telegramUserId, message) => {
        sent.push({ telegramUserId, message });
        return true;
      },
      randomUUID: (() => {
        let index = 0;
        return () => `id-${++index}`;
      })(),
      invoiceBundleVoiceMinutes: 10,
    },
  );

  assert.deepEqual(result, { ok: true, action: "unlock_invoice_credits" });
  assert.equal(state.users.length, 1);
  assert.equal(state.payments.length, 1);
  assert.equal(state.users[0].telegramUserId, "123456");
  assert.equal(state.users[0].stripeCustomerId, "cus_123");
  assert.equal(state.users[0].planTier, "PAID");
  assert.equal(state.users[0].paidInvoiceCredits, 20);
  assert.equal(state.users[0].paidVoiceSeconds, 600);
  assert.equal(sent.length, 1);
});

test("creates payment and increments voice credits for standalone voice top-up", async () => {
  const { prisma, state } = createFakePrisma();

  await fulfillCheckoutWithDatabase(
    {
      id: "cs_voice_1",
      customer: null,
      payment_intent: "pi_voice_1",
      amount_total: 500,
      metadata: {
        telegram_user_id: "222",
        purchase_type: "voice",
        credits_purchased: "10",
      },
    },
    {
      prisma,
      sendTelegramMessage: async () => true,
      randomUUID: (() => {
        let index = 0;
        return () => `voice-${++index}`;
      })(),
      invoiceBundleVoiceMinutes: 10,
    },
  );

  assert.equal(state.users[0].paidInvoiceCredits, 0);
  assert.equal(state.users[0].paidVoiceSeconds, 600);
  assert.equal(state.payments[0].purchaseType, "voice");
});

test("ignores duplicate checkout sessions once the payment has already been recorded", async () => {
  const { prisma, state } = createFakePrisma();
  state.users.push({
    id: "user-1",
    telegramUserId: "123456",
    stripeCustomerId: null,
    planTier: "FREE",
    paidInvoiceCredits: 0,
    paidVoiceSeconds: 0,
  });
  state.payments.push({
    id: "payment-1",
    stripeSessionId: "cs_existing",
  });

  const result = await fulfillCheckoutWithDatabase(
    {
      id: "cs_existing",
      customer: "cus_existing",
      payment_intent: "pi_existing",
      amount_total: 500,
      metadata: {
        telegram_user_id: "123456",
        purchase_type: "invoice",
        credits_purchased: "20",
      },
    },
    {
      prisma,
      sendTelegramMessage: async () => true,
      randomUUID: () => "unused-id",
      invoiceBundleVoiceMinutes: 10,
    },
  );

  assert.deepEqual(result, { ok: true, action: "already_processed" });
  assert.equal(state.payments.length, 1);
  assert.equal(state.users[0].paidInvoiceCredits, 0);
  assert.equal(state.users[0].paidVoiceSeconds, 0);
});
