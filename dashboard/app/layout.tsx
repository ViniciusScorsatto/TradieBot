import type { Metadata } from "next";
import { ShellFrame } from "../components/shell-frame";
import "./globals.css";

export const metadata: Metadata = {
  title: "InvoiceBot Admin",
  description: "Internal admin dashboard for InvoiceBot"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const promotionsEnabled =
    (process.env.ENABLE_PROMOTIONS ?? "false").trim().toLowerCase() === "true" ||
    (process.env.ENABLE_PROMOTIONS ?? "").trim() === "1";

  return (
    <html lang="en">
      <body>
        <ShellFrame promotionsEnabled={promotionsEnabled}>{children}</ShellFrame>
      </body>
    </html>
  );
}
