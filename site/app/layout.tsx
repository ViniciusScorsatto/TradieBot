import type { Metadata } from "next";
import { Footer } from "../components/footer";
import { Header } from "../components/header";
import "./globals.css";

export const metadata: Metadata = {
  title: "InvoiceBot",
  description: "Voice-to-invoice in Telegram for New Zealand small businesses and independent operators"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="page">
          <Header />
          {children}
          <Footer />
        </div>
      </body>
    </html>
  );
}
