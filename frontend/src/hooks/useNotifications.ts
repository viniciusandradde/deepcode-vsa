import { useState, useEffect } from "react";

export function useNotifications() {
  const [permission, setPermission] = useState<NotificationPermission>("default");
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    if ("Notification" in window) {
      setIsSupported(true);
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = async () => {
    if (!isSupported) return false;

    const result = await Notification.requestPermission();
    setPermission(result);
    return result === "granted";
  };

  const showNotification = (title: string, options?: NotificationOptions) => {
    if (!isSupported || permission !== "granted") return;

    if ("serviceWorker" in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.ready.then((registration) => {
        registration.showNotification(title, {
          icon: "/images/vsa-logo.png",
          badge: "/images/vsa-logo.png",
          ...options,
        });
      });
    } else {
      // Fallback direto (não ideal, mas funcional em alguns navegadores)
      // eslint-disable-next-line no-new
      new Notification(title, options);
    }
  };

  return {
    permission,
    isSupported,
    canNotify: permission === "granted",
    requestPermission,
    showNotification,
  };
}

