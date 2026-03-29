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
    body: `Yes, with guardrails. Voice starts with ${pricing.freeVoiceMinutesPerMonth} free minutes per month. Paid invoice bundles include ${pricing.invoiceBundleVoiceMinutes} extra voice minutes, and there is also a separate voice add-on.`
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
        <div className="heroCopy">
          <span className="eyebrow">Telegram-first invoicing for New Zealand small businesses</span>
          <h1>Turn chats, voice notes, and job details into invoices that look ready to send.</h1>
          <p>
            InvoiceBot lives where your work already happens. Capture what got done in Telegram,
            review the totals, and send a polished invoice PDF without jumping between apps.
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
          <div className="heroStats">
            <div className="heroStat">
              <strong>Voice + text</strong>
              <span>Capture invoices the way people actually work</span>
            </div>
            <div className="heroStat">
              <strong>NZ GST ready</strong>
              <span>Handles GST cleanly when your business profile needs it</span>
            </div>
            <div className="heroStat">
              <strong>PDF + email</strong>
              <span>Send the invoice in chat or email it to the client</span>
            </div>
          </div>
        </div>
        <aside className="heroVisual">
          <div className="heroGlow heroGlowOne" />
          <div className="heroGlow heroGlowTwo" />
          <div className="dashboardMock">
            <div className="dashboardChrome">
              <span />
              <span />
              <span />
            </div>
            <div className="dashboardBody">
              <div className="dashboardKpis">
                <div className="kpiCard">
                  <span>Invoices sent</span>
                  <strong>146</strong>
                </div>
                <div className="kpiCard">
                  <span>Paid faster</span>
                  <strong>+27%</strong>
                </div>
                <div className="kpiCard">
                  <span>Voice used</span>
                  <strong>84 min</strong>
                </div>
              </div>
              <div className="dashboardChart">
                <div className="chartLine" />
              </div>
              <div className="dashboardRows">
                <div className="dashboardRow">
                  <span>Client</span>
                  <span>Ready</span>
                </div>
                <div className="dashboardRow">
                  <span>Invoice</span>
                  <span>Sent</span>
                </div>
                <div className="dashboardRow">
                  <span>Email</span>
                  <span>Delivered</span>
                </div>
              </div>
            </div>
          </div>
          <div className="phoneMock">
            <div className="phoneTop" />
            <div className="phoneScreen">
              <div className="chatBubble inbound">
                Garden tidy x 2 at $95
                <br />
                Green waste removal $48
              </div>
              <div className="chatBubble outbound">Invoice draft ready. Total: NZD 264.50</div>
              <div className="chatBubble inbound compact">Send PDF</div>
              <div className="chatBubble outbound compact">Email to client</div>
            </div>
          </div>
          <div className="floatingBadge badgeTop">Telegram workflow</div>
          <div className="floatingBadge badgeBottom">PDF + email in one flow</div>
        </aside>
      </section>

      <section className="section">
        <div className="sectionHead">
          <div>
            <h2>Why teams move to this flow</h2>
            <p>
              The pitch is simple: less admin drag, faster payment, and invoices that still look like they came from a real back-office system.
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
              Every business gets access to all five layouts. Pick one once, save it to the profile, and keep the brand consistent every time.
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
              Start free every month. Voice includes {pricing.freeVoiceMinutesPerMonth} free minutes,
              then unlock another {pricing.paidBlockSize} invoices plus {pricing.invoiceBundleVoiceMinutes} voice minutes for NZD ${pricing.paidBlockPriceNzd}.
            </p>
          </article>
          <article className="priceCard">
            <h3>Built for real operations</h3>
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
