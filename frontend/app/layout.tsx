import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { Instrument_Serif, Inter, JetBrains_Mono } from "next/font/google";
import SmoothScroll from "@/components/SmoothScroll";
import "./globals.css";

const display = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-display",
});
const ui = Inter({ subsets: ["latin"], variable: "--font-ui" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Bolo Khata — speak your khaata",
  description:
    "Voice ledger for Indian kiryana shops: speak an entry, receipts go out on Telegram with a UPI pay link.",
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icon.svg", apple: "/icon.svg" },
};

export const viewport: Viewport = {
  themeColor: "#0b0d0f",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${ui.variable} ${mono.variable}`}
    >
      <body className="font-ui min-h-screen grid-paper">
        <SmoothScroll>
          <header className="sticky top-0 z-50 border-b border-[var(--line)] bg-[rgba(11,13,15,0.92)]">
            <nav className="mx-auto flex max-w-4xl items-center gap-6 px-5 py-3">
              <Link href="/ledger" className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-[var(--accent)]">◉</span>
                <span className="font-display text-lg tracking-wide">Bolo Khata</span>
              </Link>
              <div className="flex flex-1 items-center justify-end gap-5 font-mono text-[11px] uppercase tracking-[0.16em] text-[var(--muted)]">
                <Link href="/ledger" className="transition-colors hover:text-[var(--ink)]">
                  Khata
                </Link>
                <Link href="/speak" className="transition-colors hover:text-[var(--ink)]">
                  Speak
                </Link>
                <Link href="/settings" className="transition-colors hover:text-[var(--ink)]">
                  Settings
                </Link>
              </div>
            </nav>
          </header>
          <main className="mx-auto max-w-4xl px-5 py-8">{children}</main>
        </SmoothScroll>
      </body>
    </html>
  );
}
