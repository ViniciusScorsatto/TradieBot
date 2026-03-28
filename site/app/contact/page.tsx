export default function ContactPage() {
  return (
    <main className="container section">
      <div className="sectionHead">
        <div>
          <h2>Contact</h2>
          <p>
            If you want a walkthrough, need support, want to talk about a rollout, or need help with a privacy request,
            this page is the fallback when Telegram is not the right first step.
          </p>
        </div>
      </div>
      <article className="sectionCard">
        <h3>Reach the team</h3>
        <p>Email: hello@invoicebot.nz</p>
        <p>Privacy: privacy@invoicebot.nz</p>
        <p>Telegram: `@invoicebot_support`</p>
        <p>Best for: support, feedback, privacy requests, and early access conversations.</p>
      </article>
    </main>
  );
}
