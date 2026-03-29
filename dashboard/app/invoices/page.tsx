import { prisma } from "../../lib/prisma";

type InvoiceHistoryRow = {
  id: string;
  invoiceNumber: string;
  businessName: string;
  clientName: string;
  totalCents: number;
  emailedTo: string | null;
  emailedAt: string | null;
  createdAt: string;
};

function formatCurrency(cents: number) {
  return `NZD $${(Math.max(cents, 0) / 100).toFixed(2)}`;
}

async function loadInvoices(): Promise<InvoiceHistoryRow[]> {
  try {
    return await prisma.$queryRaw<InvoiceHistoryRow[]>`
      SELECT
        i.id,
        i.invoice_number AS "invoiceNumber",
        COALESCE(p.company_name, 'Unknown business') AS "businessName",
        COALESCE(c.name, 'No client') AS "clientName",
        i.total_cents AS "totalCents",
        i.emailed_to AS "emailedTo",
        CASE
          WHEN i.emailed_at IS NULL THEN NULL
          ELSE TO_CHAR(i.emailed_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI')
        END AS "emailedAt",
        TO_CHAR(i.created_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI') AS "createdAt"
      FROM invoices i
      JOIN users u ON u.id = i.user_id
      LEFT JOIN profiles p ON p.user_id = u.id
      LEFT JOIN clients c ON c.id = i.client_id
      ORDER BY i.created_at DESC
      LIMIT 100
    `;
  } catch {
    return [];
  }
}

export default async function InvoicesPage() {
  const invoices = await loadInvoices();

  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Invoice history</h2>
        <p>
          Review the latest generated invoices and see whether they were only created in Telegram or also emailed to the client.
        </p>
      </section>

      <section className="panel">
        <h3>Recent invoice activity</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Business</th>
              <th>Client</th>
              <th>Total</th>
              <th>Created</th>
              <th>Email status</th>
            </tr>
          </thead>
          <tbody>
            {invoices.length === 0 ? (
              <tr>
                <td colSpan={6}>No invoices found yet.</td>
              </tr>
            ) : invoices.map((invoice) => (
              <tr key={invoice.id}>
                <td>{invoice.invoiceNumber}</td>
                <td>{invoice.businessName}</td>
                <td>{invoice.clientName}</td>
                <td>{formatCurrency(invoice.totalCents)}</td>
                <td>{invoice.createdAt}</td>
                <td>
                  {invoice.emailedTo ? (
                    <span>
                      Sent to {invoice.emailedTo}
                      <br />
                      <span className="muted">{invoice.emailedAt}</span>
                    </span>
                  ) : (
                    <span className="muted">Generated only</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
