# Tool-calling agent CLI on UberLLM (TypeScript, no framework)

[![DeepSeek V4 Flash price on UberLLM](https://api.uberllm.dev/api/v1/public/badge/deepseek/deepseek-v4-flash.svg)](https://uberllm.dev/models/deepseek/deepseek-v4-flash?utm_source=embed&utm_medium=referral&utm_campaign=price-badge)

An agent in [one file](agent.ts) with no framework and no dependencies: plain
`fetch` against the OpenAI-compatible chat API of [UberLLM](https://uberllm.dev).
It answers questions about the folder you run it in. The model may list files,
read a file and ask for the time, for as many rounds as it needs. Read it to see
how a tool loop works, then swap in your own tools.

## Quick start

1. Copy the starter (Node 22.18 or newer, which runs TypeScript files directly;
   nothing to install):

   ```sh
   npx degit PSA-Team-source/uberllm/starters/tool-agent-cli my-agent
   cd my-agent
   ```

2. Sign in at <https://uberllm.dev>, add credit (prepaid, accounts start at $0) and
   create a key under **Dashboard → Keys**. Then:

   ```sh
   cp .env.example .env   # then paste your key after UBERLLM_API_KEY=
   ```

3. Ask about the folder:

   ```sh
   node agent.ts "What does this project do?"
   ```

Run `node agent.ts` with no question to chat; it keeps the conversation. Tool
calls, token counts and the cost of each answer are printed as it goes.

## What is in it

| File | What it does |
|---|---|
| [`agent.ts`](agent.ts) | The tools, the loop (`runAgent`) and the command line |
| [`agent.test.ts`](agent.test.ts) | `npm test` |

The tools can only read inside the folder you start it in, and they refuse
hidden files and folders (`.env`, `.git`), so your key is never sent to the
model. To add a tool, add its description to `TOOLS` and its code to `runTool`.

## Test

```sh
npm test
```

Without a key it runs the offline checks: the file rules, and the loop against
a stand-in for the API. With `UBERLLM_API_KEY` set it also calls the real API (a
fraction of a cent). `npm install && npm run typecheck` checks the types.

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

