type CheckoutSessionLike = {
  client_reference_id?: string | null;
  metadata?: {
    telegram_user_id?: string | null;
    purchase_type?: string | null;
    credits_purchased?: string | null;
  } | null;
};

type CheckoutFulfillment = {
  telegramUserId: string;
  purchaseType: "invoice" | "voice";
  creditsPurchased: number;
  voiceSecondsToAdd: number;
  invoiceCreditsToAdd: number;
  action: "unlock_invoice_credits" | "unlock_voice_credits";
  message: string;
};

export function getInvoiceBundleVoiceMinutes(): number;
export function resolveCheckoutFulfillment(
  session: CheckoutSessionLike,
  invoiceBundleVoiceMinutes?: number,
): CheckoutFulfillment | null;
