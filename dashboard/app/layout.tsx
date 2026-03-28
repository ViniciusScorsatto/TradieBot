import type { Metadata } from "next";
import { Sidebar } from "../components/sidebar";
import { Topbar } from "../components/topbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "InvoiceBot Admin",
  description: "Internal admin dashboard for InvoiceBot"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <Sidebar />
          <div className="workspace">
            <Topbar />
            <main className="main">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
