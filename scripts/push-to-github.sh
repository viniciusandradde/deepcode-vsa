#!/bin/bash
# Script para fazer push do projeto para GitHub

set -e

REPO_URL="${1:-}"

if [ -z "$REPO_URL" ]; then
    echo "❌ Erro: URL do repositório GitHub não fornecida"
    echo ""
    echo "Uso:"
    echo "  ./scripts/push-to-github.sh https://github.com/USUARIO/deepcode-vsa.git"
    echo ""
    echo "Ou com SSH:"
    echo "  ./scripts/push-to-github.sh git@github.com:USUARIO/deepcode-vsa.git"
    exit 1
fi

echo "🚀 Configurando remote GitHub..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

echo "✅ Remote configurado: $REPO_URL"
echo ""

echo "📤 Fazendo push para GitHub..."
git push -u origin main

echo ""
echo "✅ Push concluído com sucesso!"
echo ""
echo "Repositório: $REPO_URL"
