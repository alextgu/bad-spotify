import type { Metadata } from "next";
import { brand } from "@/lib/brand";
import "./globals.css";

// Reads from lib/brand.ts so renaming the project is one edit, not a hunt.
export const metadata: Metadata = {
  title: `${brand.name} — ${brand.tagline}`,
  description: brand.description,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
