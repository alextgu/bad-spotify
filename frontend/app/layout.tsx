import type { Metadata } from "next";
import { Figtree, JetBrains_Mono } from "next/font/google";
import { brand } from "@/lib/brand";
import "./globals.css";

/**
 * Two faces.
 *
 *   display/sans  Figtree, for everything that is read. Spotify sets its
 *                 entire product in Circular, which is proprietary; Figtree is
 *                 the closest thing on Google Fonts — the same geometric
 *                 grotesk skeleton, near-circular bowls, a single-storey `g`.
 *                 One family across display and body, as they do, because two
 *                 competing grotesks on one page is a tell.
 *   mono          JetBrains Mono, for labels and timecodes only.
 *
 * This replaced Instrument Serif, which was elegant and wrong: a calligraphic
 * italic on the hero read as a wine label rather than as software.
 */
const display = Figtree({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const mono = JetBrains_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: `${brand.name} — ${brand.tagline}`,
  description: brand.description,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${display.variable} ${mono.variable}`}>
      <body className="bg-paper font-sans text-ink antialiased">{children}</body>
    </html>
  );
}
