---
name: uberllm
description: Use when the user wants cheaper API access to Claude, GPT, Gemini, DeepSeek, GLM, Qwen, Kimi or other chat models, or to image, video, music and speech models; to set up UberLLM in Claude Code, Codex, Cursor or any OpenAI- or Anthropic-compatible tool or SDK; to pick a model and check its live price; to make an image, video or voice-over; or to fix an UberLLM error. UberLLM is an OpenAI- and Anthropic-compatible API marketplace where a request costs what its provider charged and UberLLM adds no fee on requests.
---

# UberLLM

> This copy is kept in step with https://uberllm.dev/SKILL.md, which is the
> latest version. If the two differ, follow the one on the site.
>
> Installed as a plugin (Claude Code or Codex)? The plugin already adds the
> UberLLM MCP server. It needs the user's key: in Claude Code the plugin asks
> for it (change it later with `claude plugin configure uberllm`); in Codex,
> set `UBERLLM_API_KEY` in the environment Codex starts from. Without a key,
> get one with step 1 below.

One API key for chat, image, video and music models. Each request is sent to an available third-party provider
for the requested model. If the provider fails before it starts answering, the request is retried, and requests
that still fail are not billed. A request costs what its provider charged for it. UberLLM adds
no fee. For a hard limit, send `provider.max_price` (chat) or `"max_cost"` (media). Each request is listed with its cost in Dashboard > Activity. Credit is prepaid.

- OpenAI-compatible base URL: `https://api.uberllm.dev/v1`
- Anthropic-compatible base URL (Claude Code, Anthropic SDK): `https://api.uberllm.dev`
- Keys look like `ull_…`. Treat a key like a password: never print it in full, never commit it, store it in
  the user's environment or the tool's own settings file.

## 1. Get a key — the user approves in their browser

Do not ask the user for a password; UberLLM has none. Link a key with one browser approval:

1. `POST https://api.uberllm.dev/api/v1/cli/link/start` with JSON `{"client_name": "<your agent name>", "client_platform": "<os>"}`.
   The answer has `link_code`, `device_code` (secret — keep it to yourself), `verification_url`,
   `expires_in` (seconds) and `interval` (seconds).
2. Tell the user, in plain words: "Open <verification_url>, sign in (Google, or an emailed 6-digit code — it
   creates the account if they have none), check the code says <link_code>, and press Approve."
3. Every `interval` seconds: `POST https://api.uberllm.dev/api/v1/cli/link/poll` with `{"device_code": "<device_code>"}`.
   Wait in the FOREGROUND (one blocking loop, up to `expires_in`), not as a background job, so you carry on
   the moment they approve.
   - `{"status":"pending"}` → keep waiting.
   - `{"status":"approved","api_key":"ull_…","base_url":"…"}` → done; the key is shown exactly once.
   - `denied` or `expired` → stop and tell the user; start over if they want.
   - HTTP 429 `slow_down` → you polled faster than `interval`; wait and continue.

The user does not create or copy a key; this link is the whole key setup. (Developers who want a key for
another tool can make one at https://uberllm.dev/dashboard/keys.)

## 2. Make sure there is credit

New accounts start at $0. Check with a 1-token call (step 4). If it answers HTTP 402 `insufficient_credits`,
ask the user to add credit at https://uberllm.dev/dashboard/credits, then try again. Usage and spend:
https://uberllm.dev/dashboard/activity.

## 3. Set up the tool

**Claude Code** — skip step 1 and run the installer; it does the browser connection itself and needs
no key (run it in the foreground and show the user the link it prints). Ask the user which they want:

- Every project on this computer: `curl -fsSL https://uberllm.dev/install/claude-code.sh | sh`
- Only the current project (others stay on their Anthropic plan):
  `curl -fsSL https://uberllm.dev/install/claude-code.sh | sh -s -- --project` (run it inside the project, or put the
  folder after `--project`). It writes `<project>/.claude/settings.local.json`. On a computer where Claude Code
  has never been set up, use the every-project install: a project's settings apply only once the folder is trusted.

The installer saves the key to a file only the user can read (`~/.uberllm/key`, or `~/.uberllm/key-<folder>-<n>`
for one project; mode 600) and writes `ANTHROPIC_BASE_URL` plus `"apiKeyHelper": "cat <that file>"` into the
settings file, backing up the old file. The key is never written into a settings file. It then verifies a live
call. If you already linked a key in step 1, pass it instead:
`curl -fsSL https://uberllm.dev/install/claude-code.sh | UBERLLM_API_KEY="<key>" sh`. Then tell the user to restart
Claude Code (quit, run `claude` again). Undo: the same command with `sh -s -- --uninstall` (add `--project` for
a project install). Full guide: https://uberllm.dev/docs/claude-code

Setting by hand, `.claude/settings.local.json` (one project) or `~/.claude/settings.json` (all projects):

```json
{
  "apiKeyHelper": "cat ~/.uberllm/key",
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.uberllm.dev",
    "ANTHROPIC_MODEL": "deepseek/deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek/deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek/deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek/deepseek-v4-flash",
    "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek/deepseek-v4-pro"
  }
}
```

- **Models.** With no model variables, Claude Code asks for its own Claude names (`opus`, `sonnet`, `haiku`,
  `claude-opus-5-5`…) and UberLLM serves those Claude models. To run any other model, map every slot as above:
  `ANTHROPIC_DEFAULT_OPUS_MODEL`, `_SONNET_`, `_HAIKU_` (also used for background work), `CLAUDE_CODE_SUBAGENT_MODEL`
  and `ANTHROPIC_MODEL` (the starting model). A slot left unset still asks for Claude, at Claude prices.
- **Which setting wins**: `claude --settings` > `.claude/settings.local.json` > `.claude/settings.json` >
  `~/.claude/settings.json`; a settings `env` value beats the same shell variable in most sessions. The key:
  `ANTHROPIC_AUTH_TOKEN`, then `ANTHROPIC_API_KEY`, then `apiKeyHelper`. The model: `/model` > `--model` >
  `ANTHROPIC_MODEL` > the `model` setting. So have the user remove every `ANTHROPIC_*` variable from their shell
  and shell profile.
- **Context and compaction.** Claude Code assumes 200,000 tokens for any non-Claude model. If the model really has
  1M (its page at https://uberllm.dev/models/<id> shows the context), add `[1m]` to the id, e.g.
  `"ANTHROPIC_MODEL": "deepseek/deepseek-v4-pro[1m]"`; for another size set `CLAUDE_CODE_MAX_CONTEXT_TOKENS`. When it
  compacts: the `autoCompactWindow` setting (100000–1000000 tokens) or `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (1–100).
- **What changes.** The claude.ai login is not used, so claude.ai connectors, `/schedule` and Remote Control are
  unavailable in these sessions. The cost Claude Code shows is its own list-price estimate, not the bill: spend is
  at https://uberllm.dev/dashboard/activity. For the balance under the prompt:
  `curl -fsSL https://uberllm.dev/install/statusline.sh | sh -s -- --install` (reads `GET /v1/balance`).
- **Data.** Everything the session reads is sent to third-party model providers. Tell the user not to use it in a
  repository that holds secrets, credentials or customer data.

**Any OpenAI-compatible tool or SDK** (OpenAI SDK, Cursor, Cline, Continue, OpenCode, Aider, LangChain, LiteLLM…):
base URL `https://api.uberllm.dev/v1`, API key = the `ull_` key, model = an id from step 4.

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.uberllm.dev/v1", api_key=os.environ["UBERLLM_API_KEY"])
client.chat.completions.create(model="deepseek/deepseek-v4-flash", messages=[{"role": "user", "content": "hi"}])
```

**Anthropic SDK**: `Anthropic(base_url="https://api.uberllm.dev", api_key=<key>)`.

## 4. Pick a model

`GET https://api.uberllm.dev/v1/models` (header `Authorization: Bearer <key>`) lists every model that can be served right
now: chat first, then image, video and music. Each entry has `type`, `endpoints` (where to send it) and
`pricing`. Narrow it with `?type=chat`, `image`, `video` or `music`. `GET https://api.uberllm.dev/v1/models/<id>` gives one
model; for a media model its `parameters` is a JSON Schema of the request body (clip lengths, resolutions, aspect
ratios, sizes, and which source picture it needs). Read it before a media request. Ids are `vendor/model`.
Each model also says `available` (false = nobody serves it right now, so a call gets `no_available_provider`),
`input_modalities` (`"image"` = it takes a picture) and `nsfw` (true = an adult or uncensored model; skip it for
business work).
Good defaults:

- Strongest for coding and agents: `anthropic/claude-opus-5.5`
- Balanced: `anthropic/claude-sonnet-5`
- Cheap and fast: `deepseek/deepseek-v4-flash`, `z-ai/glm-5.3`

Live prices per model: https://uberllm.dev/#models (each model has a page at https://uberllm.dev/models/<id>). A 1-token test:
`curl https://api.uberllm.dev/v1/chat/completions -H "Authorization: Bearer <key>" -H 'content-type: application/json' -d '{"model":"deepseek/deepseek-v4-flash","max_tokens":1,"messages":[{"role":"user","content":"."}]}'`

Balance: `GET https://api.uberllm.dev/v1/balance` → `{"balance_usd", "held_usd", "available_usd"}` (held = set aside for
requests still running).

On any request (chat, image, video, music, speech):

- `"models": ["<id>", "<id>"]` = fallback models, tried in order only when the one before cannot be served right
  now; a bad request or a money refusal is answered at once. At most 5 in `model` + `models`. The reply's
  `model` names the one that answered.
- `"model": "best-price:<job>"` or `"fastest:<job>"` (job = `chat`, `image`, `image-edit`, `text-to-video`,
  `image-to-video`, `music`, `speech`, `transcription`) lets UberLLM pick the cheapest, or quickest measured, model
  that is available right now; on a media route a pick that turns out to have nobody serving it moves on to the
  next one (up to 3). When none is, the answer is `503 no_available_provider`.
  `GET https://api.uberllm.dev/v1/models/aliases` shows what each stands for now.
- `"metadata": {"project": "x"}` (up to 16 text values) tags the request in Activity and the CSV export;
  filter with `?tag=project:x`. It is never sent to a model.
- Chat: `"provider": {"max_price": {"prompt": 1, "completion": 3}}` (US dollars per million tokens, what
  you are billed at) is a hard ceiling; `"provider": {"sort": "latency"}`, `"deny": ["<provider>"]`, `"allow"`, `"order"`
  also work. An option that cannot be applied answers `400 unsupported_routing_option`.
- Chat replies say what they cost: `usage.cost_usd` (US dollars, what you are billed) in the answer, in the last
  usage chunk of a stream (`message_delta` on `/v1/messages`), and in the `X-UberLLM-Cost-USD` header of an
  answer that is not streamed. One exception: a slow answer that is not streamed starts with spaces to keep the
  connection open, and then only the body field carries the cost.
- An image, video, music, speech or transcription model sent to `/v1/chat/completions` or `/v1/messages` (or a
  chat model sent to a media route) answers `400 wrong_endpoint` naming the right route. Nothing is charged.

## 5. Make an image, a video, music or speech

Same key, same balance. Image, video, music and speech models are listed at https://uberllm.dev/?type=video#models (and
`?type=image`, `?type=music`, `?type=audio`) with their price per picture, second, track, 1K characters or minute.
Which route, and which field carries a source picture:

| You want | POST | Source picture |
|---|---|---|
| New image | `/v1/images/generations` | none |
| Edited picture (model id usually ends in `-edit`) | `/v1/images/edits` | `image` (also `image_url`, `input_images: [...]`, `images: [{"image_url": ...}]`, or multipart `image` file) |
| Video from a prompt | `/v1/video/generations` | none |
| Video from a picture (`…-image-to-video`) | `/v1/video/generations` | `image_url` = first frame (`end_image_url` = last frame, where offered) |
| Video from reference pictures (`…-reference-to-video`) | `/v1/video/generations` | `input_images: [{"url": ..., "role": "reference"}]` |
| Text about a picture | `/v1/chat/completions` | an `image_url` part in `messages[].content` |
| Speech from text | `/v1/audio/speech` | none (text in `input`) |
| Text from a recording | `/v1/audio/transcriptions` | none (multipart `file`) |

A picture is an `https://` link, a `data:image/png;base64,…` URI, or plain base64 (PNG, JPEG, WebP); at most 8;
keep the request under 10 MB or send links.

**Image** — one call, the picture comes back in the answer:

```sh
curl https://api.uberllm.dev/v1/images/generations -H "Authorization: Bearer $UBERLLM_API_KEY" -H 'content-type: application/json' \
  -d '{"model": "<image model id>", "prompt": "a red apple on a white table", "n": 1, "size": "1024x1024"}'
curl https://api.uberllm.dev/v1/images/edits -H "Authorization: Bearer $UBERLLM_API_KEY" -H 'content-type: application/json' \
  -d '{"model": "<edit model id>", "prompt": "make the sky a sunset", "image": "https://example.com/photo.png"}'
```

The answer is `{"data": [{"url": "https://api.uberllm.dev/v1/media/artifacts/<id>/0"}], "usage": {"cost_usd": …}}` on both
routes: `response_format` defaults to `url`; send `"response_format": "b64_json"` to get the picture inline.
Download the url with the same `Authorization` header within about 15 minutes (a picture the model sent inline
comes back as a `https://api.uberllm.dev/v1/files/file_…/content` link instead, kept 24 hours, which also works as an edit source).

**Video** (and **music**: the same steps with `/v1/music/generations`) — start a job, check on it, download:

1. `POST https://api.uberllm.dev/v1/video/generations` with header `Idempotency-Key: <a new UUID>` and
   `{"model": "<video model id>", "prompt": "...", "duration_seconds": 5}` (plus `"image_url": "https://…"` for an
   image-to-video model, or `"input_images"` for a reference model; `"aspect_ratio"` defaults to `16:9` there, and a
   model that needs a picture answers `400 image_required` without one)
   → HTTP 202 `{"id": "<job id>", "status": "queued", "max_cost_usdc": "...", "poll_url": "/v1/video/generations/<job id>"}`.
   `max_cost_usdc` (millionths of a dollar) is held from the balance while it runs and is the most the job is billed;
   you pay what the provider charged for it. Sending the
   same request again with the same `Idempotency-Key` (24 h) returns the same job, never a second charge.
2. `GET https://api.uberllm.dev/v1/video/generations/<job id>` every 5–10 seconds, or skip polling with `"callback_url"` (below). HTTP 202 while
   `queued` / `running` (with `progress` 0–1); HTTP 200 once it ends: `succeeded`, `failed`, `canceled` or
   `expired`. Those six are the only statuses. A video usually takes 1–5 minutes.
3. On `succeeded`: download `results[0].url` (`https://api.uberllm.dev/v1/media/artifacts/<job id>/0`) with the key within
   about 3 hours; after that it answers 404 `artifact_expired`.

The job's `estimated_cost_usd` is the listed price, the same as `validate` and `/v1/quote` give.
You pay the real cost when it is done (`usage.cost_usd` on the finished job and the `X-UberLLM-Cost-USD` header;
also in https://uberllm.dev/dashboard/activity), and the rest of the hold comes back. Right after `succeeded` the job may
show `"usage": {"cost_pending": true, "cost_usd": null}` for a few seconds while the charge comes in (usually under
30 s; after 30 minutes without it the job is billed at its listed price). `failed`, `canceled` and `expired`
cost nothing; on `failed`, `error.retryable` says whether trying again can work. Stop a job:
`DELETE https://api.uberllm.dev/v1/video/generations/<job id>`.

Before spending: add `"validate": true` to any media request to check it and get `cost_usd` (the listed price:
the model's price × seconds or units) and `max_cost_usd` (what is held, the most it is billed) without being charged, and `"max_cost": 0.50` (US dollars) to refuse anything that can cost more (`400 max_cost_too_low`).
A model sent to the wrong path answers 400 `wrong_endpoint` and names the right one; a 402 says how much credit the
job needs.

- **Get a quote:** `POST https://api.uberllm.dev/v1/quote` with the same body → `quote_id` and `cost_usd`. Send the same
  request with `"quote_id"` within 15 minutes and it is billed what the provider charged, at most its `max_cost_usd`. One quote starts one request; other
  settings answer `400 quote_mismatch`.
- **Upload a picture once:** `curl -F file=@photo.png https://api.uberllm.dev/v1/files` → `{"id": "file_…", "url": …}`; put
  the id or url anywhere a source picture goes. Kept 24 hours, 10 MB max.
- **Price cap per unit:** `"provider": {"max_price": 0.05}` (US dollars per image / second / megapixel / request).
- **Your own storage:** `"output_upload_url": "<https presigned PUT link>"` on a video or music job; UberLLM uploads
  the finished file there and the job shows `output_upload.status` (`pending`, `delivered`, `failed`).
- **Get told when it ends:** `"callback_url": "<https link>"` on a video or music job; once it ends and its cost is
  final (never while `cost_pending`), UberLLM POSTs, once, the same JSON as the GET, signed with `UberLLM-Signature: t=…,v1=<hex HMAC-SHA256 of "t.body">`
  using the account's webhook secret (https://uberllm.dev/dashboard/keys), with `UberLLM-Event-Id: <job id>:<status>`.
  Non-2xx answers are retried after 30 s, 2, 10, 30 min and 2 h. The job shows `callback.status`.

Guide: https://uberllm.dev/docs/media

**MCP** — the same image, video, quote, model and balance calls are MCP tools at `https://api.uberllm.dev/mcp` (Streamable
HTTP, the same key). Claude Code:
`claude mcp add --transport http uberllm https://api.uberllm.dev/mcp --header "Authorization: Bearer $KEY"` (KEY = the user's
key). Tools: list_models, get_model, quote, generate_image, edit_image, start_video, get_job, wait_job (waits up to
50 s per call), balance. Guide: https://uberllm.dev/docs/mcp

**Speech** (text to speech): one call, the audio file comes back as the answer:

```sh
curl https://api.uberllm.dev/v1/audio/speech -H "Authorization: Bearer $UBERLLM_API_KEY" -H 'content-type: application/json' \
  -d '{"model": "x-ai/tts-xai-v1", "input": "Hello from UberLLM."}' -o speech.mp3
```

Optional: `voice`, `response_format` (e.g. `mp3`, `wav`), `speed`. Billed per started 1K characters of `input`.

**Transcription** (speech to text): send the recording as a multipart form, the text comes back:

```sh
curl https://api.uberllm.dev/v1/audio/transcriptions -H "Authorization: Bearer $UBERLLM_API_KEY" \
  -F model=venice/whisper-large-v3 -F file=@talk.mp3
```

→ `{"text": "...", "duration": 4.2, "usage": {"cost_usd": …}}`. Optional: `language`, `prompt`, `temperature`,
`response_format` (`json`, or `text` / `srt` / `vtt` for plain text). Billed per minute of audio. Files up to 40 MB.
Our own fields go in the form too and never reach the model: `-F max_cost=0.10`, `-F "metadata[project]=x"`, `-F validate=true`.

Both work with the OpenAI SDK (`client.audio.speech.create`, `client.audio.transcriptions.create`) with
base_url https://api.uberllm.dev/v1. Every answer carries what it cost in the `X-UberLLM-Cost-USD` header and its id in
`X-Request-Id` (also listed in https://uberllm.dev/dashboard/activity). `"validate": true`, `max_cost`, `metadata` and
`provider.max_price` work as on images. A failed request costs nothing.

## 6. Errors and what to do

| HTTP | code | meaning | do |
|---|---|---|---|
| 401 | `invalid_api_key` / `missing_api_key` | key wrong or revoked | link a new key (step 1) |
| 402 | `insufficient_credits` | balance is empty | user adds credit at https://uberllm.dev/dashboard/credits |
| 402 | `key_spend_cap_exceeded` | this key reached its spending or daily limit | raise it at https://uberllm.dev/dashboard/keys, or wait for the reset |
| 400 | `max_price_exceeded` | nothing sells it within your `provider.max_price` | raise it, or name other `models` |
| 400 | `invalid_request` | the request itself is wrong (message says why) | fix the request; do not retry as-is |
| 404 | `model_not_found` | that model id is not available | pick one from `/v1/models` |
| 429 | `rate_limited` | too many requests | wait `Retry-After` seconds, then retry; `X-RateLimit-Remaining` / `-Reset` are on every answer |
| 503 | `no_available_provider` | no provider can serve that model right now; UberLLM already retried | retry in a minute or pick another model |
| 503 | `service_unavailable` | temporary problem on our side | retry in a few minutes |

Streaming (`"stream": true`) is supported on both APIs. Once a stream has started, a failure is not retried
automatically — retry the request yourself.

## 7. Sell capacity (list the user's provider key)

If the user wants to *sell* inference capacity on a provider key (Together, OpenRouter, DeepSeek, Venice, their own
OpenAI-compatible server…), use the same `ull_…` key from step 1 against `https://api.uberllm.dev/v1/seller`. Only list
capacity the user may resell — never a key for OpenAI, Anthropic or Google. Ask the user to confirm the models and
the discount before listing; nothing goes live until you call `offers/bulk`.

1. Once: `POST /v1/seller/register` `{"display_name": "<name buyers see>"}`.
2. `GET /v1/seller/providers` gives each provider's `base_url`.
3. `POST /v1/seller/discover` `{"base_url": "...", "api_key": "<their provider key>"}` lists the models that key can
   serve, matched to ours (`model_id`; absent = not supported). It uses no provider quota.
4. `POST /v1/seller/offers/bulk` `{"endpoint_url": "...", "api_key": "...", "save_config": true, "offers": [{"model_id":
   "...", "upstream_model": "<server_model>", "match_best": true}]}`. Price is a discount off the list price:
   `"discount_pct": 40` or `"match_best": true` (the deepest live discount). Per-token prices are refused. Each
   model gets one small test request; one that fails comes back with `error` and is not listed. At most 50 per call.
5. Watch it: `GET /v1/seller/offers` (price, health, rank), `GET /v1/seller/health-log`,
   `GET /v1/seller/earnings?range=30d`, `GET /v1/seller/payouts` (owed / on the way / paid; payouts are sent by
   hand in US dollars once $5 is owed or after 72 hours).
6. Change it: `PATCH /v1/seller/offers/{id}` `{"discount_pct": 45}` or `{"status": "paused"}`;
   `POST /v1/seller/offers/{id}/reset-health` after a fix; `DELETE /v1/seller/offers/{id}` removes it and erases the
   stored key.

A `409 duplicate_offer_for_credential` means that key already serves that model at that address — update the
existing offer instead. Never print the user's provider key.
