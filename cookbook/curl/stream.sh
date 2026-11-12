#!/bin/sh
# Streaming chat (server-sent events) with curl on UberLLM.
# The last data chunk carries usage, including cost_usd.
#   export UBERLLM_API_KEY=ull_...
#   sh stream.sh
set -eu
curl -sS -N https://api.uberllm.dev/v1/chat/completions \
  -H "Authorization: Bearer $UBERLLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek/deepseek-v4-flash",
    "stream": true,
    "messages": [{"role": "user", "content": "Count from 1 to 5."}]
  }'
