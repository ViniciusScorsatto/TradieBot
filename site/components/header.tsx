import Link from "next/link";

export function Header() {
  return (
    <header className="header">
      <div className="container">
        <div className="nav">
          <Link className="brandmark" href="/">
            InvoiceBot
          </Link>
          <div className="navlinks">
            <Link href="/pricing">Pricing</Link>
            <Link href="/faq">FAQ</Link>
            <Link href="/contact">Contact</Link>
          </div>
          <a
            className="cta"
            href={process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/your_bot"}
            target="_blank"
            rel="noreferrer"
          >
            Start on Telegram
          </a>
        </div>
      </div>
    </header>
  );
}
