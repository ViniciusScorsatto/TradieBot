export type InvoiceTemplate = {
  id: string;
  name: string;
  accent: string;
  background: string;
  description: string;
};

export const invoiceTemplates: InvoiceTemplate[] = [
  {
    id: "classic-blue",
    name: "Classic Blue",
    accent: "#185adb",
    background: "#eef4ff",
    description: "Clean corporate layout with a bold blue header."
  },
  {
    id: "trade-orange",
    name: "Trade Orange",
    accent: "#e8630a",
    background: "#fff2e9",
    description: "High-energy layout for hands-on service businesses."
  },
  {
    id: "forest-ledger",
    name: "Forest Ledger",
    accent: "#256d1b",
    background: "#eef8ee",
    description: "Calm, trustworthy design with strong totals hierarchy."
  },
  {
    id: "graphite-pro",
    name: "Graphite Pro",
    accent: "#2c3639",
    background: "#f3f4f6",
    description: "Dark neutral look for premium trades and contractors."
  },
  {
    id: "sunset-statement",
    name: "Sunset Statement",
    accent: "#c44900",
    background: "#fff4eb",
    description: "Warm, modern template with a more creative feel."
  }
];

export const pricing = {
  freeInvoicesPerMonth: 10,
  warningThreshold: 8,
  paidBlockSize: 10,
  paidBlockPriceNzd: 5
};

export const siteConfig = {
  brandName: "InvoiceBot",
  botDeepLink: process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/your_bot"
};
