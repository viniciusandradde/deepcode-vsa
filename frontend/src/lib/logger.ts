/**
 * Performance-optimized logger
 * Only logs in development mode and when DEBUG flag is enabled
 */

const IS_DEV = process.env.NODE_ENV === 'development';
const DEBUG_ENABLED = typeof window !== 'undefined' &&
  (localStorage.getItem('DEBUG') === 'true' || false);

export const logger = {
  // Only log in dev mode with DEBUG flag
  debug: (...args: any[]) => {
    if (IS_DEV && DEBUG_ENABLED) {
      console.log(...args);
    }
  },

  // Always log warnings
  warn: (...args: any[]) => {
    console.warn(...args);
  },

  // Always log errors
  error: (...args: any[]) => {
    console.error(...args);
  },

  // Performance-critical: never log
  perf: (...args: any[]) => {
    // Silenced for performance
  },
};

// Helper to enable debug logging
if (typeof window !== 'undefined') {
  (window as any).enableDebug = () => {
    localStorage.setItem('DEBUG', 'true');
    console.log('Debug logging enabled. Reload page to see debug logs.');
  };

  (window as any).disableDebug = () => {
    localStorage.removeItem('DEBUG');
    console.log('Debug logging disabled.');
  };
}
