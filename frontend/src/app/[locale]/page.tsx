
import { AppShell } from "@/components/layout/app-shell";
import { DashboardOverview } from "@/components/dashboard/dashboard-overview";
import { useTranslations } from "next-intl";

export default function Home() {
  const t = useTranslations("Dashboard");

  return (
    <AppShell>
      <div className="mb-8">
        <h2 className="text-2xl font-bold tracking-tight">
          {t("title")}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("welcome")}
        </p>
      </div>

      <DashboardOverview />
    </AppShell>
  );
}
