"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Overview" },
  { href: "/users", label: "Users" },
  { href: "/billing", label: "Billing" },
  { href: "/tickets", label: "Tickets" },
  { href: "/login", label: "Admin Login" }
] as const;

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="brand">
        <h1>InvoiceBot Admin</h1>
        <p>Operate the Telegram product from one Railway-hosted console.</p>
      </div>
      <nav className="nav">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={pathname === link.href ? "active" : ""}
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
