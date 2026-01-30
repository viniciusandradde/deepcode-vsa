/**
 * Get the backend API URL based on the current environment.
 */
export function getApiBaseUrl(): string {
  // Try environment variable first
  const envUrl = process.env.NEXT_PUBLIC_API_BASE;
  
  // In browser: check window.location
  if (typeof window !== "undefined") {
    const { protocol, hostname, port } = window.location;
    
    // Debug log
    console.log("[API-URL] Browser detected:", { protocol, hostname, port, envUrl });
    
    // If we have a valid env URL that's not localhost, use it
    if (envUrl && !envUrl.includes("localhost")) {
      console.log("[API-URL] Using env URL:", envUrl);
      return envUrl;
    }
    
    // For localhost development
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      const url = "http://localhost:8000";
      console.log("[API-URL] Using localhost:", url);
      return url;
    }
    
    // For production: same host, port 8000
    const url = `${protocol}//${hostname}:8000`;
    console.log("[API-URL] Using derived URL:", url);
    return url;
  }
  
  // Server-side
  const serverUrl = envUrl || "http://localhost:8000";
  console.log("[API-URL] Server-side URL:", serverUrl);
  return serverUrl;
}
