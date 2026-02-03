"use client";

import React, { Component, ReactNode } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="m-4 border-2 border-red-300 bg-red-50 shadow-sm">
          <CardHeader>
            <h2 className="text-lg font-semibold text-slate-900">Algo deu errado</h2>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-900">
              {this.state.error?.message || "Ocorreu um erro inesperado"}
            </p>
            <Button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              variant="outline"
              className="border-red-300 text-slate-900 hover:bg-red-100"
            >
              Recarregar Página
            </Button>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}

