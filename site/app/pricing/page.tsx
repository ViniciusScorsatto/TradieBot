import { pricing } from "@invoicebot/shared";

export default function PricingPage() {
  return (
    <main className="container section">
      <div className="sectionHead">
        <div>
          <h2>Pricing</h2>
          <p>Keep the buying decision easy: generous free usage, then tiny step-up pricing for heavier users.</p>
        </div>
      </div>
      <div className="pricingLayout">
        <article className="priceCard">
          <h3>Free every month</h3>
          <div className="priceValue">{pricing.freeInvoicesPerMonth}</div>
          <p>
            Every tradie gets {pricing.freeInvoicesPerMonth} invoices per month plus{" "}
            {pricing.freeVoiceTranscriptionsPerMonth} free voice transcriptions up to {pricing.voiceNoteMaxSeconds} seconds each
            before any payment is required.
          </p>
        </article>
        <article className="priceCard">
          <h3>Extra usage</h3>
          <div className="priceValue">NZD ${pricing.paidBlockPriceNzd}</div>
          <p>
            Unlock another {pricing.paidBlockSize} invoices whenever you hit the monthly limit.
            Voice is positioned as a premium-metered feature after the free allowance.
          </p>
        </article>
      </div>
    </main>
  );
}
