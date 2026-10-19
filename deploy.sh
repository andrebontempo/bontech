#!/bin/bash
set -e

echo "===================================================="
echo "🚀 Iniciando Deploy Automático — Bontech (Flask)"
echo "===================================================="

cd "$(dirname "$0")"

git config --global --add safe.directory /opt/docker/bontech 2>/dev/null || true
git remote set-url origin https://github.com/andrebontempo/bontech.git 2>/dev/null || true

echo "📥 [1/5] Baixando atualizações do GitHub (main)..."
git fetch origin main
git reset --hard origin/main

echo "🧹 [2/5] Removendo arquivos não rastreados (mantendo .env e data/)..."
git clean -fd -e .env -e data/

# Cria o .env inicial caso ainda não exista
if [ ! -f ".env" ]; then
  echo "⚠️ Arquivo .env não encontrado. Copiando de .env.example..."
  cp .env.example .env
fi

echo "🌐 [3/5] Verificando rede externa Docker proxy..."
docker network create proxy 2>/dev/null || true

echo "🐳 [4/5] Substituindo containers antigos e subindo Flask + PostgreSQL..."
docker compose down --remove-orphans
docker compose up -d --build --remove-orphans

echo "===================================================="
echo "✨ [5/5] Deploy concluído com sucesso!"
echo "===================================================="
