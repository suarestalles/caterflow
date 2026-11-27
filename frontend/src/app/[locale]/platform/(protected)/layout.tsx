
import type { ReactNode } from "react";
import { PlatformAuthGuard } from "@/components/auth/platform-auth-guard";
import { PlatformAdminLayout } from "@/components/platform/layout/platform-admin-layout";

export default function PlatformLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <PlatformAuthGuard>
    <PlatformAdminLayout>
        {children}
    </PlatformAdminLayout>
  </PlatformAuthGuard>;
}
