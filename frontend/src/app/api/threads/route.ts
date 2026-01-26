import { NextResponse } from "next/server";
import { apiBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${apiBaseUrl}${path}`;
}

export async function GET() {
  try {
    // Por enquanto, retorna lista vazia ou cria uma sessão padrão
    // Em produção, isso viria de um endpoint de listagem de threads
    return NextResponse.json({ threads: [] });
  } catch (error) {
    console.error("Error loading threads:", error);
    return NextResponse.json({ error: "Failed to load threads" }, { status: 500 });
  }
}

export async function POST() {
  try {
    // Cria uma nova thread/sessão
    // Gera um ID único para a sessão
    const threadId = `thread-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    
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

