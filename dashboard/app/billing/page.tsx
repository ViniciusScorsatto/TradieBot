import { pricing } from "@invoicebot/shared";
import { payments } from "../../lib/data";

export default function BillingPage() {
  return (
    <div className="stack">
      <section className="hero-card">
        <h2>Billing</h2>
        <p>
          Monitor quota unlocks, recent payments, and where failed checkouts need follow-up.
          The product keeps the pricing simple: {pricing.freeInvoicesPerMonth} free invoices,
          then NZD ${pricing.paidBlockPriceNzd} for each extra block of {pricing.paidBlockSize}. Voice
          starts with {pricing.freeVoiceTranscriptionsPerMonth} free transcriptions per month and should be
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
