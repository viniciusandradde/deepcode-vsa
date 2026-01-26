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

    // Logging detalhado para diagnóstico
    const backendUrl = backend("/api/v1/chat/stream");
    console.log("[DEBUG] Attempting fetch to:", backendUrl);
    console.log("[DEBUG] apiBaseUrl from config:", apiBaseUrl);
    console.log("[DEBUG] API_BASE_URL env:", process.env.API_BASE_URL);
    console.log("[DEBUG] NEXT_PUBLIC_API_BASE env:", process.env.NEXT_PUBLIC_API_BASE);

    // Chama a API FastAPI com streaming
    const res = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: body.content,
        thread_id: threadId,
        model: body.model,
        use_tavily: body.useTavily ?? false,
      }),
    });

    if (!res.ok) {
      let errorMessage = `Failed to start stream (${res.status})`;
      let errorDetails: any = {};
      
      try {
        // FastAPI returns {"detail": "message"} for HTTPException
        const errorData = await res.json();
        console.error("Backend error (JSON):", errorData);
        errorDetails = errorData;
        
        // Try different error formats
        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        } else if (errorData.detail?.message) {
          errorMessage = errorData.detail.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.detail) {
          errorMessage = JSON.stringify(errorData.detail);
        }
      } catch (jsonError) {
        // If JSON parse fails, try text
        try {
          const errorText = await res.text();
          console.error("Backend error (text):", errorText);
          errorMessage = errorText || errorMessage;
          errorDetails = { text: errorText };
        } catch (textError) {
          console.error("Failed to read error response:", textError);
          errorDetails = { parseError: String(textError) };
        }
      }
      
      return NextResponse.json({ 
        error: errorMessage,
        details: errorDetails,
        status: res.status,
        statusText: res.statusText
      }, { status: res.status });
    }

    // Log antes de retornar o stream
    console.log("[STREAM] Returning stream to frontend, status:", res.status);
    console.log("[STREAM] Content-Type:", res.headers.get("content-type"));
    
    // Retorna o stream como SSE
    return new NextResponse(res.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no", // Disable buffering in nginx if present
      },
    });
  } catch (error) {
    // Logging detalhado do erro
    console.error("[ERROR] Fetch failed - Full error:", error);
    if (error instanceof Error) {
      console.error("[ERROR] Error name:", error.name);
      console.error("[ERROR] Error message:", error.message);
      console.error("[ERROR] Error stack:", error.stack);
      if ('cause' in error) {
        console.error("[ERROR] Error cause:", (error as any).cause);
      }
    }
    console.error("[ERROR] Error type:", typeof error);
    console.error("[ERROR] Error stringified:", JSON.stringify(error, Object.getOwnPropertyNames(error)));

    // Extrair informações úteis do erro
    let errorMessage = "Failed to start stream";
    let errorType = "Unknown";
    let errorDetails: any = {};

    if (error instanceof Error) {
      errorMessage = error.message;
      errorType = error.name;
      
      // Detectar tipos específicos de erro de rede
      if (error.message.includes("ECONNREFUSED") || error.message.includes("connection refused")) {
        errorType = "Connection Refused";
        errorDetails.suggestion = "Backend may not be running or URL is incorrect. Check if backend is accessible at: " + apiBaseUrl;
      } else if (error.message.includes("ETIMEDOUT") || error.message.includes("timeout")) {
        errorType = "Timeout";
        errorDetails.suggestion = "Backend is not responding. Check if backend is running and accessible.";
      } else if (error.message.includes("ENOTFOUND") || error.message.includes("getaddrinfo")) {
        errorType = "DNS Resolution Failed";
        errorDetails.suggestion = "Cannot resolve hostname. Check if 'backend' service name is correct in Docker network.";
      } else if (error.message.includes("fetch failed")) {
        errorType = "Network Error";
        errorDetails.suggestion = "Network connection failed. Verify Docker network configuration and service connectivity.";
      }

      errorDetails.errorName = error.name;
      errorDetails.errorMessage = error.message;
      if ('cause' in error) {
        errorDetails.cause = (error as any).cause;
      }
    } else {
      errorDetails.rawError = String(error);
    }

    errorDetails.errorType = errorType;
    errorDetails.attemptedUrl = apiBaseUrl + "/api/v1/chat/stream";

    return NextResponse.json(
      { 
        error: errorMessage,
        errorType: errorType,
        details: errorDetails
      }, 
      { status: 500 }
    );
  }
}

