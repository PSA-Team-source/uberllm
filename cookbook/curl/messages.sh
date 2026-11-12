#!/bin/sh
# Anthropic Messages format with curl on UberLLM: Claude or any other model.
#   export UBERLLM_API_KEY=ull_...
#   sh messages.sh
set -eu
curl -sS https://api.uberllm.dev/v1/messages \
  -H "x-api-key: $UBERLLM_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-haiku-4.5",
    "max_tokens": 256,
    "messages": [{"role": "user", "content": "Say hello in one sentence."}]
  }'
echo
