#!/bin/sh
# Make a video with curl on UberLLM: price check, start, poll, download.
#   export UBERLLM_API_KEY=ull_...
#   sh video.sh "a paper boat drifting down a rainy street"
# Needs jq (https://jqlang.org). Video models: GET /v1/models?type=video
set -eu
API=https://api.uberllm.dev/v1
AUTH="Authorization: Bearer $UBERLLM_API_KEY"
PROMPT="${1:-a paper boat drifting down a rainy street, cinematic}"
BODY=$(jq -n --arg p "$PROMPT" '{
  model: "fal-ai/veo3.1/lite",
  prompt: $p,
  duration_seconds: 4,
  resolution: "720p",
  aspect_ratio: "16:9",
  audio: false,
  max_cost: 0.50
}')

# 1. Price check: validate=true makes nothing and charges nothing.
curl -sS "$API/video/generations" -H "$AUTH" -H "Content-Type: application/json" \
  -d "$(echo "$BODY" | jq '. + {validate: true}')" | jq '{valid, cost_usd, max_cost_usd}'

# 2. Start. Same Idempotency-Key on a retry = same job, not a second one.
JOB=$(curl -sS "$API/video/generations" -H "$AUTH" -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen 2>/dev/null || date +%s%N)" -d "$BODY")
ID=$(echo "$JOB" | jq -r '.id // empty')
[ -n "$ID" ] || { echo "$JOB"; exit 1; }
echo "job $ID"

# 3. Poll every 8 seconds until it ends.
while :; do
  STATUS_JSON=$(curl -sS "$API/video/generations/$ID" -H "$AUTH")
  STATUS=$(echo "$STATUS_JSON" | jq -r .status)
  echo "  $STATUS"
  case "$STATUS" in queued|running) sleep 8 ;; *) break ;; esac
done
[ "$STATUS" = succeeded ] || { echo "$STATUS_JSON" | jq .error; exit 1; }

# 4. Download with the same key (files are kept about 3 hours).
curl -sS -L -o video.mp4 -H "$AUTH" "$(echo "$STATUS_JSON" | jq -r '.results[0].url')"
echo "saved video.mp4, cost \$$(echo "$STATUS_JSON" | jq -r '.usage.cost_usd')"
