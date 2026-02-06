import type { TranslatedError } from "./types";

export function translateApiError(error: string): TranslatedError {
  const errorLower = error.toLowerCase();

  // Authentication errors
  if (errorLower.includes("user not found") || errorLower.includes("401")) {
    return {
      title: "Erro de Autenticação",
      message: "A chave de API do OpenRouter é inválida ou expirou.",
      suggestions: [
        "Acesse openrouter.ai e gere uma nova API key",
        "Atualize a variável OPENROUTER_API_KEY no arquivo .env",
        "Reinicie o backend: docker compose restart backend"
      ],
      isRecoverable: false
    };
  }

  // Rate limit / quota errors
  if (errorLower.includes("rate limit") || errorLower.includes("429") || errorLower.includes("quota")) {
    return {
      title: "Limite de Requisições",
      message: "O limite de requisições da API foi atingido.",
      suggestions: [
        "Aguarde alguns minutos antes de tentar novamente",
        "Verifique seu plano no OpenRouter",
        "Considere usar um modelo diferente"
      ],
      isRecoverable: true
    };
  }

  // Spending limit
  if (errorLower.includes("spend limit") || errorLower.includes("spending limit")) {
    return {
      title: "Limite de Gastos Excedido",
      message: "O limite de gastos da chave API foi excedido.",
      suggestions: [
        "Acesse openrouter.ai/settings e aumente o Spending Limit",
        "Adicione créditos à sua conta",
        "Use um modelo mais econômico"
      ],
      isRecoverable: false
    };
  }

  // Model not found
  if (errorLower.includes("model not found") || errorLower.includes("invalid model")) {
    return {
      title: "Modelo Não Encontrado",
      message: "O modelo de IA selecionado não está disponível.",
      suggestions: [
        "Selecione outro modelo na lista",
        "Verifique se o modelo está disponível no OpenRouter"
      ],
      isRecoverable: true
    };
  }

  // Connection errors
  if (errorLower.includes("fetch") || errorLower.includes("network") || errorLower.includes("connection") || errorLower.includes("econnrefused")) {
    return {
      title: "Erro de Conexão",
      message: "Não foi possível conectar ao servidor.",
      suggestions: [
        "Verifique se o backend está rodando (porta 8000)",
        "Execute: docker compose up -d",
        "Verifique sua conexão de internet"
      ],
      isRecoverable: true
    };
  }

  // Timeout
  if (errorLower.includes("timeout") || errorLower.includes("timed out")) {
    return {
      title: "Tempo Esgotado",
      message: "A requisição demorou muito para responder.",
      suggestions: [
        "Tente novamente com uma pergunta mais curta",
        "Verifique a conexão com a internet",
        "O servidor pode estar sobrecarregado"
      ],
      isRecoverable: true
    };
  }

  // Server errors
  if (errorLower.includes("500") || errorLower.includes("internal server error")) {
    return {
      title: "Erro no Servidor",
      message: "Ocorreu um erro interno no servidor.",
      suggestions: [
        "Verifique os logs: docker logs ai_agent_backend",
        "Reinicie o backend: docker compose restart backend",
        "Tente novamente em alguns segundos"
      ],
      isRecoverable: true
    };
  }

  // Default error
  return {
    title: "Erro Inesperado",
    message: error,
    suggestions: [
      "Tente novamente",
      "Verifique os logs do backend para mais detalhes"
    ],
    isRecoverable: true
  };
}

export function formatErrorMessage(translated: TranslatedError): string {
  const icon = translated.isRecoverable ? "⚠️" : "❌";
  const suggestions = translated.suggestions.map((s, i) => `${i + 1}. ${s}`).join("\n");

  return `${icon} **${translated.title}**

${translated.message}

**Como resolver:**
${suggestions}`;
}
