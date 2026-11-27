
"use client";

import {
  RefreshCw,
  Plus,
  Pencil,
  Ban,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { useTranslations } from "next-intl";

import { apiRequest, ApiError } from "@/lib/api/client";
import {
  TenantFormModal,
  type Tenant,
} from "@/components/platform/tenants/tenant-form-modal";
import { TenantStatusBadge } from "@/components/platform/tenants/tenant-status-badge";

type TenantListResponse = {
  items: Tenant[];
  total: number;
  offset: number;
  limit: number;
};

const PAGE_SIZE = 10;

export default function PlatformTenantsPage() {
  const t = useTranslations("PlatformTenants");

  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);

  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTenant, setEditingTenant] = useState<Tenant | null>(null);

  const [processingTenantId, setProcessingTenantId] = useState<string | null>(
    null,
  );

  const loadTenants = useCallback(async () => {
    setIsLoading(true);
    setError("");

    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(PAGE_SIZE),
    });

    if (search) params.set("search", search);

    if (status !== "all") {
      params.set("is_active", status === "active" ? "true" : "false");
    }

    try {
      const response = await apiRequest<TenantListResponse>(
        `platform-tenants/?${params.toString()}`,
      );

      setTenants(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : t("loadError"),
      );
    } finally {
      setIsLoading(false);
    }
  }, [offset, search, status, t]);

  useEffect(() => {
    void loadTenants();
  }, [loadTenants]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      setOffset(0);
      setSearch(searchInput.trim());
      setSuccess("");
    }, 300);
  
    return () => window.clearTimeout(timeout);
  }, [searchInput]);

  function openCreateModal() {
    setEditingTenant(null);
    setIsModalOpen(true);
  }

  function openEditModal(tenant: Tenant) {
    setEditingTenant(tenant);
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingTenant(null);
  }

  async function handleModalSuccess(action: "created" | "updated") {
    setIsModalOpen(false);
    setEditingTenant(null);
    setSuccess(action === "created" ? t("created") : t("updated"));

    if (action === "created") {
      // A empresa recém-criada deve aparecer na primeira página,
      // independentemente dos filtros anteriores.
      setSearchInput("");
      setSearch("");
      setStatus("all");
      setOffset(0);

      if (offset === 0 && search === "" && status === "all") {
        await loadTenants();
      }

      return;
    }

    await loadTenants();
  }

  async function handleToggleStatus(tenant: Tenant) {
    const action = tenant.is_active ? "suspend" : "activate";

    const confirmed = window.confirm(
      tenant.is_active
        ? t("confirmSuspend", { name: tenant.name })
        : t("confirmActivate", { name: tenant.name }),
    );

    if (!confirmed) return;

    setProcessingTenantId(tenant.id);
    setError("");
    setSuccess("");

    try {
      await apiRequest(
        `platform-tenants/${tenant.id}/${action}`,
        { method: "POST" },
      );

      setSuccess(
        tenant.is_active
          ? t("suspendedSuccess")
          : t("activatedSuccess"),
      );

      await loadTenants();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : t("actionError"),
      );
    } finally {
      setProcessingTenantId(null);
    }
  }

  function handleStatusChange(value: string) {
    setOffset(0);
    setStatus(value);
    setSuccess("");
  }

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <main className="min-h-screen bg-background p-6 sm:p-10">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">
            CaterFlow / Platform Admin
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            {t("title")}
          </h1>

          <p className="mt-2 text-sm text-muted-foreground">
            {t("description")}
          </p>
        </header>

        <section className="rounded-xl border bg-card p-5 shadow-sm">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold">{t("registeredTenants")}</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {t("total", { count: total })}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={openCreateModal}
                className="flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:opacity-90"
              >
                <Plus className="size-4" />
                {t("newTenant")}
              </button>
            </div>
          </div>

          <div className="mb-5 flex flex-col gap-3 sm:flex-row">
            <input
                type="search"
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
                placeholder={t("searchPlaceholder")}
                className="h-10 min-w-0 flex-1 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
            />

            <select
                value={status}
                onChange={(event) => handleStatusChange(event.target.value)}
                className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
            >
                <option value="all">{t("allStatuses")}</option>
                <option value="active">{t("active")}</option>
                <option value="suspended">{t("suspended")}</option>
            </select>

            <button
                type="button"
                onClick={() => void loadTenants()}
                disabled={isLoading}
                title={t("refresh")}
                aria-label={t("refresh")}
                className="flex size-10 shrink-0 items-center justify-center rounded-md border transition hover:bg-muted disabled:opacity-50"
            >
                <RefreshCw
                className={`size-4 ${isLoading ? "animate-spin" : ""}`}
                />
            </button>
            </div>

          {error && (
            <div
              role="alert"
              className="mb-5 rounded-md bg-destructive/10 p-3 text-sm text-destructive"
            >
              {error}
            </div>
          )}

          {success && (
            <div
              role="status"
              className="mb-5 rounded-md bg-green-500/10 p-3 text-sm text-green-700"
            >
              {success}
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="px-3 py-3 font-medium">{t("name")}</th>
                  <th className="px-3 py-3 font-medium">{t("identifier")}</th>
                  <th className="px-3 py-3 font-medium">{t("status")}</th>
                  <th className="px-3 py-3 font-medium">{t("createdAt")}</th>
                  <th className="px-3 py-3 text-right font-medium">
                    {t("actions")}
                  </th>
                </tr>
              </thead>

              <tbody>
                {isLoading ? (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-3 py-10 text-center text-muted-foreground"
                    >
                      {t("loading")}
                    </td>
                  </tr>
                ) : tenants.length === 0 ? (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-3 py-10 text-center text-muted-foreground"
                    >
                      {t("empty")}
                    </td>
                  </tr>
                ) : (
                  tenants.map((tenant) => {
                    const isProcessing = processingTenantId === tenant.id;

                    return (
                      <tr
                        key={tenant.id}
                        className="border-b last:border-0"
                      >
                        <td className="px-3 py-4 font-medium">
                          {tenant.name}
                        </td>

                        <td className="px-3 py-4 font-mono text-xs text-muted-foreground">
                          {tenant.id}
                        </td>

                        <td className="px-3 py-4">
                          <TenantStatusBadge
                            isActive={tenant.is_active}
                            activeLabel={t("active")}
                            suspendedLabel={t("suspended")}
                          />
                        </td>

                        <td className="px-3 py-4 text-muted-foreground">
                          {new Intl.DateTimeFormat(undefined, {
                            dateStyle: "medium",
                          }).format(new Date(tenant.created_at))}
                        </td>

                        <td className="px-3 py-4">
                          <div className="flex justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => openEditModal(tenant)}
                              title={t("edit")}
                              aria-label={t("edit")}
                              className="flex size-9 items-center justify-center rounded-md border transition hover:bg-muted"
                            >
                              <Pencil className="size-4" />
                            </button>

                            <button
                              type="button"
                              onClick={() => void handleToggleStatus(tenant)}
                              disabled={isProcessing}
                              title={
                                tenant.is_active
                                  ? t("suspend")
                                  : t("activate")
                              }
                              aria-label={
                                tenant.is_active
                                  ? t("suspend")
                                  : t("activate")
                              }
                              className="flex size-9 items-center justify-center rounded-md border transition hover:bg-muted disabled:opacity-50"
                            >
                              {isProcessing ? (
                                <Loader2 className="size-4 animate-spin" />
                              ) : tenant.is_active ? (
                                <Ban className="size-4 text-destructive" />
                              ) : (
                                <CheckCircle2 className="size-4 text-green-600" />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <footer className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t pt-4">
            <p className="text-sm text-muted-foreground">
              {t("page", {
                current: currentPage,
                total: totalPages,
              })}
            </p>

            <div className="flex gap-2">
              <button
                type="button"
                disabled={offset === 0 || isLoading}
                onClick={() =>
                  setOffset((value) => Math.max(0, value - PAGE_SIZE))
                }
                className="rounded-md border px-3 py-2 text-sm disabled:opacity-40"
              >
                {t("previous")}
              </button>

              <button
                type="button"
                disabled={offset + PAGE_SIZE >= total || isLoading}
                onClick={() => setOffset((value) => value + PAGE_SIZE)}
                className="rounded-md border px-3 py-2 text-sm disabled:opacity-40"
              >
                {t("next")}
              </button>
            </div>
          </footer>
        </section>
      </div>

      <TenantFormModal
        open={isModalOpen}
        tenant={editingTenant}
        onClose={closeModal}
        onSuccess={handleModalSuccess}
      />
    </main>
  );
}
