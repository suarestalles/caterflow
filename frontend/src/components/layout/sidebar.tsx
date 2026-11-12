
"use client";

import {
  CalendarDays,
  ClipboardList,
  LayoutDashboard,
  Settings,
  Users,
  Utensils,
  Wallet,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";

const navigation = [
  { label: "dashboard", href: "/" as const, icon: LayoutDashboard },
  { label: "events", href: "/events" as const, icon: CalendarDays },
  { label: "quotes", href: "/quotes" as const, icon: ClipboardList },
  { label: "clients", href: "/clients" as const, icon: Users },
  { label: "menus", href: "/menus" as const, icon: Utensils },
  { label: "finances", href: "/finances" as const, icon: Wallet },
];

type SidebarProps = {
  onNavigate?: () => void;
};

export function Sidebar({ onNavigate }: SidebarProps) {
  const t = useTranslations("Navigation");
  const pathname = usePathname();

  return (
    <aside className="flex min-h-screen w-64 shrink-0 flex-col border-r border-border bg-white">
      <div className="flex h-20 items-center gap-3 border-b border-border px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <Utensils size={22} />
        </div>
        <span className="text-xl font-bold tracking-tight">CaterFlow</span>
      </div>

      <nav className="flex-1 space-y-1 px-4 py-6">
        <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {t("workspace")}
        </p>

        {navigation.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Icon size={19} />
              {t(item.label)}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4">
        <Link
          href="/settings"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <Settings size={19} />
          {t("settings")}
        </Link>
      </div>
    </aside>
  );
}
