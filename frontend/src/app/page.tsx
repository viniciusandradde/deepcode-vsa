"use client";

import { useState, useEffect } from "react";
import { GenesisUIProvider } from "@/state/useGenesisUI";
import { ChatPane } from "@/components/app/ChatPane";
import { Sidebar } from "@/components/app/Sidebar";
import { ErrorBoundary } from "@/components/app/ErrorBoundary";
import { InstallPromptBanner } from "@/components/app/InstallPromptBanner";
import { OfflineBanner } from "@/components/app/OfflineBanner";

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
        {/* PWA Banners - renderizados após UI principal para evitar hydration issues */}
        <OfflineBanner />
        <InstallPromptBanner />
      </GenesisUIProvider>
    </ErrorBoundary>
  );
}

