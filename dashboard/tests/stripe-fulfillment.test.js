import test from "node:test";
import assert from "node:assert/strict";
import { resolveCheckoutFulfillment } from "../lib/stripe-fulfillment.js";

test("ignores checkout sessions without a usable telegram user id or credits", () => {
  assert.equal(resolveCheckoutFulfillment({ metadata: {} }, 10), null);
  assert.equal(
    resolveCheckoutFulfillment(
      {
        metadata: {
          telegram_user_id: "123",
          credits_purchased: "0",
        },
      },
      10,
    ),
    null,
  );
});

test("builds voice top-up fulfillment correctly", () => {
  const result = resolveCheckoutFulfillment(
    {
      metadata: {
        telegram_user_id: "123456",
        purchase_type: "voice",
        credits_purchased: "10",
      },
    },
    10,
  );

  assert.deepEqual(result, {
    telegramUserId: "123456",
    purchaseType: "voice",
    creditsPurchased: 10,
    voiceSecondsToAdd: 600,
    invoiceCreditsToAdd: 0,
    action: "unlock_voice_credits",
    message: "Payment received. 10 voice minutes have been added to your account. You can keep invoicing by voice now.",
  });
});

test("builds invoice bundle fulfillment correctly", () => {
  const result = resolveCheckoutFulfillment(
    {
      metadata: {
        telegram_user_id: "123456",
        purchase_type: "invoice",
        credits_purchased: "20",
      },
    },
    10,
  );

  assert.deepEqual(result, {
    telegramUserId: "123456",
    purchaseType: "invoice",
    creditsPurchased: 20,
    voiceSecondsToAdd: 600,
    invoiceCreditsToAdd: 20,
    action: "unlock_invoice_credits",
    message: "Payment received. 20 invoice credits and 10 voice minutes have been added to your account. You can keep generating invoices now.",
  });
});
