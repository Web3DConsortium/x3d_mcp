import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";

export const metadata: Metadata = {
  title: "x3d_mcp Studio",
  description: "AI-native, standards-grounded 3D authoring for the open web.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        {children}
        <Script
          src="https://cdn.jsdelivr.net/npm/x_ite@latest/dist/x_ite.min.js"
          strategy="afterInteractive"
        />
      </body>
    </html>
  );
}
