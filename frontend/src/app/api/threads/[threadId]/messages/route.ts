import { NextRequest, NextResponse } from "next/server";
import { apiBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${apiBaseUrl}${path}`;
}

interface PostPayload {
  content: string;
  model: string;
  useTavily: boolean;
  attachments?: Array<{
    file_id: string;
    name?: string;
    mime?: string;
    size?: number;
    url?: string;
  }>;
  enable_vsa?: boolean;
  enable_glpi?: boolean;
  enable_zabbix?: boolean;
  enable_linear?: boolean;
  enable_planning?: boolean;
}

export async function POST(
  req: NextRequest,
  context: { params: Promise<{ threadId: string }> }
) {
  try {
    const { threadId } = await context.params;
    const body = (await req.json()) as Partial<PostPayload>;

    if (!body?.content || !body.model) {
      return NextResponse.json({ error: "Missing content or model" }, { status: 400 });
    }

    // Chama a API FastAPI
    const res = await fetch(backend("/api/v1/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: body.content,
        thread_id: threadId,
        model: body.model,
        use_tavily: body.useTavily ?? false,
        enable_vsa: body.enable_vsa ?? false,
        enable_glpi: body.enable_glpi ?? false,
        enable_zabbix: body.enable_zabbix ?? false,
        enable_linear: body.enable_linear ?? false,
        enable_planning: body.enable_planning ?? false,
        attachments: body.attachments ?? [],
      }),
    });

    if (!res.ok) {
      const error = await res.text();
      return NextResponse.json({ error: error || "Failed to send message" }, { status: res.status });
    }

    const data = await res.json();
    
    // Retorna no formato esperado pelo frontend
    return NextResponse.json({ 
      result: {
        response: data.response,
        thread_id: data.conversation_id || threadId,
        messages: [
          {
            id: `user-${Date.now()}`,
            role: "user",
            content: body.content,
            timestamp: Date.now(),
          },
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: data.response,
            timestamp: Date.now(),
            modelId: body.model,
            usedTavily: body.useTavily,
          }
        ]
      }
    });
  } catch (error) {
    console.error("Error sending message:", error);
    return NextResponse.json({ error: "Failed to send message" }, { status: 500 });
  }
}

