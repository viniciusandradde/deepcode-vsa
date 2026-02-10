"use client";

import { WifiOff } from "lucide-react";
import { useOnlineStatus } from "@/hooks/useOnlineStatus";
import { useMounted } from "@/hooks/useMounted";

export function OfflineBanner() {
  const mounted = useMounted();
  const isOnline = useOnlineStatus();

  // Só renderiza após montar no cliente (previne hydration mismatch)
  if (!mounted || isOnline) return null;

  return (
    <div className="safe-area-top fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-black px-4 py-2 flex items-center justify-center gap-2">
      <WifiOff className="w-5 h-5" />
      <span className="font-medium">Sem conexão com a internet</span>
    </div>
  );
}
