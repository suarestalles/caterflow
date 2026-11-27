
"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "@/i18n/navigation";
import { useAuth } from "@/providers/auth-provider";

export function PlatformAuthGuard({
  children,
}: {
  children: ReactNode;
}) {
  const { session, isLoading, error, reloadSession } = useAuth();
  const router = useRouter();

  const isPlatformAdmin = session?.is_platform_admin === true;

  useEffect(() => {
    if (!isLoading && !error && !isPlatformAdmin) {
      router.replace("/platform/login");
    }
  }, [error, isLoading, isPlatformAdmin, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div
          className="h-8 w-8 animate-spin rounded-full border-4 border-primary/20 border-t-primary"
          role="status"
          aria-label="Verificando sessão administrativa"
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

  if (!isPlatformAdmin) return null;

  return children;
}
