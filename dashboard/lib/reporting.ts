import { pricing } from "@invoicebot/shared";
import { prisma } from "./prisma";

export type OverviewStat = {
  label: string;
  value: string;
};

export type OverviewUserRow = {
  id: string;
  name: string;
  plan: string;
  invoiceCount: number;
  templateId: string;
};

export type PaymentRow = {
  id: string;
  name: string;
  amount: string;
  credits: string;
  status: string;
  date: string;
};

function formatCurrency(cents: number) {
  return `NZD $${(Math.max(cents, 0) / 100).toFixed(2)}`;
}

function formatPurchaseCredits(purchaseType: string, creditsPurchased: number) {
  if (purchaseType === "voice") {
    return `${creditsPurchased} min`;
  }
  return `${creditsPurchased} invoices + ${pricing.invoiceBundleVoiceMinutes} min`;
}

export async function loadOverviewStats(): Promise<OverviewStat[]> {
  try {
    const [row] = await prisma.$queryRaw<
      {
        activeUsers: number;
        invoicesThisMonth: number;
        revenueThisMonthCents: number;
        openTickets: number;
      }[]
    >`
      WITH month_window AS (
        SELECT DATE_TRUNC('month', timezone('Pacific/Auckland', NOW())) AS month_start
      )
      SELECT
        (SELECT COUNT(*)::int FROM users) AS "activeUsers",
        (
          SELECT COUNT(*)::int
          FROM invoices i, month_window mw
          WHERE timezone('Pacific/Auckland', i.created_at) >= mw.month_start
        ) AS "invoicesThisMonth",
        (
          SELECT COALESCE(SUM(amount_cents), 0)::int
          FROM payments p, month_window mw
          WHERE p.status = 'SUCCEEDED'
            AND timezone('Pacific/Auckland', p.created_at) >= mw.month_start
        ) AS "revenueThisMonthCents",
        (
          SELECT COUNT(*)::int
          FROM tickets
          WHERE status <> 'CLOSED'
        ) AS "openTickets"
    `;

    return [
      { label: "Active users", value: String(row?.activeUsers ?? 0) },
      { label: "Invoices this month", value: String(row?.invoicesThisMonth ?? 0) },
      { label: "Revenue this month", value: formatCurrency(row?.revenueThisMonthCents ?? 0) },
      { label: "Open tickets", value: String(row?.openTickets ?? 0) },
    ];
  } catch {
    return [
      { label: "Active users", value: "0" },
      { label: "Invoices this month", value: "0" },
      { label: "Revenue this month", value: "NZD $0.00" },
      { label: "Open tickets", value: "0" },
    ];
  }
}

export async function loadOverviewUsers(): Promise<OverviewUserRow[]> {
  try {
    return await prisma.$queryRaw<OverviewUserRow[]>`
      SELECT
        u.id,
        COALESCE(
          NULLIF(TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))), ''),
          COALESCE(p.company_name, 'Unknown business')
        ) AS name,
        u.plan_tier AS plan,
        u.invoice_count_this_month AS "invoiceCount",
        COALESCE(p.default_template_id, 'classic-blue') AS "templateId"
      FROM users u
      LEFT JOIN profiles p ON p.user_id = u.id
      ORDER BY u.joined_at DESC
      LIMIT 5
    `;
  } catch {
    return [];
  }
}

export async function loadRecentPayments(limit = 10): Promise<PaymentRow[]> {
  try {
    const rows = await prisma.$queryRaw<
      {
        id: string;
        name: string;
        amountCents: number;
        creditsPurchased: number;
        purchaseType: string;
        status: string;
        date: string;
      }[]
    >`
      SELECT
        p.id,
        COALESCE(
          NULLIF(TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))), ''),
          COALESCE(pr.company_name, 'Unknown business')
        ) AS name,
        p.amount_cents AS "amountCents",
        p.credits_purchased AS "creditsPurchased",
        p.purchase_type AS "purchaseType",
        p.status,
        TO_CHAR(p.created_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI') AS date
      FROM payments p
      JOIN users u ON u.id = p.user_id
      LEFT JOIN profiles pr ON pr.user_id = u.id
      ORDER BY p.created_at DESC
      LIMIT ${limit}
    `;

    return rows.map((row) => ({
      id: row.id,
      name: row.name,
      amount: formatCurrency(row.amountCents),
      credits: formatPurchaseCredits(row.purchaseType, row.creditsPurchased),
      status: row.status,
      date: row.date,
    }));
  } catch {
    return [];
  }
}
