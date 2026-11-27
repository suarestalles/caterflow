
"use client";

import { FormEvent, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { ApiError, apiRequest } from "@/lib/api/client";

export type PlatformUserTenant = {
  id: string;
  name: string;
};

export type PlatformUser = {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  is_platform_admin: boolean;
  tenants: PlatformUserTenant[];
  created_at: string;
  updated_at: string;
};

type TenantListResponse = {
  items: PlatformUserTenant[];
  total: number;
  offset: number;
  limit: number;
};

type UserFormModalProps = {
  open: boolean;
  user?: PlatformUser | null;
  onClose: () => void;
  onSuccess: (user: PlatformUser) => void;
};

export function UserFormModal({
  open,
  user,
  onClose,
  onSuccess,
}: UserFormModalProps) {
  const t = useTranslations("PlatformUsers");

  const isEditing = Boolean(user);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isPlatformAdmin, setIsPlatformAdmin] = useState(false);
  const [selectedTenantIds, setSelectedTenantIds] = useState<string[]>([]);

  const [tenants, setTenants] = useState<PlatformUserTenant[]>([]);
  const [loadingTenants, setLoadingTenants] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;

    setFullName(user?.full_name ?? "");
    setEmail(user?.email ?? "");
    setPassword("");
    setIsPlatformAdmin(user?.is_platform_admin ?? false);
    setSelectedTenantIds(user?.tenants.map((tenant) => tenant.id) ?? []);
    setError("");

    let cancelled = false;

    async function loadTenants() {
      setLoadingTenants(true);

      try {
        const response = await apiRequest<TenantListResponse>(
          "platform-tenants/?offset=0&limit=100",
        );

        if (!cancelled) {
          setTenants(response.items);
        }
      } catch {
        if (!cancelled) {
          setError(t("loadTenantsError"));
        }
      } finally {
        if (!cancelled) {
          setLoadingTenants(false);
        }
      }
    }

    void loadTenants();

    return () => {
      cancelled = true;
    };
  }, [open, user, t]);

  if (!open) return null;

  function toggleTenant(tenantId: string) {
    setSelectedTenantIds((current) =>
      current.includes(tenantId)
        ? current.filter((id) => id !== tenantId)
        : [...current, tenantId],
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (fullName.trim().length < 2) {
      setError(t("invalidName"));
      return;
    }

    if (!email.trim()) {
      setError(t("validationError"));
      return;
    }

    if (!isEditing && password.length < 12) {
      setError(t("invalidPassword"));
      return;
    }

    if (!isPlatformAdmin && selectedTenantIds.length === 0) {
      setError(t("userRequiresTenant"));
      return;
    }

    setLoading(true);

    try {
      const payload = {
        full_name: fullName.trim(),
        email: email.trim().toLowerCase(),
        is_platform_admin: isPlatformAdmin,
        tenant_ids: selectedTenantIds,
        ...(!isEditing ? { password } : {}),
      };

      const savedUser = isEditing
        ? await apiRequest<PlatformUser>(`platform-users/${user!.id}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
          })
        : await apiRequest<PlatformUser>("platform-users/", {
            method: "POST",
            body: JSON.stringify(payload),
          });

      onSuccess(savedUser);
      onClose();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError(t("emailAlreadyExists"));
      } else if (err instanceof ApiError && err.status === 422) {
        setError(t("validationError"));
      } else {
        setError(isEditing ? t("updateError") : t("createError"));
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-modal-title"
        className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"
      >
        <div className="mb-6">
          <h2
            id="user-modal-title"
            className="text-xl font-semibold text-slate-900"
          >
            {isEditing ? t("editTitle") : t("createTitle")}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {isEditing ? t("editDescription") : t("createDescription")}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label
              htmlFor="user-full-name"
              className="mb-1.5 block text-sm font-medium text-slate-700"
            >
              {t("fullName")}
            </label>

            <input
              id="user-full-name"
              type="text"
              required
              minLength={2}
              maxLength={150}
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder={t("fullNamePlaceholder")}
              className="h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
            />
          </div>

          <div>
            <label
              htmlFor="user-email"
              className="mb-1.5 block text-sm font-medium text-slate-700"
            >
              {t("email")}
            </label>

            <input
              id="user-email"
              type="email"
              required
              maxLength={254}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder={t("emailPlaceholder")}
              className="h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
            />
          </div>

          {!isEditing && (
            <div>
              <label
                htmlFor="user-password"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                {t("password")}
              </label>

              <input
                id="user-password"
                type="password"
                required
                minLength={12}
                maxLength={128}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={t("passwordPlaceholder")}
                className="h-10 w-full rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
              />

              <p className="mt-1 text-xs text-slate-500">
                {t("passwordHint")}
              </p>
            </div>
          )}

          <div className="rounded-xl border border-slate-200 p-4">
            <label className="flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                checked={isPlatformAdmin}
                onChange={(event) => setIsPlatformAdmin(event.target.checked)}
                className="mt-0.5 size-4 rounded border-slate-300 accent-primary"
              />

              <span>
                <span className="block text-sm font-medium text-slate-800">
                  {t("platformAdmin")}
                </span>
                <span className="mt-1 block text-xs text-slate-500">
                  {t("platformAdminDescription")}
                </span>
              </span>
            </label>
          </div>

          <div>
            <div className="mb-2 flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">
                {t("tenants")}
              </label>

              <span className="text-xs text-slate-500">
                {t("selectedTenants", {
                  count: selectedTenantIds.length,
                })}
              </span>
            </div>

            {loadingTenants ? (
              <p className="rounded-lg border border-slate-200 px-3 py-4 text-center text-sm text-slate-500">
                {t("loadingTenants")}
              </p>
            ) : tenants.length === 0 ? (
              <p className="rounded-lg border border-slate-200 px-3 py-4 text-center text-sm text-slate-500">
                {t("noTenants")}
              </p>
            ) : (
              <div className="flex max-h-48 flex-wrap gap-2 overflow-y-auto rounded-lg border border-slate-200 p-3">
                {tenants.map((tenant) => {
                  const selected = selectedTenantIds.includes(tenant.id);

                  return (
                    <button
                      key={tenant.id}
                      type="button"
                      onClick={() => toggleTenant(tenant.id)}
                      aria-pressed={selected}
                      className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                        selected
                          ? "border-primary bg-primary text-white"
                          : "border-slate-200 bg-white text-slate-600 hover:border-primary hover:text-primary"
                      }`}
                    >
                      {selected ? "✓ " : "+ "}
                      {tenant.name}
                    </button>
                  );
                })}
              </div>
            )}

            <p className="mt-2 text-xs text-slate-500">
              {t("tenantsHint")}
            </p>
          </div>

          {error && (
            <p
              role="alert"
              className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
            >
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 border-t border-slate-100 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="h-9 rounded-lg border border-slate-200 px-4 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {t("cancel")}
            </button>

            <button
              type="submit"
              disabled={loading || loadingTenants}
              className="h-9 rounded-lg bg-primary px-4 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
            >
              {loading
                ? t("saving")
                : isEditing
                  ? t("saveChanges")
                  : t("create")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
