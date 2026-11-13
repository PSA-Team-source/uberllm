# UberLLM starters

Four small projects you can copy and run. Each one uses
[UberLLM](https://uberllm.dev) as the model provider through its
OpenAI-compatible base URL, `https://api.uberllm.dev/v1`: one key for chat,
image, video, music and speech models, each call served by a third-party
provider and billed at that provider's price.

| Starter | What you get | Stack |
|---|---|---|
| [`nextjs-ai-sdk-chat`](nextjs-ai-sdk-chat) | A streaming chat app with a tool and typed output | Next.js, Vercel AI SDK |
| [`langgraph-agent`](langgraph-agent) | An agent that calls tools in a loop | Python, LangGraph |
| [`crewai-crew`](crewai-crew) | Two agents that research and write | Python, CrewAI |
| [`tool-agent-cli`](tool-agent-cli) | A tool-calling agent in one file, no framework, no dependencies | TypeScript, Node |

## Quick start

1. Copy one (replace the name with any starter above):

   ```sh
   npx degit PSA-Team-source/uberllm/starters/tool-agent-cli my-agent
   cd my-agent
   ```

2. Sign in at <https://uberllm.dev>, add credit (prepaid, accounts start at $0) and
   create a key under **Dashboard → Keys**. Then:

   ```sh
   cp .env.example .env   # .env.local for the Next.js starter
   ```

3. Follow the starter's README to install and run. It is one or two commands.

Every starter pins its dependency versions, sets the UberLLM base URL in code
(an `OPENAI_BASE_URL` in your shell is not used), and has a smoke test that runs
without a key and adds a real API call when `UBERLLM_API_KEY` is set.

Single-file examples for more SDKs and languages are in the
[cookbook](../cookbook).

## Does your project support UberLLM? Add a live price badge

If your README tells people they can use UberLLM, a badge shows the current
price of the model you recommend. It is an SVG that UberLLM serves, so it
updates by itself when the price changes.

[![DeepSeek V4 Flash price on UberLLM](https://api.uberllm.dev/api/v1/public/badge/deepseek/deepseek-v4-flash.svg)](https://uberllm.dev/models/deepseek/deepseek-v4-flash?utm_source=embed&utm_medium=referral&utm_campaign=price-badge)

Markdown:

```md
[![DeepSeek V4 Flash price on UberLLM](https://api.uberllm.dev/api/v1/public/badge/deepseek/deepseek-v4-flash.svg)](https://uberllm.dev/models/deepseek/deepseek-v4-flash?utm_source=embed&utm_medium=referral&utm_campaign=price-badge)
```

HTML:

```html
<a href="https://uberllm.dev/models/deepseek/deepseek-v4-flash?utm_source=embed&amp;utm_medium=referral&amp;utm_campaign=price-badge"><img src="https://api.uberllm.dev/api/v1/public/badge/deepseek/deepseek-v4-flash.svg" alt="DeepSeek V4 Flash price on UberLLM"></a>
```

- Put any model id from <https://uberllm.dev/models> in both URLs, for example
  `anthropic/claude-sonnet-5.5`. The badge address is
  `https://api.uberllm.dev/api/v1/public/badge/<model id>.svg` and the link goes
  to `https://uberllm.dev/models/<model id>` (the `utm_` part only tells us the visit
  came from a badge; you can take it off).
- An id that does not exist answers 404, so check the badge loads before you commit.
- Need the numbers instead of a picture? The same prices are JSON at
  `https://api.uberllm.dev/api/v1/public/prices?model=<model id>` (no key, open
  to browsers).
- To have your app listed on <https://uberllm.dev/apps>, send the `HTTP-Referer`
  and `X-Title` headers: <https://uberllm.dev/docs/apps>.

## Check

```sh
node starters.test.mjs          # every starter has what this README promises
node starters.test.mjs --live   # also: the badge and every public link answer
```

## License

MIT, see [LICENSE](../LICENSE).
