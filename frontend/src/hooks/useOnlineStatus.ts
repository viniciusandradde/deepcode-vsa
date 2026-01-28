import { useState, useEffect } from "react";

export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined" || typeof navigator === "undefined") return;

    try {
      const handleOnline = () => setIsOnline(true);
      const handleOffline = () => setIsOnline(false);

      // Inicializa com estado atual
      if (typeof navigator.onLine !== "undefined") {
        setIsOnline(navigator.onLine);
      }

      window.addEventListener("online", handleOnline);
      window.addEventListener("offline", handleOffline);

      return () => {
        window.removeEventListener("online", handleOnline);
        window.removeEventListener("offline", handleOffline);
      };
    } catch (error) {
      console.warn("useOnlineStatus error:", error);
    }
  }, []);

  return isOnline;
}

