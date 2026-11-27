
import type { ReactNode } from "react";
import { AuthGuard } from "@/components/auth/auth-guard";

export default function TenantLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <AuthGuard>{children}</AuthGuard>;
}
