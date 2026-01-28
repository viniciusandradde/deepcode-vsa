"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { GenesisUIProvider } from "@/state/useGenesisUI";
import { ChatPane } from "@/components/app/ChatPane";
import { Sidebar } from "@/components/app/Sidebar";
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

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("sidebarCollapsed", String(sidebarCollapsed));
    }
  }, [sidebarCollapsed]);

  return (
    <ErrorBoundary>
      <GenesisUIProvider>
        <div className="flex h-screen">
          <Sidebar collapsed={sidebarCollapsed} />
          <ChatPane 
            sidebarCollapsed={sidebarCollapsed}
            onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        </div>
        {/* PWA Banners com lazy loading (client-only, sem SSR) */}
        <OfflineBanner />
        <InstallPromptBanner />
      </GenesisUIProvider>
    </ErrorBoundary>
  );
}

