import { NextRequest, NextResponse } from "next/server";
import { apiBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${apiBaseUrl}${path}`;
}

export async function GET(
  req: NextRequest,
  context: { params: Promise<{ threadId: string }> }
) {
  try {
    const { threadId } = await context.params;
    
    // Por enquanto, retorna mensagens vazias
    // Em produção, isso buscaria mensagens do backend
    return NextResponse.json({ 
      thread_id: threadId,
      messages: []
    });
  } catch (error) {
    console.error("Error fetching thread:", error);
    return NextResponse.json({ error: "Failed to fetch thread" }, { status: 500 });
  }
}

export async function DELETE(
  req: NextRequest,
  context: { params: Promise<{ threadId: string }> }
) {
  try {
    const { threadId } = await context.params;
    
    // Tenta deletar no backend se houver endpoint
    // Por enquanto, apenas retorna sucesso (limpeza local será feita no frontend)
    try {
      const res = await fetch(backend(`/api/v1/threads/${threadId}`), {
        method: "DELETE",
      });
      
      // Se o endpoint existir no backend, usa a resposta
      if (res.ok || res.status === 404) {
        // 404 significa que não existe no backend, o que é OK para limpeza local
        return new NextResponse(null, { status: 204 });
      }
    } catch (backendError) {
      // Backend pode não ter endpoint DELETE ainda, continua com limpeza local
      console.log("Backend DELETE endpoint not available, proceeding with local cleanup");
    }
    
    // Retorna sucesso para permitir limpeza local
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Error deleting thread:", error);
    return NextResponse.json({ error: "Failed to delete thread" }, { status: 500 });
  }
}

