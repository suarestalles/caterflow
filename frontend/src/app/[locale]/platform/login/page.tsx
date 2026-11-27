
"use client";

import { useState, type FormEvent } from "react";
import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { useAuth } from "@/providers/auth-provider";

export default function PlatformLoginPage() {
  const t = useTranslations("PlatformLogin");
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const { reloadSession } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const languages = [
    { code: "es", label: "Español" },
    { code: "pt", label: "Português" },
    { code: "en", label: "English" },
  ] as const;

  function handleLocaleChange(newLocale: string) {
    router.replace(pathname, {
      locale: newLocale as "es" | "pt" | "en",
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!email.trim() || !password) {
      setError(t("requiredFields"));
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/platform/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "same-origin",
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      if (!response.ok) {
        setError(t("invalidCredentials"));
        return;
      }

      const authenticated = await reloadSession();

      if (!authenticated) {
        setError(t("sessionError"));
        return;
      }

      router.replace("/platform");
      router.refresh();
    } catch {
      setError(t("unexpectedError"));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            CaterFlow
          </h1>

          <div className="mt-6">
            <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary">
              Platform Admin
            </span>
          </div>

          <h2 className="mt-5 text-2xl font-semibold tracking-tight">
            {t("title")}
          </h2>

          <p className="mt-2 text-sm text-muted-foreground">
            {t("description")}
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col space-y-5 rounded-xl border bg-card p-6 shadow-sm"
        >
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              {t("email")}
            </label>

            <input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder={t("emailPlaceholder")}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none transition focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              {t("password")}
            </label>

            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder={t("passwordPlaceholder")}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none transition focus:ring-2 focus:ring-primary"
            />
          </div>

          {error && (
            <p
              role="alert"
              className="rounded-md bg-destructive/10 p-3 text-sm text-destructive"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="h-10 w-full rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? t("submitting") : t("submit")}
          </button>

          <select
            aria-label="Idioma"
            value={locale}
            onChange={(event) => handleLocaleChange(event.target.value)}
            className="h-9 rounded-lg border border-border bg-background px-2 text-sm font-medium text-foreground outline-none focus:ring-2 focus:ring-primary"
          >
            {languages.map((language) => (
              <option key={language.code} value={language.code}>
                {language.label}
              </option>
            ))}
          </select>
        </form>
      </div>
    </main>
  );
}
