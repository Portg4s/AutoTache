import type { Metadata, Viewport } from "next";
import { ThemeProvider } from "@/components/theme/ThemeProvider";
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
    <html lang="fr" className="h-full antialiased" suppressHydrationWarning>
      <body className="min-h-full bg-[radial-gradient(circle_at_top,_#f8fafc_0,_#eef3f8_34rem)] text-slate-950 dark:bg-[radial-gradient(circle_at_top,_#172033_0,_#020617_34rem)] dark:text-slate-100">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
