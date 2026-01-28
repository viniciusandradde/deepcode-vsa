#!/usr/bin/env python3
"""Script para adicionar tratamento de erros amigáveis no frontend."""

import re

# Caminho do arquivo (usando tmp para evitar problemas de permissão)
file_path = "/tmp/useGenesisUI_original.tsx"
output_path = "/tmp/useGenesisUI_modified.tsx"

# Lê o conteúdo atual
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Código de tratamento de erros a ser adicionado
error_handling_code = '''
// ============================================
// Error Translation - User-friendly messages
// ============================================
interface TranslatedError {
  title: string;
  message: string;
  suggestions: string[];
  isRecoverable: boolean;
}

function translateApiError(error: string): TranslatedError {
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

function formatErrorMessage(translated: TranslatedError): string {
  const icon = translated.isRecoverable ? "⚠️" : "❌";
  const suggestions = translated.suggestions.map((s, i) => `${i + 1}. ${s}`).join("\\n");
  
  return `${icon} **${translated.title}**

${translated.message}

**Como resolver:**
${suggestions}`;
}

'''

# Verifica se o código já foi adicionado
if "translateApiError" not in content:
    # Encontra a posição para inserir (após os imports, antes do hook)
    insert_marker = '// Custom hook for localStorage persistence'
    
    if insert_marker in content:
        content = content.replace(
            insert_marker,
            error_handling_code + insert_marker
        )
        print("✅ Código de tratamento de erros adicionado")
    else:
        print("❌ Marcador não encontrado")
        exit(1)
else:
    print("ℹ️ Código de tratamento de erros já existe")

# Atualiza o tratamento de erros no stream (type === "error")
old_stream_error = '''} else if (data.type === "error") {
                        console.error("[STREAM] Error from stream:", data.error);
                        throw new Error(data.error);'''

new_stream_error = '''} else if (data.type === "error") {
                        console.error("[STREAM] Error from stream:", data.error);
                        const translated = translateApiError(data.error || "Erro desconhecido");
                        const formattedError = formatErrorMessage(translated);
                        throw new Error(formattedError);'''

if old_stream_error in content:
    content = content.replace(old_stream_error, new_stream_error)
    print("✅ Tratamento de erro no stream atualizado")
else:
    print("ℹ️ Tratamento de erro no stream já atualizado ou não encontrado")

# Atualiza a mensagem de erro final no catch
old_catch_error = '''// Show error to user with detailed message
        const errorMessage: GenesisMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `❌ **Erro ao enviar mensagem**\\n\\n${errorMsg}${errorDetails}\\n\\n**Possíveis causas:**\\n- API keys não configuradas (OPENROUTER_API_KEY, OPENAI_API_KEY)\\n- Backend não está acessível\\n- Problema de conexão\\n\\nVerifique os logs do backend para mais detalhes.`,
          timestamp: Date.now(),
        };'''

new_catch_error = '''// Show error to user with detailed message
        // Use translated error if not already formatted
        let finalErrorContent = errorMsg;
        if (!errorMsg.includes("**Como resolver:**")) {
          const translated = translateApiError(errorMsg);
          finalErrorContent = formatErrorMessage(translated);
        }
        const errorMessage: GenesisMessage = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: finalErrorContent + errorDetails,
          timestamp: Date.now(),
        };'''

if old_catch_error in content:
    content = content.replace(old_catch_error, new_catch_error)
    print("✅ Mensagem de erro no catch atualizada")
else:
    print("ℹ️ Mensagem de erro no catch já atualizada ou não encontrada")

# Salva o arquivo modificado
with open(output_path, "w", encoding="utf-8") as f:
    f.write(content)

print("\n✅ Arquivo modificado salvo em:")
print(f"📁 {output_path}")
