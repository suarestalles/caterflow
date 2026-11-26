
"use client";

import { useState, type ReactNode } from "react";
import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { AuthGuard } from "@/components/auth/auth-guard";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const [sidebarVisible, setSidebarVisible] = useState(true);

  return (
    <AuthGuard>
      <div className="flex min-h-screen overflow-x-hidden bg-background">
        <div
          inert={!sidebarVisible}
          aria-hidden={!sidebarVisible}
          className={`shrink-0 overflow-hidden transition-[width,opacity,transform] duration-300 ease-in-out motion-reduce:transition-none ${
            sidebarVisible
              ? "w-64 translate-x-0 opacity-100"
              : "w-0 -translate-x-4 opacity-0 pointer-events-none"
          }`}
        >
          <Sidebar onNavigate={() => setSidebarVisible(false)} />
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          <Header
            onToggleSidebar={() => setSidebarVisible((visible) => !visible)}
          />

          <main className="flex-1 p-5 sm:p-8">
            <div className="mx-auto max-w-7xl">{children}</div>
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
