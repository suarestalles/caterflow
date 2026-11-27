
"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "@/i18n/navigation";
import { useAuth } from "@/providers/auth-provider";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { session, isLoading, error, reloadSession } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const isPlatformAdmin = session?.is_platform_admin === true;
  const hasTenantAccess = Boolean(session?.tenant) && !isPlatformAdmin;

  useEffect(() => {
    if (isLoading || error) return;

    if (!session) {
      router.replace("/login");
      return;
    }

    if (isPlatformAdmin) {
      router.replace("/platform");
      return;
    }

    if (!hasTenantAccess) {
      router.replace("/login");
    }
  }, [
    error,
    hasTenantAccess,
    isLoading,
    isPlatformAdmin,
    pathname,
    router,
    session,
  ]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div
          className="h-8 w-8 animate-spin rounded-full border-4 border-primary/20 border-t-primary"
          role="status"
          aria-label="Verificando sessão"
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-6 text-center">
        <p className="text-sm text-muted-foreground">{error}</p>
        <button
          type="button"
          onClick={() => void reloadSession()}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  if (!session || !hasTenantAccess) return null;

  return children;
}
