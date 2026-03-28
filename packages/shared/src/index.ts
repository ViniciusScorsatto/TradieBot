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
    description: "Dark neutral look for premium service businesses and contractors."
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
  paidBlockSize: 20,
  paidBlockPriceNzd: 5,
  freeVoiceTranscriptionsPerMonth: 20,
  voiceNoteMaxSeconds: 60
};

export type PromotionCategory = {
  id: string;
  label: string;
  description: string;
};

export const promotionCategories: PromotionCategory[] = [
  { id: "tools", label: "Tools", description: "Hardware, gear, and business equipment offers." },
  { id: "vehicles", label: "Vehicles", description: "Utes, vans, leasing, and vehicle upkeep deals." },
  { id: "fuel", label: "Fuel", description: "Fuel cards, discounts, and running-cost promotions." },
  { id: "insurance", label: "Insurance", description: "Business, vehicle, and liability cover offers." },
  { id: "accounting", label: "Accounting", description: "Bookkeeping, tax, and accounting service offers." },
  { id: "software", label: "Software", description: "Apps, tools, and workflow software promotions." }
];

export const siteConfig = {
  brandName: "InvoiceBot",
  botDeepLink: process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/your_bot"
};
