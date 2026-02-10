import { NextRequest, NextResponse } from "next/server";
import { apiBaseUrl } from "@/lib/config";

function backend(path: string) {
  return `${apiBaseUrl}${path}`;
}

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const res = await fetch(backend("/api/v1/files/upload"), {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const error = await res.text();
      return NextResponse.json({ detail: error || "Upload falhou" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json({ detail: "Falha ao enviar arquivo" }, { status: 500 });
  }
}
