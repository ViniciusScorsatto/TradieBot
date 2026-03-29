import { pricing, siteConfig } from "@invoicebot/shared";

function checkoutMessage(checkout?: string, type?: string) {
  const target = type === "voice" ? "voice minutes" : "invoice credits";
  if (checkout === "success") {
    return {
      tone: "success",
      body: `Payment received. Your ${target} should unlock shortly. Head back to Telegram and continue where you left off.`
    };
  }
  if (checkout === "cancelled") {
    return {
      tone: "warning",
      body: `Checkout was cancelled. You can keep going with the free workflow now and come back to unlock ${target} later.`
    };
  }
  return null;
}

export default function PricingPage({
  searchParams
}: {
  searchParams?: { checkout?: string; type?: string };
}) {
  const message = checkoutMessage(searchParams?.checkout, searchParams?.type);
  return (
    <main className="container section">
      <div className="sectionHead">
        <div>
          <h2>Pricing</h2>
          <p>Keep the buying decision easy: generous free usage, then tiny step-up pricing for heavier users.</p>
        </div>
      </div>
      {message ? (
        <section className={`siteNotice ${message.tone === "success" ? "siteNoticeSuccess" : "siteNoticeWarning"}`}>
          {message.body}
        </section>
      ) : null}
      <div className="pricingLayout">
        <article className="priceCard">
          <h3>Free every month</h3>
          <div className="priceValue">{pricing.freeInvoicesPerMonth}</div>
          <p>
            Every business gets {pricing.freeInvoicesPerMonth} invoices per month plus{" "}
            {pricing.freeVoiceMinutesPerMonth} free voice minutes up to {pricing.voiceNoteMaxSeconds} seconds per note
            before any payment is required.
          </p>
        </article>
        <article className="priceCard">
          <h3>Extra usage</h3>
          <div className="priceValue">NZD ${pricing.paidBlockPriceNzd}</div>
          <p>
            Unlock another {pricing.paidBlockSize} invoices whenever you hit the monthly limit.
            Voice is positioned as a premium-metered feature after the free allowance, sold in minute bundles.
          </p>
          <div className="pricingActions">
            <a className="cta" href={siteConfig.botDeepLink} target="_blank" rel="noreferrer">
              Buy {pricing.paidBlockSize} invoices in Telegram
            </a>
            <a className="secondary" href={siteConfig.botDeepLink} target="_blank" rel="noreferrer">
              Buy {pricing.paidVoiceMinutesBlock} voice minutes in Telegram
            </a>
          </div>
          <p className="pricingHint">
            Secure checkout opens from the Telegram bot so your credits can be applied to the right account.
          </p>
        </article>
      </div>
    </main>
  );
}
