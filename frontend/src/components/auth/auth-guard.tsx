
"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "@/i18n/navigation";
import { useAuth } from "@/providers/auth-provider";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { session, isLoading, error, reloadSession } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !error && !session && pathname !== "/login") {
      router.replace("/login");
    }
  }, [error, isLoading, pathname, router, session]);

  if (pathname === "/login") return children;

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

  if (!session) return null;

  return children;
}
