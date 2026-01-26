"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface UseAudioRecorderReturn {
  isRecording: boolean;
  transcript: string;
  error: string | null;
  isSupported: boolean;
  startRecording: () => void;
  stopRecording: () => void;
  clearTranscript: () => void;
}

// Tipos para Web Speech API
interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  onend: () => void;
  onstart: () => void;
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message: string;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

export function useAudioRecorder(
  onTranscriptUpdate?: (transcript: string) => void,
  silenceTimeout: number = 3000
): UseAudioRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastTranscriptRef = useRef<string>("");
  const processedResultsRef = useRef<Set<number>>(new Set());

  // Verificar suporte do navegador
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);

    if (!SpeechRecognition) {
      setError(
        "Seu navegador não suporta reconhecimento de voz. Use Chrome, Edge ou Safari."
      );
    }
  }, []);

  // Limpar timer ao desmontar
  useEffect(() => {
    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignorar erros ao parar
        }
      }
    };
  }, []);

  const resetSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }

    silenceTimerRef.current = setTimeout(() => {
      if (isRecording && recognitionRef.current) {
        stopRecording();
      }
    }, silenceTimeout);
  }, [isRecording, silenceTimeout]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {
        console.error("Erro ao parar gravação:", e);
      }
    }

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    setIsRecording(false);
  }, []);

  const startRecording = useCallback(() => {
    if (!isSupported) {
      setError("Reconhecimento de voz não suportado neste navegador");
      return;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError("Reconhecimento de voz não disponível");
      return;
    }

    try {
      // Limpar estado anterior
      setError(null);
      setTranscript("");
      lastTranscriptRef.current = "";
      processedResultsRef.current.clear();

      // Criar nova instância
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "pt-BR";

      // Handler de resultados
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const previousFinal = lastTranscriptRef.current;
        let finalTranscript = previousFinal;
        let interimTranscript = "";

        // Processar apenas resultados novos (a partir do resultIndex)
        // Isso evita processar resultados já processados anteriormente
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcript = result[0].transcript.trim();

          if (result.isFinal) {
            // Resultados finais: a API envia o texto completo desde o início
            // Precisamos extrair apenas a parte nova comparando com o que já temos
            if (previousFinal && transcript.startsWith(previousFinal)) {
              // Extrair apenas o texto novo
              const newText = transcript.substring(previousFinal.length).trim();
              if (newText) {
                finalTranscript = previousFinal + " " + newText;
              } else {
                // Nenhum texto novo, manter o anterior
                finalTranscript = previousFinal;
              }
            } else {
              // Primeiro resultado ou resultado que não começa com o texto anterior
              // (pode acontecer se o reconhecimento reiniciou)
              finalTranscript = transcript;
            }
          } else {
            // Resultados intermediários: contêm todo o texto desde o início
            // Usar apenas o último resultado intermediário
            interimTranscript = transcript;
          }
        }

        // Atualizar o texto final acumulado apenas se mudou
        const hasNewFinal = finalTranscript !== previousFinal;
        if (hasNewFinal) {
          lastTranscriptRef.current = finalTranscript;
          
          // Notificar callback apenas quando há novos resultados finais
          if (onTranscriptUpdate) {
            onTranscriptUpdate(finalTranscript);
          }
        }

        // Para exibição: combinar texto final + parte nova do intermediário
        let displayText = finalTranscript;
        if (interimTranscript) {
          // Se o intermediário começa com o texto final, pegar apenas a parte nova
          if (finalTranscript && interimTranscript.startsWith(finalTranscript)) {
            const newPart = interimTranscript.substring(finalTranscript.length).trim();
            if (newPart) {
              displayText = finalTranscript + " " + newPart;
            }
          } else if (!finalTranscript) {
            // Se não há texto final ainda, usar o intermediário
            displayText = interimTranscript;
          }
        }

        setTranscript(displayText);

        // Resetar timer de silêncio quando há atividade
        resetSilenceTimer();
      };

      // Handler de erros
      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error("Erro de reconhecimento:", event.error, event.message);

        let errorMessage = "Erro ao processar áudio";

        switch (event.error) {
          case "no-speech":
            errorMessage = "Nenhuma fala detectada. Tente novamente.";
            break;
          case "audio-capture":
            errorMessage =
              "Não foi possível acessar o microfone. Verifique as permissões.";
            break;
          case "not-allowed":
            errorMessage =
              "Permissão de microfone negada. Permita o acesso nas configurações do navegador.";
            break;
          case "network":
            errorMessage = "Erro de rede. Verifique sua conexão.";
            break;
          case "aborted":
            // Ignorar erros de aborto (quando o usuário para manualmente)
            return;
          default:
            errorMessage = `Erro: ${event.message || event.error}`;
        }

        setError(errorMessage);
        stopRecording();
      };

      // Handler de fim
      recognition.onend = () => {
        setIsRecording(false);
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      };

      // Handler de início
      recognition.onstart = () => {
        setIsRecording(true);
        setError(null);
        resetSilenceTimer();
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Erro desconhecido ao iniciar gravação";
      setError(errorMessage);
      console.error("Erro ao iniciar gravação:", err);
    }
  }, [isSupported, onTranscriptUpdate, resetSilenceTimer, stopRecording]);

  const clearTranscript = useCallback(() => {
    setTranscript("");
    lastTranscriptRef.current = "";
    setError(null);
  }, []);

  return {
    isRecording,
    transcript,
    error,
    isSupported,
    startRecording,
    stopRecording,
    clearTranscript,
  };
}

