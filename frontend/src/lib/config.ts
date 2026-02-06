// For server-side (Next.js API routes): use Docker service name or localhost
// For client-side: use NEXT_PUBLIC_API_BASE (exposed to browser)
const SERVER_API_BASE = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const CLIENT_API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

// API routes always run on server, so use server URL
// Client code uses CLIENT_API_BASE (but should use API routes, not direct backend calls)
export const apiBaseUrl = SERVER_API_BASE;
export const clientApiBaseUrl = CLIENT_API_BASE;
