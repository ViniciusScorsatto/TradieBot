export function getInvoiceBundleVoiceMinutes() {
  return Number(process.env.INVOICE_BUNDLE_VOICE_MINUTES ?? "10");
}

export function resolveCheckoutFulfillment(session, invoiceBundleVoiceMinutes = getInvoiceBundleVoiceMinutes()) {
  const telegramUserId = session.metadata?.telegram_user_id ?? session.client_reference_id;
  const purchaseType = session.metadata?.purchase_type ?? "invoice";
  const creditsPurchased = Number(session.metadata?.credits_purchased ?? "0");

  if (!telegramUserId || !creditsPurchased) {
    return null;
  }

  if (purchaseType === "voice") {
    return {
      telegramUserId: String(telegramUserId),
      purchaseType,
      creditsPurchased,
      voiceSecondsToAdd: creditsPurchased * 60,
      invoiceCreditsToAdd: 0,
      action: "unlock_voice_credits",
      message: `Payment received. ${creditsPurchased} voice minutes have been added to your account. You can keep invoicing by voice now.`
    };
  }

  return {
    telegramUserId: String(telegramUserId),
    purchaseType: "invoice",
    creditsPurchased,
    voiceSecondsToAdd: invoiceBundleVoiceMinutes * 60,
    invoiceCreditsToAdd: creditsPurchased,
    action: "unlock_invoice_credits",
    message: `Payment received. ${creditsPurchased} invoice credits and ${invoiceBundleVoiceMinutes} voice minutes have been added to your account. You can keep generating invoices now.`
  };
}
