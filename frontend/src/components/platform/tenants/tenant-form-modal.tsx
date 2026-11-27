
"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Loader2, X } from "lucide-react";
import { useTranslations } from "next-intl";

import { apiRequest, ApiError } from "@/lib/api/client";

export type Tenant = {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type TenantFormModalProps = {
  open: boolean;
  tenant: Tenant | null;
  onClose: () => void;
  onSuccess: (action: "created" | "updated") => void;
};

export function TenantFormModal({
  open,
  tenant,
  onClose,
  onSuccess,
}: TenantFormModalProps) {
  const t = useTranslations("PlatformTenants");

  const [name, setName] = useState(tenant?.name ?? "");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setName(tenant?.name ?? "");
      setError("");
    }
  }, [open, tenant]);

  if (!open) return null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedName = name.trim();

    if (!normalizedName) {
      setError(t("requiredName"));
      return;
    }

    setIsSaving(true);
    setError("");

    try {
      if (tenant) {
        await apiRequest(`platform-tenants/${tenant.id}`, {
          method: "PATCH",
          body: JSON.stringify({ name: normalizedName }),
        });

        onSuccess("updated");
      } else {
        await apiRequest("platform-tenants/", {
          method: "POST",
          body: JSON.stringify({ name: normalizedName }),
        });

        onSuccess("created");
      }
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : t("saveError"),
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !isSaving) {
          onClose();
        }
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="tenant-modal-title"
        className="w-full max-w-md rounded-xl border bg-card p-6 shadow-xl"
      >
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h2
              id="tenant-modal-title"
              className="text-xl font-semibold"
            >
              {tenant ? t("editTitle") : t("createTitle")}
            </h2>

            <p className="mt-1 text-sm text-muted-foreground">
              {t("modalDescription")}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isSaving}
            aria-label={t("close")}
            className="flex size-8 items-center justify-center rounded-md transition hover:bg-muted disabled:opacity-50"
          >
            <X className="size-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <label
            htmlFor="tenant-name"
            className="mb-2 block text-sm font-medium"
          >
            {t("name")}
          </label>

          <input
            id="tenant-name"
            type="text"
            autoFocus
            required
            maxLength={150}
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder={t("namePlaceholder")}
            disabled={isSaving}
            className="h-11 w-full rounded-md border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
          />

          {error && (
            <p role="alert" className="mt-3 text-sm text-destructive">
              {error}
            </p>
          )}

          <div className="mt-6 flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="rounded-md border px-4 py-2 text-sm font-medium transition hover:bg-muted disabled:opacity-50"
            >
              {t("cancel")}
            </button>

            <button
              type="submit"
              disabled={isSaving || !name.trim()}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
            >
              {isSaving && (
                <Loader2 className="size-4 animate-spin" />
              )}
              {isSaving ? t("saving") : t("save")}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
