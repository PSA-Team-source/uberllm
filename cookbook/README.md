# UberLLM Cookbook

Runnable examples for calling [UberLLM](https://uberllm.dev) from the SDKs and
frameworks people already use: OpenAI and Anthropic SDKs, LangChain, LlamaIndex,
LiteLLM, Pydantic AI, CrewAI, Instructor, DSPy, the Vercel AI SDK, Mastra, Go,
Rust, Java (Spring AI), .NET and curl. Also images, video, music and speech.

UberLLM is one API key for chat, image, video, music and speech models. It speaks
the OpenAI and the Anthropic wire formats, so the change in each example is the
base URL and the key:

| Format | Base URL |
|---|---|
| OpenAI (`/chat/completions`, `/responses`, images, video, audio) | `https://api.uberllm.dev/v1` |
| Anthropic (`/v1/messages`) | `https://api.uberllm.dev` |

Models are sold by third-party providers, usually below list price. Live prices
per model: <https://uberllm.dev/models>. A request that fails is not billed.

## Setup

1. Sign in at <https://uberllm.dev>, add credit (prepaid, from $5) and create a key
   under **Dashboard → API keys**. Keys start with `ull_`.
2. Put it in your environment, never in code:

   ```sh
   export UBERLLM_API_KEY=ull_...
   ```

Every example reads `UBERLLM_API_KEY` and sets the UberLLM base URL in code, so an
`OPENAI_BASE_URL` or `OPENAI_API_KEY` in your shell is never used by mistake.
Most examples take `UBERLLM_MODEL` to try another model; the default is
`deepseek/deepseek-v4-flash`.

## Examples

Every example below was run against the live API on 2026-11-12 with the
library versions listed under [Tested with](#tested-with).

### Python

| Example | What it shows |
|---|---|
| [`python/openai/chat.py`](python/openai/chat.py) | OpenAI SDK chat completion, token counts and `usage.cost_usd` |
| [`python/openai/stream.py`](python/openai/stream.py) | Streaming, with usage and cost in the last chunk |
| [`python/openai/tools.py`](python/openai/tools.py) | Tool calling, the full call → run → answer loop |
| [`python/openai/structured_output.py`](python/openai/structured_output.py) | `chat.completions.parse` into a Pydantic model |
| [`python/openai/responses_api.py`](python/openai/responses_api.py) | The Responses API, multi-turn (stateless) |
| [`python/openai/vision.py`](python/openai/vision.py) | Ask about a picture: link or local file |
| [`python/openai/routing.py`](python/openai/routing.py) | Price cap (`provider.max_price`), fallback models, tags, balance |
| [`python/openai/list_models.py`](python/openai/list_models.py) | Cheapest tool-capable models from `GET /v1/models` |
| [`python/anthropic/messages.py`](python/anthropic/messages.py) | Anthropic SDK: a reply and a stream |
| [`python/anthropic/tools.py`](python/anthropic/tools.py) | Anthropic SDK tool use loop |
| [`python/langchain/chat.py`](python/langchain/chat.py) | LangChain `ChatOpenAI`: invoke, stream, tools, structured output |
| [`python/langchain/agent.py`](python/langchain/agent.py) | LangChain `create_agent` with tools |
| [`python/llamaindex/chat.py`](python/llamaindex/chat.py) | LlamaIndex `OpenAILike`: complete, chat, stream, `FunctionAgent` |
| [`python/litellm/chat.py`](python/litellm/chat.py) | LiteLLM `openai/` prefix, streaming, Router with fallback, proxy config |
| [`python/pydantic-ai/agent.py`](python/pydantic-ai/agent.py) | Pydantic AI agent with a tool and a typed result |
| [`python/instructor/extract.py`](python/instructor/extract.py) | Instructor: validated extraction with retries |
| [`python/dspy/program.py`](python/dspy/program.py) | DSPy signature + `ChainOfThought` |
| [`python/crewai/crew.py`](python/crewai/crew.py) | CrewAI: two agents, two tasks |
| [`python/media/image_generate.py`](python/media/image_generate.py) | Make an image, with a cost ceiling (`max_cost`) |
| [`python/media/image_edit.py`](python/media/image_edit.py) | Edit a picture, with fallback models |
| [`python/media/video.py`](python/media/video.py) | Video job: price check, start, poll, download |
| [`python/media/music.py`](python/media/music.py) | Music job |
| [`python/media/speech.py`](python/media/speech.py) | Text to speech and speech to text |

```sh
cd python
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python openai/chat.py
```

### TypeScript

| Example | What it shows |
|---|---|
| [`typescript/openai/chat.ts`](typescript/openai/chat.ts) | OpenAI Node SDK: reply, cost, stream |
| [`typescript/openai/tools.ts`](typescript/openai/tools.ts) | Tool calling loop |
| [`typescript/anthropic/messages.ts`](typescript/anthropic/messages.ts) | Anthropic TypeScript SDK: reply and stream |
| [`typescript/vercel-ai-sdk/provider.ts`](typescript/vercel-ai-sdk/provider.ts) | UberLLM provider via `@ai-sdk/openai-compatible` |
| [`typescript/vercel-ai-sdk/generate.ts`](typescript/vercel-ai-sdk/generate.ts) | `generateText`, `streamText`, tools, `Output.object` |
| [`typescript/vercel-ai-sdk/image.ts`](typescript/vercel-ai-sdk/image.ts) | `generateImage` |
| [`typescript/langchain/chat.ts`](typescript/langchain/chat.ts) | LangChain.js: invoke, stream, tools, structured output |
| [`typescript/mastra/agent.ts`](typescript/mastra/agent.ts) | Mastra agent with a tool |

```sh
cd typescript
npm install
npx tsx openai/chat.ts
```

For the Vercel AI SDK there is also a ready provider package:
[`ai-sdk-provider-uberllm`](https://github.com/PSA-Team-source/ai-sdk-provider-uberllm).
For LangChain (Python): [`langchain-uberllm`](https://github.com/PSA-Team-source/langchain-uberllm).

### Other languages

| Example | Run |
|---|---|
| [`go/openai-go`](go/openai-go/main.go): official `openai-go/v3`, reply, stream, tool loop | `cd go/openai-go && go run .` |
| [`rust/async-openai`](rust/async-openai/src/main.rs): reply, stream, tool loop | `cd rust/async-openai && cargo run` |
| [`java/spring-ai`](java/spring-ai): Spring AI `ChatClient`, stream, `@Tool`, typed entity | `cd java/spring-ai && mvn spring-boot:run` |
| [`dotnet/openai-dotnet`](dotnet/openai-dotnet/Program.cs): official OpenAI .NET SDK, reply, stream, tool loop | `cd dotnet/openai-dotnet && dotnet run` |
| [`curl/`](curl): chat, stream, Anthropic format, models + balance, image, video, speech | `sh curl/chat.sh` |

## Good to know

- **Cost of each call.** Chat replies carry `usage.cost_usd` (US dollars), streamed
  ones in the last chunk. Media answers and jobs carry it too, and every request
  is listed with its cost in **Dashboard → Activity**.
- **Price ceilings.** `provider.max_price` (chat, per 1M tokens) and `max_cost`
  (image, video, music, speech, per request). A request that would cost more is
  refused with nothing charged. See [`routing.py`](python/openai/routing.py).
- **Reasoning models.** Some models (DeepSeek V4 Flash among them) think before
  answering on the OpenAI format. Don't set a tiny `max_tokens` or the thinking
  can use it up. On the Anthropic format they only think when you send `thinking`.
- **No embeddings endpoint.** UberLLM serves chat, image, video, music and speech.
  For RAG, pair it with any embedding model.
- **Errors** are plain JSON with a `code` and a message that says what to do:
  <https://uberllm.dev/docs/errors>.

## Tested with

Python 3.12: openai 3.3.0, anthropic 2.8.0, langchain-openai 1.7.4, langchain-core 1.8.0,
llama-index-llms-openai-like 0.8.1, litellm 1.109.1, pydantic-ai-slim 2.38.0,
instructor 1.17.0, dspy 3.5.0, crewai 1.15.40. Node 22: openai 7.55, @anthropic-ai/sdk 1.8,
ai 7.0, @ai-sdk/openai-compatible 3.0, @langchain/openai 1.8, @mastra/core 1.82.
Go 1.26 with openai-go v3.98.0. Rust 1.97 with async-openai 0.43. Java 21 with
Spring Boot 4.1.2 and Spring AI 2.0.2. .NET 10 with OpenAI 2.15.0.

If an example stops working with a newer library version, please open an issue.

## Links

- Docs: <https://uberllm.dev/docs> · OpenAPI spec: <https://uberllm.dev/openapi.json>
- Models and live prices: <https://uberllm.dev/models>
- MCP server, Claude Code / Codex plugins and the agent skill: [the repository root](../README.md)
- Support: support@uberllm.dev

## License

MIT, see [LICENSE](../LICENSE).
