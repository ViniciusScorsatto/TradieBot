import Link from "next/link";

export function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footerRow">
          <p>
            InvoiceBot is built for small businesses and independent operators who want invoices out the door fast,
            without adding more admin.
          </p>
          <div className="footerLinks">
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <Link href="/contact">Contact</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
