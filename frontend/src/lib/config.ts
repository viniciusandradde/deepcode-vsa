// For server-side (Next.js API routes): use Docker service name or localhost
// For client-side: use NEXT_PUBLIC_API_BASE (exposed to browser)
const SERVER_API_BASE = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const CLIENT_API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const DEFAULT_LANGGRAPH_BASE = process.env.NEXT_PUBLIC_LANGGRAPH_BASE ?? "http://127.0.0.1:2024";
const DEFAULT_ASSISTANT_ID = process.env.NEXT_PUBLIC_ASSISTANT_ID ?? "agent";

// Logging para debug (apenas em desenvolvimento)
if (process.env.NODE_ENV === 'development') {
  console.log("[CONFIG] Environment variables:");
  console.log("[CONFIG]   API_BASE_URL:", process.env.API_BASE_URL || "(not set)");
  console.log("[CONFIG]   NEXT_PUBLIC_API_BASE:", process.env.NEXT_PUBLIC_API_BASE || "(not set)");
  console.log("[CONFIG]   NODE_ENV:", process.env.NODE_ENV);
  console.log("[CONFIG] Resolved URLs:");
  console.log("[CONFIG]   SERVER_API_BASE (for API routes):", SERVER_API_BASE);
  console.log("[CONFIG]   CLIENT_API_BASE (for browser):", CLIENT_API_BASE);
}

// API routes always run on server, so use server URL
// Client code uses CLIENT_API_BASE (but should use API routes, not direct backend calls)
export const apiBaseUrl = SERVER_API_BASE;
export const clientApiBaseUrl = CLIENT_API_BASE;
export const langgraphBaseUrl = DEFAULT_LANGGRAPH_BASE;
export const langgraphAssistantId = DEFAULT_ASSISTANT_ID;

