import { dashboardCopy, overviewStats, payments, tickets, users } from "../lib/data";

export default function DashboardHome() {
  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Run the bot, billing, and support from one place.</h2>
        <p>
          This dashboard is the operational nerve center for InvoiceBot. It tracks the
          tradies currently using the Telegram bot, how close they are to the free limit,
          what template they chose, what they have paid, and who needs support.
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
            {dashboardCopy.pricing.paidBlockSize} for NZD ${dashboardCopy.pricing.paidBlockPriceNzd}.
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
          <h3>Recent ticket pressure</h3>
          <p>Bug and claim tickets should bubble to the top so no tradie gets stuck waiting.</p>
          <table className="table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Status</th>
                <th>User</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket, index) => (
                <tr key={`${ticket.user}-${index}`}>
                  <td><span className="badge">{ticket.type}</span></td>
                  <td>{ticket.status}</td>
                  <td>{ticket.user}</td>
                </tr>
              ))}
            </tbody>
          </table>
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
