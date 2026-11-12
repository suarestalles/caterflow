
"use client";

import { Bell, Menu, Search } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";

const languages = [
  { code: "es", label: "ES" },
  { code: "pt", label: "PT" },
  { code: "en", label: "EN" },
] as const;

type HeaderProps = {
  onToggleSidebar: () => void;
};

export function Header({ onToggleSidebar }: HeaderProps) {
  const t = useTranslations("Header");
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  function handleLocaleChange(newLocale: string) {
    router.replace(pathname, {
      locale: newLocale as "es" | "pt" | "en",
    });
  }

  return (
    <header className="flex min-h-20 items-center justify-between gap-4 border-b border-border bg-white px-4 sm:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          aria-label="Mostrar ou ocultar menu"
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Menu size={21} />
        </button>

        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold text-foreground">
            {t("title")}
          </h1>
          <p className="hidden text-sm text-muted-foreground sm:block">
            {t("description")}
          </p>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-3 sm:gap-5">
        <select
          aria-label="Idioma"
          value={locale}
          onChange={(event) => handleLocaleChange(event.target.value)}
          className="h-9 rounded-lg border border-border bg-white px-2 text-sm font-medium text-foreground outline-none focus:ring-2 focus:ring-primary"
        >
          {languages.map((language) => (
            <option key={language.code} value={language.code}>
              {language.label}
            </option>
          ))}
        </select>

        <button
          type="button"
          aria-label={t("search")}
          className="hidden text-muted-foreground transition-colors hover:text-foreground sm:block"
        >
          <Search size={20} />
        </button>

        <button
          type="button"
          aria-label={t("notifications")}
          className="relative text-muted-foreground transition-colors hover:text-foreground"
        >
          <Bell size={20} />
          <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-amber-500" />
        </button>

        <div className="flex items-center gap-3 border-l border-border pl-3 sm:pl-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
            CF
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-medium">{t("company")}</p>
            <p className="text-xs text-muted-foreground">
              {t("administrator")}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
