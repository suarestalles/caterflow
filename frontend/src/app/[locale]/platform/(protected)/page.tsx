
"use client";

import { useAuth } from "@/providers/auth-provider";
import { useTranslations } from "next-intl";

export default function PlatformDashboardPage() {
  const t = useTranslations("Platform");
  const { session } = useAuth();

  return (
    <main className="min-h-screen bg-background p-6 sm:p-10">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b pb-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-primary">
              CaterFlow
            </p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight">
              {t("title")}
            </h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {t("description")}
            </p>
          </div>
        </header>

        <section className="mt-10 rounded-xl border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold">
            {t("welcome", {
              name: session?.user.full_name ?? "",
            })}
          </h2>

          <p className="mt-2 text-sm text-muted-foreground">
            {t("adminDescription")}
          </p>
        </section>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              title: t("tenants"),
              description: t("tenantsDescription"),
            },
            {
              title: t("users"),
              description: t("usersDescription"),
            },
            {
              title: t("memberships"),
              description: t("membershipsDescription"),
            },
          ].map((item) => (
            <article
              key={item.title}
              className="rounded-xl border bg-card p-5"
            >
              <h3 className="font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {item.description}
              </p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
