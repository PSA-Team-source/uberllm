#!/bin/sh
# Chat completion with curl on UberLLM (OpenAI format).
#   export UBERLLM_API_KEY=ull_...
#   sh chat.sh
set -eu
curl -sS https://api.uberllm.dev/v1/chat/completions \
  -H "Authorization: Bearer $UBERLLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-v4-flash",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}]
  }'
echo
# The reply has usage.cost_usd: what the call cost, in US dollars.
