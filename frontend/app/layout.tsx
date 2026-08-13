import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "bad spotify",
  description:
    "A wearable agent whose only feature is playing the worst possible music for the moment.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="grid-bg font-sans antialiased">
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
