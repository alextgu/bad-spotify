import type { Metadata } from "next";
import { Instrument_Serif, JetBrains_Mono, Schibsted_Grotesk } from "next/font/google";
import { brand } from "@/lib/brand";
import "./globals.css";

/**
 * Three faces, each with one job, loaded through `next/font` so they are
 * self-hosted and there is no render-blocking request to Google on stage.
 *
 *   serif  every display line. Weight 400 only — there is no bold, which is
 *          the point: the size does the work and the page never shouts.
 *   sans   body, UI, anything that has to be read at length.
 *   mono   labels and timecodes. Small, wide-tracked, uppercase.
 */
const serif = Instrument_Serif({
  weight: "400",
  style: ["normal", "italic"],
  subsets: ["latin"],
  variable: "--font-serif",
  display: "swap",
});

const sans = Schibsted_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
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
    <html lang="en" className={`${serif.variable} ${sans.variable} ${mono.variable}`}>
      <body className="bg-paper font-sans text-ink antialiased">{children}</body>
    </html>
  );
}
