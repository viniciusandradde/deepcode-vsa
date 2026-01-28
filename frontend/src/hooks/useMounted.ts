import { useEffect, useState } from "react";

/**
 * Hook para detectar se o componente está montado no cliente
 * Previne hydration mismatch errors entre server e client rendering
 */
export function useMounted() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return mounted;
}
