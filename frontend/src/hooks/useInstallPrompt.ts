import { useState, useEffect } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

export function useInstallPrompt() {
  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    try {
      // Verifica se já está instalado (PWA standalone)
      if (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) {
        setIsInstalled(true);
        return;
      }

      const handleBeforeInstall = (e: Event) => {
        e.preventDefault();
        setInstallPrompt(e as BeforeInstallPromptEvent);
      };

      window.addEventListener("beforeinstallprompt", handleBeforeInstall);

      return () => {
        window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
      };
    } catch (error) {
      console.warn("useInstallPrompt error:", error);
    }
  }, []);

  const promptInstall = async () => {
    if (!installPrompt) return false;

    try {
      await installPrompt.prompt();
      const choice = await installPrompt.userChoice;

      if (choice.outcome === "accepted") {
        setInstallPrompt(null);
        setIsInstalled(true);
        return true;
      }

      return false;
    } catch (error) {
      console.warn("promptInstall error:", error);
      return false;
    }
  };

  return {
    installPrompt,
    isInstalled,
    canInstall: !!installPrompt && !isInstalled,
    promptInstall,
  };
}

