import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoTache",
  description: "Suivi personnel de recherche d'emploi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="h-full antialiased">
      <body className="min-h-full bg-slate-100 text-slate-950">{children}</body>
    </html>
  );
}
