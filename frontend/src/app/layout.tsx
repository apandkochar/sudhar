import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sudhaar • Consent-first AI Agent (Nimbus Finance)",
  description: "Concept prototype for the Paytm Build for India AI Hackathon",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased font-sans bg-slate-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
