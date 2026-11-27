"use client";

import {
  LayoutDashboard,
  Building2,
  Users,
  X,
} from "lucide-react";

import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";

type PlatformSidebarProps = {
  mobileOpen: boolean;
  onClose: () => void;
};

const navigationItems = [
  {
    href: "/platform",
    label: "dashboard",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    href: "/platform/tenants",
    label: "tenants",
    icon: Building2,
    exact: false,
  },
  {
    href: "/platform/users",
    label: "users",
    icon: Users,
    exact: false,
  },
] as const;

export function PlatformSidebar({
  mobileOpen,
  onClose,
}: PlatformSidebarProps) {
  const t = useTranslations("PlatformLayout");
  const pathname = usePathname();

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-50 flex w-64 flex-col
        border-r border-slate-200 bg-white
        transition-transform duration-200
        lg:static lg:translate-x-0
        ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
      `}
    >
      <div className="flex h-16 items-center justify-between border-b border-slate-200 px-5">
        <Link
          href="/platform"
          onClick={onClose}
          className="text-xl font-bold tracking-tight text-primary"
        >
          CaterFlow
        </Link>

        <button
          type="button"
          onClick={onClose}
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
          aria-label={t("closeMenu")}
        >
          <X className="size-5" />
        </button>
      </div>

      <div className="px-4 pb-2 pt-6">
        <p className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
          {t("administration")}
        </p>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {navigationItems.map((item) => {
          const Icon = item.icon;

          const isActive = item.exact
            ? pathname === item.href
            : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              aria-current={isActive ? "page" : undefined}
              className={`
                flex items-center gap-3 rounded-lg px-3 py-2.5
                text-sm font-medium transition-colors
                ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }
              `}
            >
              <Icon className="size-5 shrink-0" />
              {t(item.label)}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 p-4">
        <p className="text-xs text-slate-400">
          {t("platformVersion")}
        </p>
      </div>
    </aside>
  );
}