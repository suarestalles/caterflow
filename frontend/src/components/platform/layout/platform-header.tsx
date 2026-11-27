"use client";

import { LogOut, Menu, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useTranslations } from "next-intl";

import { useAuth } from "@/providers/auth-provider";
import { useRouter } from "@/i18n/navigation";

type PlatformHeaderProps = {
  onMenuClick: () => void;
};

export function PlatformHeader({
  onMenuClick,
}: PlatformHeaderProps) {
  const t = useTranslations("PlatformLayout");
  const { session, logout } = useAuth();
  const router = useRouter();

  const [isLoggingOut, setIsLoggingOut] = useState(false);

  async function handleLogout() {
    if (isLoggingOut) return;

    setIsLoggingOut(true);

    try {
      await logout();
      router.replace("/platform/login");
    } finally {
      setIsLoggingOut(false);
    }
  }

  const userName = session?.user.full_name ?? "";
  const userEmail = session?.user.email ?? "";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenuClick}
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
          aria-label={t("openMenu")}
        >
          <Menu className="size-5" />
        </button>

        <div className="flex items-center gap-2">
          <ShieldCheck className="size-5 text-primary" />

          <div>
            <p className="text-sm font-semibold text-slate-900">
              {t("adminPanel")}
            </p>
            <p className="hidden text-xs text-slate-500 sm:block">
              {t("platformDescription")}
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium text-slate-800">
            {userName}
          </p>
          <p className="text-xs text-slate-500">
            {userEmail}
          </p>
        </div>

        <button
          type="button"
          onClick={() => void handleLogout()}
          disabled={isLoggingOut}
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:opacity-50"
          title={t("logout")}
        >
          <LogOut className="size-4" />
          <span className="hidden sm:inline">
            {isLoggingOut ? t("loggingOut") : t("logout")}
          </span>
        </button>
      </div>
    </header>
  );
}