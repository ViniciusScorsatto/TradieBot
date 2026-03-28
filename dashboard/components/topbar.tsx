"use client";

import { usePathname } from "next/navigation";
import { signOutAction } from "../app/auth-actions";

const titles: Record<string, { title: string; subtitle: string }> = {
  "/": { title: "Dashboard", subtitle: "Operations snapshot across billing, support, and usage." },
  "/users": { title: "Users", subtitle: "Manage customers, credits, and quota resets." },
  "/billing": { title: "Billing", subtitle: "Track Stripe activity and purchased credit blocks." },
  "/promotions": { title: "Promotions", subtitle: "Send affiliate campaigns to opted-in audiences." },
  "/tickets": { title: "Tickets", subtitle: "Handle bugs, claims, and support conversations." },
  "/login": { title: "Admin Login", subtitle: "Access control for the internal operations console." }
};

export function Topbar() {
  const pathname = usePathname();
  const content = titles[pathname] ?? titles["/"];
  const showAuthActions = pathname !== "/login";

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
        {showAuthActions ? (
          <form action={signOutAction}>
            <button className="topbarSignout" type="submit">
              Sign out
            </button>
          </form>
        ) : null}
        <div className="topbarAvatar">IB</div>
      </div>
    </header>
  );
}
