#!/bin/sh
set -e

echo "Starting Airport AI Platform Backend..."

mkdir -p /app/data/sqlite /app/data/faiss /app/data/pdfs /app/data/logs

echo "Waiting for Ollama at ${OLLAMA_BASE_URL:-http://ollama:11434}..."
until curl -sf "${OLLAMA_BASE_URL:-http://ollama:11434}/api/tags" > /dev/null 2>&1; do
  echo "Ollama not ready, retrying in 3s..."
  sleep 3
done
echo "Ollama is ready."

exec "$@"
