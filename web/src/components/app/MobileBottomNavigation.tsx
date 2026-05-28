import Link from "next/link";
import { BriefcaseBusiness, FileText } from "lucide-react";

type NavigationItem = "offers" | "applications";

type MobileBottomNavigationProps = {
  active: NavigationItem;
  applicationsCount?: number;
};

export function MobileBottomNavigation({ active, applicationsCount = 0 }: MobileBottomNavigationProps) {
  const items = [
    {
      key: "offers" as const,
      href: "/dashboard",
      label: "Offres",
      icon: BriefcaseBusiness,
    },
    {
      key: "applications" as const,
      href: "/candidatures",
      label: "Candidatures",
      icon: FileText,
      count: applicationsCount,
    },
  ];

  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200/80 bg-white/95 px-4 pb-[calc(env(safe-area-inset-bottom)+0.5rem)] pt-2 shadow-[0_-10px_30px_rgba(15,23,42,0.08)] backdrop-blur dark:border-slate-800 dark:bg-slate-950/95 md:hidden">
      <div className="mx-auto grid max-w-md grid-cols-2 gap-2">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.key;

          return (
            <Link
              key={item.key}
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              className={`flex min-h-14 items-center justify-center gap-2 rounded-2xl px-3 text-sm font-semibold transition ${
                isActive
                  ? "bg-slate-950 text-white dark:bg-teal-400 dark:text-slate-950"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              }`}
            >
              <Icon aria-hidden="true" className="h-5 w-5" />
              <span>{item.label}</span>
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
      </div>
    </nav>
  );
}
