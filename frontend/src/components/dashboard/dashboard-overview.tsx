
"use client";

import {
  ArrowUpRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileText,
  MapPin,
  Users,
  Wallet,
} from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

const metrics = [
  {
    title: "eventsThisMonth",
    value: 12,
    description: "upcomingEvents",
    icon: CalendarDays,
  },
  {
    title: "pendingQuotes",
    value: 8,
    description: "awaitingApproval",
    icon: FileText,
  },
  {
    title: "expectedRevenue",
    value: 8450,
    description: "confirmedEvents",
    icon: Wallet,
  },
  {
    title: "activeClients",
    value: 24,
    description: "registeredClients",
    icon: Users,
  },
];

const upcomingEvents = [
  {
    id: 1,
    name: "corporateEvent",
    client: "Empresa ABC",
    date: "2026-11-15T12:00:00",
    location: "Valencia",
    status: "confirmed",
  },
  {
    id: 2,
    name: "birthday",
    client: "María González",
    date: "2026-11-18T19:30:00",
    location: "Paterna",
    status: "confirmed",
  },
  {
    id: 3,
    name: "coffeeBreak",
    client: "Empresa XYZ",
    date: "2026-11-21T09:00:00",
    location: "Valencia",
    status: "preparing",
  },
];

const recentActivities = [
  {
    id: 1,
    title: "quoteCreated",
    description: "corporateQuote",
    time: "twentyMinutesAgo",
    icon: FileText,
  },
  {
    id: 2,
    title: "eventConfirmed",
    description: "mariasBirthday",
    time: "twoHoursAgo",
    icon: CheckCircle2,
  },
  {
    id: 3,
    title: "clientRegistered",
    description: "companyXYZ",
    time: "yesterday",
    icon: Users,
  },
];

export function DashboardOverview() {
  const t = useTranslations("Dashboard");
  const locale = useLocale();

  const dateFormatter = new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  const currencyFormatter = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  });

  return (
    <div className="space-y-8">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;

          return (
            <div
              key={metric.title}
              className="rounded-xl border border-border bg-card p-5 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">
                  {t(metric.title)}
                </p>
                <div className="rounded-lg bg-primary/10 p-2 text-primary">
                  <Icon size={19} />
                </div>
              </div>

              <p className="mt-4 text-2xl font-bold tracking-tight">
                {metric.title === "expectedRevenue"
                  ? currencyFormatter.format(metric.value)
                  : new Intl.NumberFormat(locale, {
                      minimumIntegerDigits:
                        metric.title === "pendingQuotes" ? 2 : 1,
                    }).format(metric.value)}
              </p>

              <p className="mt-1 text-xs text-muted-foreground">
                {t(metric.description)}
              </p>
            </div>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <div className="rounded-xl border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b border-border p-5">
            <div>
              <h2 className="font-semibold">{t("nextEvents")}</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {t("scheduledEvents")}
              </p>
            </div>

            <button className="flex items-center gap-1 text-sm font-medium text-primary hover:underline">
              {t("viewAll")} <ArrowUpRight size={16} />
            </button>
          </div>

          <div className="divide-y divide-border">
            {upcomingEvents.map((event) => (
              <div
                key={event.id}
                className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <h3 className="font-medium">{t(event.name)}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {event.client}
                  </p>

                  <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <CalendarDays size={14} />
                      {dateFormatter.format(new Date(event.date))}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock3 size={14} />
                      {new Intl.DateTimeFormat(locale, {
                        hour: "2-digit",
                        minute: "2-digit",
                      }).format(new Date(event.date))}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin size={14} />
                      {event.location}
                    </span>
                  </div>
                </div>

                <span
                  className={`w-fit rounded-full px-3 py-1 text-xs font-medium ${
                    event.status === "confirmed"
                      ? "bg-emerald-500/10 text-emerald-700"
                      : "bg-amber-500/10 text-amber-700"
                  }`}
                >
                  {t(event.status)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card shadow-sm">
          <div className="border-b border-border p-5">
            <h2 className="font-semibold">{t("recentActivity")}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {t("latestUpdates")}
            </p>
          </div>

          <div className="space-y-6 p-5">
            {recentActivities.map((activity) => {
              const Icon = activity.icon;

              return (
                <div key={activity.id} className="flex gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <Icon size={17} />
                  </div>

                  <div className="min-w-0">
                    <p className="text-sm font-medium">
                      {t(activity.title)}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {t(activity.description)}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      {t(activity.time)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
