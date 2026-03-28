export default function PrivacyPage() {
  return (
    <main className="container section">
      <div className="sectionHead">
        <div>
          <h2>Privacy Policy</h2>
          <p>
            This page explains what InvoiceBot collects, why it is collected, and how people can ask for access,
            correction, or deletion of their information.
          </p>
        </div>
      </div>

      <div className="faqGrid">
        <article className="faqItem">
          <h3>What we collect</h3>
          <p>
            InvoiceBot may collect Telegram account identifiers, business profile details, saved client details,
            invoice content, generated invoice metadata, support requests, and payment-related account metadata.
          </p>
        </article>
        <article className="faqItem">
          <h3>Why we collect it</h3>
          <p>
            We use this information to provide the invoicing service, generate PDFs, email invoices when requested,
            support users, prevent abuse, and manage billing and account operations.
          </p>
        </article>
        <article className="faqItem">
          <h3>Who processes data for us</h3>
          <p>
            Depending on the feature being used, InvoiceBot may rely on hosting and infrastructure providers,
            payment providers, email delivery services, and AI transcription services to process personal data on our behalf.
          </p>
        </article>
        <article className="faqItem">
          <h3>Data requests</h3>
          <p>
            To request access, correction, or deletion of your data, contact the team at
            {" "}privacy@invoicebot.nz. We will use reasonable efforts to verify and respond to legitimate requests.
          </p>
        </article>
        <article className="faqItem">
          <h3>Retention</h3>
          <p>
            We retain service data only for as long as it is reasonably needed to operate the product, support users,
            comply with legal obligations, and maintain billing and security records.
          </p>
        </article>
        <article className="faqItem">
          <h3>International processing</h3>
          <p>
            Because InvoiceBot uses cloud-based service providers, personal data may be processed in countries outside
            your own. Where this happens, we rely on provider safeguards and contractual controls where available.
          </p>
        </article>
      </div>
    </main>
  );
}
