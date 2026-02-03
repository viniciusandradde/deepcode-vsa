"use client";

import { useState } from "react";
import { Download, X } from "lucide-react";
import { useInstallPrompt } from "@/hooks/useInstallPrompt";
import { useMounted } from "@/hooks/useMounted";

export function InstallPromptBanner() {
  const mounted = useMounted();
  const { canInstall, promptInstall } = useInstallPrompt();
  const [dismissed, setDismissed] = useState(false);

  // Só renderiza após montar no cliente (previne hydration mismatch)
  if (!mounted || !canInstall || dismissed) return null;

  const handleInstall = async () => {
    const accepted = await promptInstall();
    if (accepted) {
      setDismissed(true);
    }
  };

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 max-w-md w-full mx-4">
      <div className="bg-vsa-orange-gradient text-slate-900 rounded-lg border-2 border-vsa-orange/30 shadow-lg p-4 flex items-center gap-3">
        <Download className="w-6 h-6 flex-shrink-0" />
        <div className="flex-1">
          <p className="font-semibold text-sm">Instalar VSA Nexus AI</p>
          <p className="text-xs opacity-90">Acesse offline e tenha melhor performance</p>
        </div>
        <button
          onClick={handleInstall}
          className="bg-white text-slate-900 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-100 transition-colors border-2 border-white/60"
        >
          Instalar
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="text-slate-900 hover:bg-white/40 p-1 rounded transition-colors"
          aria-label="Dispensar"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
