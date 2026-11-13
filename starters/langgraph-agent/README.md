# LangGraph agent on UberLLM (Python)

[![DeepSeek V4 Flash price on UberLLM](https://api.uberllm.dev/api/v1/public/badge/deepseek/deepseek-v4-flash.svg)](https://uberllm.dev/models/deepseek/deepseek-v4-flash?utm_source=embed&utm_medium=referral&utm_campaign=price-badge)

A [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) agent:
the model calls tools in a loop until it can answer. It has two tools, a live
model-price lookup and a multiplier, so it can answer "what would 3 million
output tokens of GPT-5.5 cost?". [UberLLM](https://uberllm.dev) is the model
provider, through LangChain's `ChatOpenAI` with `base_url` set.

## Quick start

1. Copy the starter and install (Python 3.11 or newer):

   ```sh
   npx degit PSA-Team-source/uberllm/starters/langgraph-agent my-agent
   cd my-agent && python -m venv .venv && . .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Sign in at <https://uberllm.dev>, add credit (prepaid, accounts start at $0) and
   create a key under **Dashboard → Keys**. Then:

   ```sh
   cp .env.example .env   # then paste your key after UBERLLM_API_KEY=
   ```

3. Ask it something:

   ```sh
   python agent.py "What would 3 million output tokens of openai/gpt-5.5 cost?"
   ```

Tool calls are printed as they were made, then the answer.

## What is in it

| File | What it does |
|---|---|
| [`agent.py`](agent.py) | The tools, the model (`make_llm`) and the graph (`build_agent`): model → tools → model |
| [`test_agent.py`](test_agent.py) | `python test_agent.py` |

To add a tool, write a function with `@tool` and add it to `TOOLS`.

## Test

```sh
python test_agent.py
```

Without a key it needs no network: the price tool and the graph run against
stand-ins for the price list and the chat API. With `UBERLLM_API_KEY` set it
also calls the real API (a fraction of a cent).

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

Versions: `langgraph` 1.2.21, `langchain-openai` 1.7.4, `langchain-core` 1.8.0.
More on LangChain: <https://uberllm.dev/docs/langchain>.
