import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "AutoTache",
    template: "%s | AutoTache",
  },
  applicationName: "AutoTache",
  description: "Suivi personnel de recherche d'emploi et de candidatures.",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    title: "AutoTache",
    statusBarStyle: "default",
  },
};

export const viewport: Viewport = {
  themeColor: "#0f172a",
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
