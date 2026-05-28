import Link from "next/link";
import { BriefcaseBusiness, FileText, LogOut } from "lucide-react";
import { logoutAction } from "@/app/actions";
import { ThemeToggle } from "@/components/theme/ThemeToggle";

type AppHeaderProps = {
  subtitle: string;
  active: "offers" | "applications";
  applicationsCount?: number;
};

export function AppHeader({ subtitle, active, applicationsCount = 0 }: AppHeaderProps) {
  const navItems = [
    { key: "offers" as const, href: "/dashboard", label: "Offres", icon: BriefcaseBusiness },
    { key: "applications" as const, href: "/candidatures", label: "Candidatures", icon: FileText, count: applicationsCount },
  ];

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 pt-[env(safe-area-inset-top)] shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-950/88">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-4 py-3">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-sm font-black text-white shadow-sm dark:bg-teal-500 dark:text-slate-950">
            AT
          </div>
          <div className="min-w-0">
            <p className="text-lg font-semibold leading-tight text-slate-950 dark:text-slate-50">AutoTache</p>
            <p className="truncate text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <nav className="hidden items-center gap-2 md:flex" aria-label="Navigation principale">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = active === item.key;

              return (
                <Link
                  key={item.key}
                  href={item.href}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex h-11 items-center gap-2 rounded-2xl px-3 text-sm font-semibold transition ${
                    isActive
                      ? "bg-slate-950 text-white dark:bg-teal-400 dark:text-slate-950"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                >
                  <Icon aria-hidden="true" className="h-4 w-4" />
                  {item.label}
                  {item.count && item.count > 0 ? (
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        isActive ? "bg-white/15 text-white dark:bg-slate-950/15 dark:text-slate-950" : "bg-teal-50 text-teal-700 dark:bg-teal-400/10 dark:text-teal-300"
                      }`}
                    >
                      {item.count}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </nav>
          <ThemeToggle />
          <form action={logoutAction}>
            <button
              type="submit"
              className="flex h-11 items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <LogOut aria-hidden="true" className="h-4 w-4" />
              <span className="hidden sm:inline">Se déconnecter</span>
            </button>
          </form>
        </div>
      </div>
    </header>
  );
}
