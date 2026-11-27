
"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import {
  Search,
  Plus,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Pencil,
  Shield,
} from "lucide-react";

import { apiRequest, ApiError } from "@/lib/api/client";
import {
  PlatformUser,
  UserFormModal,
} from "@/components/platform/users/user-form-modal";
import { UserStatusBadge } from "@/components/platform/users/user-status-badge";

type UserListResponse = {
  items: PlatformUser[];
  total: number;
  offset: number;
  limit: number;
};

const PAGE_SIZE = 20;

export default function PlatformUsersPage() {
  const t = useTranslations("PlatformUsers");

  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<PlatformUser | null>(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        offset: String(offset),
        limit: String(PAGE_SIZE),
      });

      if (search.trim()) {
        params.set("search", search.trim());
      }

      if (statusFilter !== "all") {
        params.set("is_active", statusFilter === "active" ? "true" : "false");
      }

      const response = await apiRequest<UserListResponse>(
        `platform-users/?${params.toString()}`,
      );

      setUsers(response.items);
      setTotal(response.total);
    } catch {
      setError(t("loadError"));
    } finally {
      setLoading(false);
    }
  }, [offset, search, statusFilter, t]);

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void loadUsers();
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [loadUsers, refreshKey]);

  function handleSearchChange(value: string) {
    setSearch(value);
    setOffset(0);
    setSuccess("");
  }

  function handleFilterChange(value: string) {
    setStatusFilter(value);
    setOffset(0);
    setSuccess("");
  }

  function openCreateModal() {
    setSelectedUser(null);
    setModalOpen(true);
    setError("");
    setSuccess("");
  }

  function openEditModal(user: PlatformUser) {
    setSelectedUser(user);
    setModalOpen(true);
    setError("");
    setSuccess("");
  }

  function closeModal() {
    setModalOpen(false);
    setSelectedUser(null);
  }

  function handleSaved(user: PlatformUser) {
    setSuccess(
      selectedUser
        ? t("updatedSuccess", { name: user.full_name })
        : t("createdSuccess", { name: user.full_name }),
    );

    setSearch("");
    setStatusFilter("all");
    setOffset(0);
    setRefreshKey((current) => current + 1);
  }

  async function handleStatusChange(user: PlatformUser) {
    const nextAction = user.is_active ? "deactivate" : "activate";

    const confirmed = window.confirm(
      user.is_active
        ? t("confirmDeactivate", { name: user.full_name })
        : t("confirmActivate", { name: user.full_name }),
    );

    if (!confirmed) return;

    setActionLoading(user.id);
    setError("");
    setSuccess("");

    try {
      await apiRequest<PlatformUser>(
        `platform-users/${user.id}/${nextAction}`,
        { method: "POST" },
      );

      setSuccess(
        user.is_active
          ? t("deactivatedSuccess")
          : t("activatedSuccess"),
      );

      setRefreshKey((current) => current + 1);
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setError(t("cannotDeactivateSelf"));
      } else {
        setError(t("actionError"));
      }
    } finally {
      setActionLoading(null);
    }
  }

  const firstItem = total === 0 ? 0 : offset + 1;
  const lastItem = Math.min(offset + PAGE_SIZE, total);
  const canGoBack = offset > 0;
  const canGoForward = offset + PAGE_SIZE < total;

  return (
    <main className="min-h-screen bg-background p-6 sm:p-10">
      <div className="mx-auto max-w-7xl">
        <div className="space-y-6">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-6 text-primary" />
                <h1 className="text-2xl font-semibold text-slate-900">
                  {t("title")}
                </h1>
              </div>

              <p className="mt-1 text-sm text-slate-500">
                {t("description")}
              </p>
            </div>

            <button
              type="button"
              onClick={openCreateModal}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-primary px-4 text-sm font-medium text-white hover:opacity-90"
            >
              <Plus className="size-4" />
              {t("newUser")}
            </button>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />

                <input
                  type="search"
                  value={search}
                  onChange={(event) => handleSearchChange(event.target.value)}
                  placeholder={t("searchPlaceholder")}
                  className="h-10 w-full rounded-lg border border-slate-200 pl-9 pr-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(event) => handleFilterChange(event.target.value)}
                className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-primary"
              >
                <option value="all">{t("allStatuses")}</option>
                <option value="active">{t("active")}</option>
                <option value="inactive">{t("inactive")}</option>
              </select>

              <button
                type="button"
                onClick={() => setRefreshKey((current) => current + 1)}
                disabled={loading}
                title={t("refresh")}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-slate-200 px-3 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                <RefreshCw
                  className={`size-4 ${loading ? "animate-spin" : ""}`}
                />
                <span className="sm:hidden">{t("refresh")}</span>
              </button>
            </div>

            {error && (
              <p
                role="alert"
                className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
              >
                {error}
              </p>
            )}

            {success && (
              <p
                role="status"
                className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700"
              >
                {success}
              </p>
            )}

            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-3 py-3 font-medium">{t("name")}</th>
                    <th className="px-3 py-3 font-medium">{t("email")}</th>
                    <th className="px-3 py-3 font-medium">{t("tenants")}</th>
                    <th className="px-3 py-3 font-medium">{t("status")}</th>
                    <th className="px-3 py-3 text-right font-medium">
                      {t("actions")}
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {loading ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-3 py-10 text-center text-slate-500"
                      >
                        {t("loading")}
                      </td>
                    </tr>
                  ) : users.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-3 py-10 text-center text-slate-500"
                      >
                        {t("empty")}
                      </td>
                    </tr>
                  ) : (
                    users.map((user) => (
                      <tr key={user.id} className="hover:bg-slate-50/70">
                        <td className="px-3 py-4">
                          <div className="font-medium text-slate-900">
                            {user.full_name}
                          </div>

                          {user.is_platform_admin && (
                            <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
                              <Shield className="size-3" />
                              {t("platformAdmin")}
                            </span>
                          )}
                        </td>

                        <td className="px-3 py-4 text-slate-600">
                          {user.email}
                        </td>

                        <td className="px-3 py-4">
                          {user.tenants.length > 0 ? (
                            <div className="flex max-w-sm flex-wrap gap-1.5">
                              {user.tenants.map((tenant) => (
                                <span
                                  key={tenant.id}
                                  className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700"
                                >
                                  {tenant.name}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400">
                              {t("noTenants")}
                            </span>
                          )}
                        </td>

                        <td className="px-3 py-4">
                          <UserStatusBadge isActive={user.is_active} />
                        </td>

                        <td className="px-3 py-4">
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => openEditModal(user)}
                              title={t("edit")}
                              aria-label={t("edit")}
                              className="inline-flex size-8 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 hover:text-primary"
                            >
                              <Pencil className="size-4" />
                            </button>

                            <button
                              type="button"
                              onClick={() => void handleStatusChange(user)}
                              disabled={actionLoading === user.id}
                              className={`rounded-lg px-3 py-1.5 text-xs font-medium disabled:opacity-50 ${
                                user.is_active
                                  ? "text-red-700 hover:bg-red-50"
                                  : "text-emerald-700 hover:bg-emerald-50"
                              }`}
                            >
                              {actionLoading === user.id
                                ? t("processing")
                                : user.is_active
                                  ? t("deactivate")
                                  : t("activate")}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="mt-4 flex flex-col justify-between gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center">
              <p className="text-xs text-slate-500">
                {t("pagination", {
                  first: firstItem,
                  last: lastItem,
                  total,
                })}
              </p>

              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setOffset((current) => Math.max(0, current - PAGE_SIZE))
                  }
                  disabled={!canGoBack || loading}
                  className="inline-flex size-8 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                  aria-label={t("previousPage")}
                >
                  <ChevronLeft className="size-4" />
                </button>

                <button
                  type="button"
                  onClick={() => setOffset((current) => current + PAGE_SIZE)}
                  disabled={!canGoForward || loading}
                  className="inline-flex size-8 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40"
                  aria-label={t("nextPage")}
                >
                  <ChevronRight className="size-4" />
                </button>
              </div>
            </div>
          </div>

          <UserFormModal
            open={modalOpen}
            user={selectedUser}
            onClose={closeModal}
            onSuccess={handleSaved}
          />
        </div>
      </div>
    </main>
  );
}
