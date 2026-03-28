import Link from "next/link";
import { dashboardCopy, overviewStats, payments, users } from "../lib/data";
import { prisma } from "../lib/prisma";

type OverviewTicketRow = {
  id: string;
  type: "BUG" | "CLAIM" | "IMPROVEMENT" | "IDEA";
  status: "OPEN" | "IN_PROGRESS" | "CLOSED";
  userName: string;
  subject: string;
  updatedAt: string;
};

async function loadRecentTickets(): Promise<OverviewTicketRow[]> {
  try {
    return await prisma.$queryRaw<OverviewTicketRow[]>`
      SELECT
        t.id,
        t.type,
        t.status,
        COALESCE(NULLIF(TRIM(CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))), ''), COALESCE(p.company_name, 'Unknown business')) AS "userName",
        t.subject,
        TO_CHAR(t.updated_at AT TIME ZONE 'Pacific/Auckland', 'YYYY-MM-DD HH24:MI') AS "updatedAt"
      FROM tickets t
      JOIN users u ON u.id = t.user_id
      LEFT JOIN profiles p ON p.user_id = u.id
      ORDER BY
        CASE t.status
          WHEN 'OPEN' THEN 0
          WHEN 'IN_PROGRESS' THEN 1
          ELSE 2
        END,
        CASE t.type
          WHEN 'BUG' THEN 0
          WHEN 'CLAIM' THEN 1
          WHEN 'IMPROVEMENT' THEN 2
          ELSE 3
        END,
        t.updated_at DESC
      LIMIT 4
    `;
  } catch {
    return [];
  }
}

function statusTone(status: OverviewTicketRow["status"]) {
  if (status === "OPEN") {
    return "badge status-open";
  }
  if (status === "IN_PROGRESS") {
    return "badge status-progress";
  }
  return "badge status-closed";
}

function typeTone(type: OverviewTicketRow["type"]) {
  if (type === "BUG") {
    return "badge ticket-bug";
  }
  if (type === "CLAIM") {
    return "badge ticket-claim";
  }
  if (type === "IMPROVEMENT") {
    return "badge ticket-improvement";
  }
  return "badge ticket-idea";
}

export default async function DashboardHome() {
  const recentTickets = await loadRecentTickets();

  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Run the bot, billing, and support from one place.</h2>
        <p>
          This dashboard is the operational nerve center for InvoiceBot. It tracks the
          businesses currently using the Telegram bot, how close they are to the free limit,
          what template they chose, what they have paid, how voice usage should be controlled,
          and who needs support.
        </p>
      </section>

      <section className="grid metrics">
        {overviewStats.map((stat) => (
          <article key={stat.label} className="metric">
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
          </article>
        ))}
      </section>

      <section className="two-col">
        <article className="panel">
          <h3>Launch shape</h3>
          <p>
            Free plan includes {dashboardCopy.pricing.freeInvoicesPerMonth} invoices per month.
            Warn at {dashboardCopy.pricing.warningThreshold}, then sell another block of{" "}
            {dashboardCopy.pricing.paidBlockSize} for NZD ${dashboardCopy.pricing.paidBlockPriceNzd}. Voice starts with{" "}
            {dashboardCopy.pricing.freeVoiceTranscriptionsPerMonth} free transcriptions and should later be monetized separately.
          </p>
          <table className="table">
            <thead>
              <tr>
                <th>User</th>
                <th>Plan</th>
                <th>Invoices</th>
                <th>Template</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.handle}>
                  <td>{user.name}</td>
                  <td>{user.plan}</td>
                  <td>{user.invoiceCount}</td>
                  <td>{user.templateId}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="panel">
          <div className="ticket-panel-head">
            <div>
              <h3>Recent ticket pressure</h3>
              <p>Bug and claim tickets should bubble to the top so no business gets stuck waiting.</p>
            </div>
            <Link href="/tickets" className="button small-button ticket-link-button">
              Open ticket desk
            </Link>
          </div>

          {recentTickets.length === 0 ? (
            <div className="ticket-overview-empty">
              <p className="muted">No support tickets yet. Once customers use `/support`, the live queue will show up here.</p>
            </div>
          ) : (
            <div className="ticket-overview-list">
              {recentTickets.map((ticket) => (
                <Link
                  key={ticket.id}
                  href={`/tickets?ticket=${ticket.id}`}
                  className="ticket-overview-item"
                >
                  <div className="ticket-overview-top">
                    <div className="row-actions">
                      <span className={typeTone(ticket.type)}>{ticket.type.toLowerCase()}</span>
                      <span className={statusTone(ticket.status)}>
                        {ticket.status.replace("_", " ").toLowerCase()}
                      </span>
                    </div>
                    <span className="muted">{ticket.updatedAt}</span>
                  </div>
                  <strong>{ticket.subject}</strong>
                  <p>{ticket.userName}</p>
                </Link>
              ))}
            </div>
          )}
        </article>
      </section>

      <section className="panel">
        <h3>Recent payments</h3>
        <p>Stripe credits are used to extend invoice quota without turning this into a full SaaS portal.</p>
        <table className="table">
          <thead>
            <tr>
              <th>User</th>
              <th>Amount</th>
              <th>Credits</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {payments.map((payment) => (
              <tr key={`${payment.name}-${payment.date}`}>
                <td>{payment.name}</td>
                <td>{payment.amount}</td>
                <td>{payment.credits}</td>
                <td>{payment.status}</td>
                <td>{payment.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
