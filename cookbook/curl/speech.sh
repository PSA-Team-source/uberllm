#!/bin/sh
# Text to speech, then back to text, with curl on UberLLM.
#   export UBERLLM_API_KEY=ull_...
#   sh speech.sh "Your order has shipped."
set -eu
TEXT="${1:-Your order has shipped and will arrive on Friday.}"
curl -sS https://api.uberllm.dev/v1/audio/speech \
  -H "Authorization: Bearer $UBERLLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"venice/kokoro-tts\", \"voice\": \"af_heart\", \"input\": \"$TEXT\"}" \
  -o speech.mp3
echo "saved speech.mp3"

curl -sS https://api.uberllm.dev/v1/audio/transcriptions \
  -H "Authorization: Bearer $UBERLLM_API_KEY" \
  -F model=venice/whisper-large-v3 \
  -F file=@speech.mp3
echo
