"use client";

import { useCallback, useEffect, useState } from "react";
import { logger } from "@/lib/logger";

export function useLocalStorageState(key: string, defaultValue: boolean): [boolean, (value: boolean) => void] {
  // Always start with defaultValue for SSR
  const [state, setState] = useState<boolean>(defaultValue);

  // Hydrate from localStorage on mount (client-side only)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(key);
      logger.perf(`[useLocalStorageState] Hydrating ${key}:`, saved);

      if (saved !== null) {
        const parsedValue = saved === 'true';
        setState(parsedValue);
        logger.perf(`[useLocalStorageState] Restored ${key}:`, parsedValue);
      }
    }
  }, [key]);

  const setValue = useCallback((value: boolean) => {
    setState(value);
    if (typeof window !== 'undefined') {
      localStorage.setItem(key, String(value));
      logger.perf(`[useLocalStorageState] Saved ${key}:`, value);
    }
  }, [key]);

  return [state, setValue];
}
