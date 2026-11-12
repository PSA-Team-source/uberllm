#!/bin/sh
# Make an image with curl on UberLLM and save it as image.png.
#   export UBERLLM_API_KEY=ull_...
#   sh image.sh "a red bicycle on a white background"
# Needs jq (https://jqlang.org) and base64.
set -eu
PROMPT="${1:-a red bicycle on a white background, studio photo}"
BODY=$(jq -n --arg p "$PROMPT" '{
  model: "black-forest-labs/flux.2-klein-4b",
  prompt: $p,
  size: "1024x1024",
  response_format: "b64_json",
  max_cost: 0.10
}')
curl -sS https://api.uberllm.dev/v1/images/generations \
  -H "Authorization: Bearer $UBERLLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY" > image.json
if jq -e .error image.json >/dev/null; then jq .error image.json; exit 1; fi
jq -r '.data[0].b64_json' image.json | base64 -d > image.png
echo "saved image.png, cost \$$(jq -r '.usage.cost_usd' image.json)"
rm image.json
