"use client";

import { useState, type ReactNode } from "react";

import { PlatformHeader } from "./platform-header";
import { PlatformSidebar } from "./platform-sidebar";

export function PlatformAdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  function closeMobileMenu() {
    setMobileOpen(false);
  }

  return (
    <div className="flex min-h-screen bg-background">
      {mobileOpen && (
        <button
          type="button"
          aria-label="Fechar menu"
          onClick={closeMobileMenu}
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
        />
      )}

      <PlatformSidebar
        mobileOpen={mobileOpen}
        onClose={closeMobileMenu}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <PlatformHeader
          onMenuClick={() => setMobileOpen(true)}
        />

        <main className="min-w-0 flex-1 p-6 sm:p-8">
          <div className="mx-auto w-full max-w-7xl">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}