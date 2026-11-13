# Next.js chat app on UberLLM (Vercel AI SDK)

[![DeepSeek V4 Flash price on UberLLM](https://api.uberllm.dev/api/v1/public/badge/deepseek/deepseek-v4-flash.svg)](https://uberllm.dev/models/deepseek/deepseek-v4-flash?utm_source=embed&utm_medium=referral&utm_campaign=price-badge)

A streaming chat app: Next.js App Router, the Vercel AI SDK (`useChat` +
`streamText`) and one tool the model can call (it looks up live model prices).
[UberLLM](https://uberllm.dev) is the model provider, through the official
`@ai-sdk/openai-compatible` package.

## Quick start

1. Copy the starter and install:

   ```sh
   npx degit PSA-Team-source/uberllm/starters/nextjs-ai-sdk-chat my-chat
   cd my-chat && npm install
   ```

2. Sign in at <https://uberllm.dev>, add credit (prepaid, accounts start at $0) and
   create a key under **Dashboard → Keys**. Then:

   ```sh
   cp .env.example .env.local   # then paste your key after UBERLLM_API_KEY=
   ```

3. Run it and open <http://localhost:3000>:

   ```sh
   npm run dev
   ```

Ask "What does GPT-5.5 cost per million tokens?" to see the tool run.

## What is in it

| File | What it does |
|---|---|
| [`lib/uberllm.ts`](lib/uberllm.ts) | The UberLLM provider (base URL, key, default model) |
| [`lib/tools.ts`](lib/tools.ts) | The tools the model may call. Add yours here |
| [`app/api/chat/route.ts`](app/api/chat/route.ts) | The chat endpoint: streams the answer, runs tools, up to 5 steps |
| [`app/page.tsx`](app/page.tsx) | The chat screen: messages, tool activity, stop, retry, errors |
| [`smoke.test.mts`](smoke.test.mts) | `npm test` |

## Typed output

The provider sets `supportsStructuredOutputs: true`. That is what makes the SDK
send your schema to the model, so `Output.object` returns data that matches it:

```ts
import { generateText, Output } from 'ai';
import { z } from 'zod';
import { MODEL, uberllm } from '@/lib/uberllm';

const { output } = await generateText({
  model: uberllm(MODEL),
  output: Output.object({ schema: z.object({ city: z.string(), country: z.string() }) }),
  prompt: 'The capital of France.',
});
// output = { city: 'Paris', country: 'France' }
```

Use a model that lists `structured_outputs` under `supported_parameters` in
`GET https://api.uberllm.dev/v1/models`.

## Test

```sh
npm test
```

Without a key it runs the offline checks: the real `/api/chat` handler against a
stand-in for the API. With `UBERLLM_API_KEY` set it also calls the real API (a
fraction of a cent).

## Before you put it on the internet

`/api/chat` spends your credit for anyone who can reach it. Add sign-in or a
rate limit first, and set a spend limit on the key. On Vercel, add
`UBERLLM_API_KEY` under Project → Settings → Environment Variables.

## Good to know

- **Another model.** Set `UBERLLM_MODEL` to any chat model id from
  <https://uberllm.dev/models> that takes tools. The badge above shows the
  default model's current price.
- **Cost.** Each call costs what its provider charged, and a failed call is not
  billed. Every request is listed with its cost in **Dashboard → Activity**. To
  cap what this key can spend, set a spend limit on it in **Dashboard → Keys**.
- **The key only goes to `https://api.uberllm.dev/v1`.** The base URL is set in
  code, so an `OPENAI_BASE_URL` in your shell is not used.
- Errors are plain JSON with a message that says what to do:
  <https://uberllm.dev/docs/errors>.

More starters: [the list](../README.md) · Docs: <https://uberllm.dev/docs/starters> · MIT license.

Versions: Node 20.9 or newer; `next` 16.4.6, `ai` 7.0.172, `@ai-sdk/react`
4.0.176, `@ai-sdk/openai-compatible` 3.0.92, `zod` 4.6.7. More on the SDK:
<https://uberllm.dev/docs/ai-sdk>.
