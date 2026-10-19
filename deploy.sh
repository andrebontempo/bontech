#!/bin/bash
set -e

echo "===================================================="
echo "🚀 Iniciando Deploy Automático — Bontech (Flask)"
echo "===================================================="

cd "$(dirname "$0")"

git config --global --add safe.directory /opt/docker/bontech 2>/dev/null || true
git remote set-url origin https://github.com/andrebontempo/bontech.git 2>/dev/null || true

echo "📥 [1/6] Baixando atualizações do GitHub (main)..."
git fetch origin main
git reset --hard origin/main

echo "🧹 [2/6] Removendo resíduos do antigo WordPress (pasta data/ e .env legado)..."
if [ -d "data" ]; then
  echo "🗑️ Removendo diretório legado ./data (antigo WordPress/MariaDB)..."
  rm -rf ./data 2>/dev/null || sudo rm -rf ./data 2>/dev/null || docker run --rm -v "$(pwd):/work" alpine rm -rf /work/data || true
fi

if [ -f ".env" ] && grep -q "WORDPRESS_" ".env" 2>/dev/null; then
  echo "🔄 Substituindo .env legado do WordPress pelo novo .env do Flask..."
  cp -f .env.example .env
fi

# Cria o .env inicial caso ainda não exista
if [ ! -f ".env" ]; then
  echo "⚠️ Arquivo .env não encontrado. Copiando de .env.example..."
  cp .env.example .env
fi

echo "🧹 [3/6] Limpando arquivos não rastreados (mantendo apenas .env)..."
git clean -fd -e .env

echo "🌐 [4/6] Verificando rede externa Docker proxy..."
docker network create proxy 2>/dev/null || true

echo "🐳 [5/6] Substituindo containers e subindo Flask + PostgreSQL..."
docker rm -f bontech_app bontech-app bontech_db bontech-db bontech_wordpress wordpress 2>/dev/null || true
docker compose down --remove-orphans
docker compose up -d --build --remove-orphans

echo "===================================================="
echo "✨ [6/6] Deploy e limpeza concluídos com sucesso!"
echo "===================================================="
