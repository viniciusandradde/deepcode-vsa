import { randomUUID } from "crypto";
import { NextResponse } from "next/server";
import { apiBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${apiBaseUrl}${path}`;
}

export async function GET() {
  try {
    // Agora buscamos as threads diretamente do backend FastAPI,
    // que lê os checkpoints do PostgreSQL.
    const res = await fetch(backend("/api/v1/threads"));

    if (!res.ok) {
      console.error("Backend /api/v1/threads responded with", res.status);
      return NextResponse.json({ threads: [] });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error loading threads:", error);
    return NextResponse.json({ error: "Failed to load threads" }, { status: 500 });
  }
}

export async function POST() {
  try {
    // Cria uma nova thread/sessão
    // Gera um ID único para a sessão
    const threadId = `thread-${Date.now()}-${randomUUID().slice(0, 12)}`;
    
    return NextResponse.json({ 
      thread_id: threadId,
      thread: {
        thread_id: threadId,
        created_at: new Date().toISOString(),
      }
    });
  } catch (error) {
    console.error("Error creating thread:", error);
    return NextResponse.json({ error: "Failed to create thread" }, { status: 500 });
  }
}

