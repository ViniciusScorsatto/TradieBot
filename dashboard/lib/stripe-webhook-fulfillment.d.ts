type CheckoutSessionLike = {
  id: string;
  customer?: unknown;
  payment_intent?: unknown;
  amount_total?: number | null;
  client_reference_id?: string | null;
  metadata?: {
    telegram_user_id?: string | null;
    purchase_type?: string | null;
    credits_purchased?: string | null;
  } | null;
};

type FulfillmentResult = {
  ok: boolean;
  action: string;
};

type PrismaLike = {
  user: {
    findFirst(args: unknown): Promise<{ id: string; stripeCustomerId?: string | null } | null>;
    update(args: unknown): Promise<unknown>;
    create(args: unknown): Promise<{ id: string }>;
  };
  payment: {
    findFirst(args: unknown): Promise<{ id: string } | null>;
    create(args: unknown): Promise<unknown>;
  };
};

export function fulfillCheckoutWithDatabase(
  session: CheckoutSessionLike,
  deps: {
    prisma: PrismaLike;
    sendTelegramMessage: (telegramUserId: string, message: string) => Promise<boolean>;
    randomUUID?: () => string;
    invoiceBundleVoiceMinutes?: number;
  },
): Promise<FulfillmentResult>;
