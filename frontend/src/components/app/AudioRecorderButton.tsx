"use client";

import { useEffect } from "react";
import clsx from "clsx";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";

interface AudioRecorderButtonProps {
  onTranscript?: (transcript: string) => void;
  onError?: (error: string) => void;
  silenceTimeout?: number;
  className?: string;
}

export function AudioRecorderButton({
  onTranscript,
  onError,
  silenceTimeout = 3000,
  className,
}: AudioRecorderButtonProps) {
  const {
    isRecording,
    transcript,
    error,
    isSupported,
    startRecording,
    stopRecording,
    clearTranscript,
  } = useAudioRecorder(onTranscript, silenceTimeout);

  // Notificar erros via callback
  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  // Limpar transcrição quando parar de gravar
  useEffect(() => {
    if (!isRecording && transcript) {
      // Pequeno delay para garantir que a transcrição final foi processada
      const timer = setTimeout(() => {
        clearTranscript();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isRecording, transcript, clearTranscript]);

  const handleToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  if (!isSupported) {
    return (
      <button
        disabled
        className={clsx(
          "flex h-12 w-12 items-center justify-center rounded-lg border-2 border-slate-400 bg-slate-100 text-slate-500 cursor-not-allowed",
          className
        )}
        title="Reconhecimento de voz não suportado"
        aria-label="Reconhecimento de voz não suportado"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      className={clsx(
        "relative flex h-12 w-12 items-center justify-center rounded-lg border-2 transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white",
        isRecording
          ? "border-vsa-orange-600 bg-vsa-orange/20 text-vsa-orange-700 shadow-vsa-orange focus:ring-vsa-orange animate-pulse"
          : "border-slate-400 bg-white text-slate-600 hover:border-vsa-orange hover:bg-vsa-orange/5 hover:text-vsa-orange-600 focus:ring-vsa-orange/40",
        className
      )}
      aria-label={isRecording ? "Parar gravação" : "Iniciar gravação"}
      title={isRecording ? "Parar gravação" : "Iniciar gravação de voz"}
    >
      {/* Ícone de microfone */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-5 w-5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        {isRecording ? (
          // Ícone de stop quando gravando
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        ) : (
          // Ícone de microfone quando não gravando
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        )}
      </svg>

      {/* Indicador de gravação ativa */}
      {isRecording && (
        <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-500 animate-ping" />
      )}
    </button>
  );
}
