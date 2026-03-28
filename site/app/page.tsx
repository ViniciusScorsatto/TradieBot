import { invoiceTemplates, pricing } from "@invoicebot/shared";

const features = [
  {
    title: "Speak the invoice",
    body: "Send a voice note or typed job details in Telegram and let InvoiceBot turn them into line items, with voice protected by fair-use limits."
  },
  {
    title: "Choose a template once",
    body: "Pick from five polished invoice templates and keep that style saved to your profile."
  },
  {
    title: "Send a branded PDF back fast",
    body: "Review totals, confirm, and get a clean invoice PDF back in chat in minutes."
  }
];

const faqs = [
  {
    title: "Do I need to create an account?",
    body: "No. The customer experience starts in Telegram. Admin login and 2FA are only for the internal operations dashboard."
  },
  {
    title: "Do I get free invoices?",
    body: `Yes. You get ${pricing.freeInvoicesPerMonth} free invoices each month, then NZD $${pricing.paidBlockPriceNzd} for every extra block of ${pricing.paidBlockSize}.`
  },
  {
    title: "Is voice invoicing included?",
    body: `Yes, with guardrails. Voice starts with ${pricing.freeVoiceTranscriptionsPerMonth} free transcriptions per month, then becomes a premium-metered feature.`
  },
  {
    title: "Can I save clients and business details?",
    body: "Yes. InvoiceBot stores your business profile, saved clients, and default template so repeat invoices stay fast."
  },
  {
    title: "Can I upload my own template?",
    body: "Not in v1. The first release focuses on five curated templates that already look professional and work reliably."
  }
];

export default function HomePage() {
  return (
    <main className="container">
      <section className="hero">
        <div>
          <span className="eyebrow">Built for New Zealand small businesses and independent operators</span>
          <h1>Turn work notes into polished invoices straight from Telegram.</h1>
          <p>
            InvoiceBot helps you speak or type what got done, review the totals, and send
            a branded invoice PDF without waiting to get back to the office.
          </p>
          <div className="heroActions">
            <a
              className="cta"
              href={process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/your_bot"}
              target="_blank"
              rel="noreferrer"
            >
              Start on Telegram
            </a>
            <a className="secondary" href="/pricing">See pricing</a>
          </div>
        </div>
        <aside className="heroCard">
          <div className="heroFlow">
            <div className="flowStep">
              <strong>1. Send job details</strong>
              <p>“Garden tidy x 2 at $95, green waste removal $48, callout $120.”</p>
            </div>
            <div className="flowStep">
              <strong>2. Review and confirm</strong>
              <p>InvoiceBot shows the itemised list, GST, and total before it generates anything.</p>
            </div>
            <div className="flowStep">
              <strong>3. Get the PDF back in chat</strong>
              <p>Your business details, saved client, and default invoice template are applied automatically.</p>
            </div>
          </div>
        </aside>
      </section>

      <section className="section">
        <div className="sectionHead">
          <div>
            <h2>Why small businesses buy it</h2>
            <p>
              The pitch is simple: less admin drag, faster payment, and invoices that still look like they came from a proper system.
            </p>
          </div>
        </div>
        <div className="featureGrid">
          {features.map((feature) => (
            <article key={feature.title} className="sectionCard">
              <h3>{feature.title}</h3>
              <p>{feature.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="sectionHead">
          <div>
            <h2>Five templates, zero design stress</h2>
            <p>
              Every customer gets access to all five layouts. They pick one once, save it to their profile, and reuse it on every invoice.
            </p>
          </div>
        </div>
        <div className="templateGrid">
          {invoiceTemplates.map((template) => (
            <article key={template.id} className="templateCard">
              <div
                className="templateSwatch"
                style={{
                  background: `linear-gradient(135deg, ${template.accent} 0%, ${template.background} 100%)`
                }}
              />
              <h3>{template.name}</h3>
              <p>{template.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="pricingLayout">
          <article className="priceCard">
            <h3>Simple pricing</h3>
            <div className="priceValue">10 free</div>
            <p>
              Start free every month. Voice also includes {pricing.freeVoiceTranscriptionsPerMonth} free transcriptions,
              then unlock another {pricing.paidBlockSize} invoices for NZD ${pricing.paidBlockPriceNzd}.
            </p>
          </article>
          <article className="priceCard">
            <h3>What you get</h3>
            <p>
              Voice or text invoice capture, saved clients, default template selection, branded PDF output,
              and support through Telegram, with premium voice capacity as usage grows.
            </p>
            <div className="heroActions">
              <a
                className="cta"
                href={process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/your_bot"}
                target="_blank"
                rel="noreferrer"
              >
                Start on Telegram
              </a>
            </div>
          </article>
        </div>
      </section>

      <section className="section">
        <div className="sectionHead">
          <div>
            <h2>Questions businesses ask before they try it</h2>
          </div>
        </div>
        <div className="faqGrid">
          {faqs.map((faq) => (
            <article key={faq.title} className="faqItem">
              <h3>{faq.title}</h3>
              <p>{faq.body}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
