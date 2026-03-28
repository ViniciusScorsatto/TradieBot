"use client";

import { usePathname } from "next/navigation";

const titles: Record<string, { title: string; subtitle: string }> = {
  "/": { title: "Dashboard", subtitle: "Operations snapshot across billing, support, and usage." },
  "/users": { title: "Users", subtitle: "Manage customers, credits, and quota resets." },
  "/billing": { title: "Billing", subtitle: "Track Stripe activity and purchased credit blocks." },
  "/tickets": { title: "Tickets", subtitle: "Handle bugs, claims, and support conversations." },
  "/login": { title: "Admin Login", subtitle: "Access control for the internal operations console." }
};

export function Topbar() {
  const pathname = usePathname();
  const content = titles[pathname] ?? titles["/"];

  return (
    <header className="topbar">
      <div>
        <span className="topbarEyebrow">InvoiceBot Admin</span>
        <h1>{content.title}</h1>
        <p>{content.subtitle}</p>
      </div>
      <div className="topbarMeta">
        <div className="topbarChip">
          <span className="statusDot" />
          Production-ready shell
        </div>
        <div className="topbarAvatar">IB</div>
      </div>
    </header>
  );
}
