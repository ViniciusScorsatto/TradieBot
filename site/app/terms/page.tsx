export default function TermsPage() {
  return (
    <main className="container section">
      <div className="sectionHead">
        <div>
          <h2>Terms of Service</h2>
          <p>
            These terms outline the current product expectations for accessing and using InvoiceBot during the current release stage.
          </p>
        </div>
      </div>

      <div className="faqGrid">
        <article className="faqItem">
          <h3>Service scope</h3>
          <p>
            InvoiceBot is a Telegram-first invoicing tool for small businesses and independent operators. Features may evolve,
            change, or be withdrawn as the product develops.
          </p>
        </article>
        <article className="faqItem">
          <h3>User responsibility</h3>
          <p>
            Users remain responsible for checking invoice details, GST treatment, pricing, client details, and any legal or tax requirements
            before sending invoices to customers.
          </p>
        </article>
        <article className="faqItem">
          <h3>Billing and credits</h3>
          <p>
            Paid invoice or voice credits unlock additional usage capacity inside the product. Credits are product entitlements and may be
            adjusted for fraud, abuse, duplicate payments, refunds, or support corrections.
          </p>
        </article>
        <article className="faqItem">
          <h3>Availability</h3>
          <p>
            We aim to keep the service available and reliable, but do not guarantee uninterrupted access, bug-free operation, or error-free
            third-party integrations.
          </p>
        </article>
        <article className="faqItem">
          <h3>Acceptable use</h3>
          <p>
            Users must not use the service for unlawful activity, spam, fraud, or abusive automation. We may suspend access to protect the
            platform, other users, or service providers.
          </p>
        </article>
        <article className="faqItem">
          <h3>Contact</h3>
          <p>
            For support, billing issues, or legal requests, contact hello@invoicebot.nz or use the support flow inside the bot.
          </p>
        </article>
      </div>
    </main>
  );
}
