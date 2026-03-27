import { invoiceTemplates, pricing } from "@invoicebot/shared";

export const overviewStats = [
  { label: "Active users", value: "124" },
  { label: "Invoices this month", value: "612" },
  { label: "MRR", value: "NZD $145" },
  { label: "Open tickets", value: "8" }
];

export const users = [
  {
    name: "Mike Jensen",
    handle: "@mikebuilds",
    plan: "Free",
    invoiceCount: 8,
    joinedAt: "2026-03-12",
    templateId: "trade-orange",
    stripeCustomerId: null
  },
  {
    name: "Sina Patel",
    handle: "@sinaplumbing",
    plan: "Paid",
    invoiceCount: 13,
    joinedAt: "2026-03-01",
    templateId: "classic-blue",
    stripeCustomerId: "cus_123456789"
  },
  {
    name: "Tama Rangi",
    handle: "@tamaelectric",
    plan: "Free",
    invoiceCount: 3,
    joinedAt: "2026-03-24",
    templateId: "forest-ledger",
    stripeCustomerId: null
  }
];

export const payments = [
  { name: "Sina Patel", amount: "NZD $5", credits: 10, status: "Succeeded", date: "2026-03-26" },
  { name: "Aroha Mason", amount: "NZD $5", credits: 10, status: "Pending", date: "2026-03-25" },
  { name: "Cam Hart", amount: "NZD $5", credits: 10, status: "Failed", date: "2026-03-24" }
];

export const tickets = [
  { type: "BUG", status: "OPEN", user: "Mike Jensen", body: "Totals looked wrong on GST line." },
  { type: "CLAIM", status: "IN_PROGRESS", user: "Sina Patel", body: "Need manual credits after duplicate charge." },
  { type: "IDEA", status: "OPEN", user: "Tama Rangi", body: "Would love recurring invoices next." }
];

export const dashboardCopy = {
  pricing,
  invoiceTemplates
};
