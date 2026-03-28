import type { Metadata } from "next";
import { ShellFrame } from "../components/shell-frame";
import "./globals.css";

export const metadata: Metadata = {
  title: "InvoiceBot Admin",
  description: "Internal admin dashboard for InvoiceBot"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ShellFrame>{children}</ShellFrame>
      </body>
    </html>
  );
}
