export default function FaqPage() {
  const questions = [
    ["How does it work?", "You start in Telegram, send voice or text job details, confirm the totals, and receive the invoice PDF back in chat."],
    ["Can I store my clients?", "Yes. Saved clients and business details make repeat invoices much faster."],
    ["Do I choose a template?", "Yes. Pick from five curated templates and keep one as your default."],
    ["Is voice unlimited?", "No. Voice includes 20 free transcriptions per month, capped at 60 seconds each, and is intended to become a premium-metered feature so the product stays sustainable."],
    ["Is there customer login?", "No customer portal in v1. The product experience is Telegram-first."],
    ["What if I need support?", "Use the support flow inside the bot or contact the team through the website contact page."]
  ];

  return (
    <main className="container section">
      <div className="sectionHead">
        <div>
          <h2>FAQ</h2>
          <p>The first release keeps the product tight: Telegram in, invoice out, simple pricing, and quick support.</p>
        </div>
      </div>
      <div className="faqGrid">
        {questions.map(([title, body]) => (
          <article key={title} className="faqItem">
            <h3>{title}</h3>
            <p>{body}</p>
          </article>
        ))}
      </div>
    </main>
  );
}
