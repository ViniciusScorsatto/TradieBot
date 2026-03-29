"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Overview" },
  { href: "/users", label: "Users" },
  { href: "/invoices", label: "Invoices" },
  { href: "/billing", label: "Billing" },
  { href: "/promotions", label: "Promotions" },
  { href: "/tickets", label: "Tickets" },
  { href: "/login", label: "Admin Login" }
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebarProfile">
        <div className="sidebarAvatar">IB</div>
        <div>
          <strong>Ops Console</strong>
          <p>Billing, support, and customer controls</p>
        </div>
      </div>
      <div className="brand">
        <span className="brandKicker">Control room</span>
        <h1>InvoiceBot</h1>
        <p>Run the product from one internal dashboard.</p>
      </div>
      <nav className="nav">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={pathname === link.href ? "active" : ""}
          >
            <span className="navBullet" />
            {link.label}
          </Link>
        ))}
      </nav>
      <div className="sidebarFootnote">
        Keep product ops tight: usage, credits, payments, and support all live here.
      </div>
    </aside>
  );
}
