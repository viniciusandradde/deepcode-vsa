import { useEffect, useRef } from "react";

interface SwipeHandlers {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
}

export function useSwipeGesture(handlers: SwipeHandlers) {
  const touchStartX = useRef<number>(0);
  const touchEndX = useRef<number>(0);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleTouchStart = (e: TouchEvent) => {
      touchStartX.current = e.touches[0].clientX;
    };

    const handleTouchMove = (e: TouchEvent) => {
      touchEndX.current = e.touches[0].clientX;
    };

    const handleTouchEnd = () => {
      const swipeDistance = touchEndX.current - touchStartX.current;
      const minSwipeDistance = 50;

      if (Math.abs(swipeDistance) < minSwipeDistance) return;

      if (swipeDistance > 0 && handlers.onSwipeRight) {
        handlers.onSwipeRight();
      } else if (swipeDistance < 0 && handlers.onSwipeLeft) {
        handlers.onSwipeLeft();
      }

      touchStartX.current = 0;
      touchEndX.current = 0;
    };

    document.addEventListener("touchstart", handleTouchStart);
    document.addEventListener("touchmove", handleTouchMove);
    document.addEventListener("touchend", handleTouchEnd);

    return () => {
      document.removeEventListener("touchstart", handleTouchStart);
      document.removeEventListener("touchmove", handleTouchMove);
      document.removeEventListener("touchend", handleTouchEnd);
    };
  }, [handlers]);
}

