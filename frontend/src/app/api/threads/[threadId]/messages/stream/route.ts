import { NextRequest, NextResponse } from "next/server";
import { apiBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${apiBaseUrl}${path}`;
}

interface PostPayload {
  content: string;
  model: string;
  useTavily: boolean;
  thread_id?: string;
  // VSA Integration fields (Task 1.1)
  enable_vsa?: boolean;
  enable_glpi?: boolean;
  enable_zabbix?: boolean;
  enable_linear?: boolean;
  enable_planning?: boolean;
}

const isDev = process.env.NODE_ENV === "development";

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

    const backendUrl = backend("/api/v1/chat/stream");

    if (isDev) {
      console.log("[DEBUG] Attempting fetch to:", backendUrl);
    }

    // Timeout para conexao inicial com o backend (120s)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120_000);

    let res: Response;
    try {
      res = await fetch(backendUrl, {
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
        }),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeoutId);
    }

    if (!res.ok) {
      let errorMessage = `Failed to start stream (${res.status})`;

      try {
        const errorData = await res.json();
        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        } else if (errorData.detail?.message) {
          errorMessage = errorData.detail.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch {
        try {
          const errorText = await res.text();
          if (errorText) errorMessage = errorText;
        } catch {
          // Use default error message
        }
      }

      return NextResponse.json({
        error: errorMessage,
        status: res.status,
      }, { status: res.status });
    }

    return new NextResponse(res.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  } catch (error) {
    console.error("[ERROR] Stream fetch failed:", error instanceof Error ? error.message : error);

    let errorMessage = "Failed to start stream";
    let errorType = "Unknown";

    if (error instanceof Error) {
      if (error.name === "AbortError") {
        errorType = "Timeout";
        errorMessage = "O backend nao respondeu em 120 segundos. Verifique se o servico esta rodando.";
      } else if (error.message.includes("ECONNREFUSED") || error.message.includes("connection refused")) {
        errorType = "Connection Refused";
        errorMessage = "Backend is not reachable. Check if the service is running.";
      } else if (error.message.includes("ETIMEDOUT") || error.message.includes("timeout")) {
        errorType = "Timeout";
        errorMessage = "Backend is not responding.";
      } else if (error.message.includes("ENOTFOUND") || error.message.includes("getaddrinfo")) {
        errorType = "DNS Resolution Failed";
        errorMessage = "Cannot resolve backend hostname.";
      } else if (error.message.includes("fetch failed")) {
        errorType = "Network Error";
        errorMessage = "Network connection to backend failed.";
      } else {
        errorMessage = "An internal error occurred.";
      }
    }

    return NextResponse.json(
      {
        error: errorMessage,
        errorType: errorType,
      },
      { status: 500 }
    );
  }
}
