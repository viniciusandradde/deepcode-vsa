"use client";

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { GenesisUIProvider } from "@/state/useGenesisUI";
import { ChatPane } from "@/components/app/ChatPane";
import { Sidebar } from "@/components/app/Sidebar";
import { CommandPalette } from "@/components/app/CommandPalette";
import { ErrorBoundary } from "@/components/app/ErrorBoundary";

// Lazy load PWA banners (client-only) para evitar hydration mismatch
const InstallPromptBanner = dynamic(
  () => import("@/components/app/InstallPromptBanner").then(mod => ({ default: mod.InstallPromptBanner })),
  { ssr: false }
);

const OfflineBanner = dynamic(
  () => import("@/components/app/OfflineBanner").then(mod => ({ default: mod.OfflineBanner })),
  { ssr: false }
);

export default function Home() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("sidebarCollapsed");
      return saved === "true";
    }
    return false;
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cmdkOpen, setCmdkOpen] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("sidebarCollapsed", String(sidebarCollapsed));
    }
  }, [sidebarCollapsed]);

  const handleSidebarToggle = useCallback(() => {
    if (typeof window === "undefined") return;
    if (window.innerWidth < 1024) {
      setSidebarOpen((prev) => !prev);
      return;
    }
    setSidebarCollapsed((prev) => !prev);
  }, []);

  const handleSidebarClose = useCallback(() => {
    setSidebarOpen(false);
  }, []);

  // Cmd+K / Ctrl+K global shortcut
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCmdkOpen((prev) => !prev);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <ErrorBoundary>
      <GenesisUIProvider>
        <div className="relative min-h-[100dvh] min-w-0 overflow-x-hidden lg:flex">
          <Sidebar
            collapsed={sidebarCollapsed}
            open={sidebarOpen}
            onClose={handleSidebarClose}
          />
          <ChatPane
            sidebarCollapsed={sidebarCollapsed}
            sidebarOpen={sidebarOpen}
            onToggleSidebar={handleSidebarToggle}
          />
        </div>
        <CommandPalette open={cmdkOpen} onOpenChange={setCmdkOpen} />
        {/* PWA Banners com lazy loading (client-only, sem SSR) */}
        <OfflineBanner />
        <InstallPromptBanner />
      </GenesisUIProvider>
    </ErrorBoundary>
  );
}
