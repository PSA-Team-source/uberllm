#!/bin/sh
# List models and check your balance on UberLLM.
#   export UBERLLM_API_KEY=ull_...
#   sh models.sh            # chat models
#   sh models.sh video      # also: image, music, speech, transcription, all
# Needs jq for the table (https://jqlang.org).
set -eu
TYPE="${1:-chat}"
curl -sS "https://api.uberllm.dev/v1/models?type=$TYPE" \
  -H "Authorization: Bearer $UBERLLM_API_KEY" |
  jq -r '.data[] | select(.available) | [.id, (.pricing | tostring)] | @tsv'

curl -sS https://api.uberllm.dev/v1/balance -H "Authorization: Bearer $UBERLLM_API_KEY"
echo
# Live prices on the web: https://uberllm.dev/models
