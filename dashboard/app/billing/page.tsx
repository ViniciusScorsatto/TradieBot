import { pricing } from "@invoicebot/shared";
import { loadRecentPayments } from "../../lib/reporting";

export default async function BillingPage() {
  const payments = await loadRecentPayments(20);
  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Billing</h2>
        <p>
          Monitor quota unlocks, recent payments, and where failed checkouts need follow-up.
          The product keeps the pricing simple: {pricing.freeInvoicesPerMonth} free invoices,
          then NZD ${pricing.paidBlockPriceNzd} for each extra block of {pricing.paidBlockSize}. Voice
          starts with {pricing.freeVoiceMinutesPerMonth} free voice minutes per month and should be
          treated as a premium-metered feature.
        </p>
      </section>

      <section className="panel">
        <h3>Stripe activity</h3>
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
            {payments.length === 0 ? (
              <tr>
                <td colSpan={5}>No Stripe activity recorded yet.</td>
              </tr>
            ) : payments.map((payment) => (
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
