# CrewAI crew on UberLLM (Python)

[![DeepSeek V4 Flash price on UberLLM](https://api.uberllm.dev/api/v1/public/badge/deepseek/deepseek-v4-flash.svg)](https://uberllm.dev/models/deepseek/deepseek-v4-flash?utm_source=embed&utm_medium=referral&utm_campaign=price-badge)

A [CrewAI](https://docs.crewai.com) crew of two agents on one model: a
researcher that looks up live model prices with a tool, and a writer that turns
them into a short buying note. [UberLLM](https://uberllm.dev) is the model
provider, as a custom OpenAI-compatible endpoint.

## Quick start

1. Copy the starter and install (Python 3.10 to 3.13):

   ```sh
   npx degit PSA-Team-source/uberllm/starters/crewai-crew my-crew
   cd my-crew && python3 -m venv .venv && . .venv/bin/activate
   pip install -r requirements.txt
   ```

   CrewAI does not install on Python 3.14 yet. If that is what you have,
   [uv](https://docs.astral.sh/uv/) gets you a 3.13: replace `python3 -m venv .venv`
   with `uv venv --python 3.13 .venv` and `pip install` with `uv pip install`.

2. Sign in at <https://uberllm.dev>, add credit (prepaid, accounts start at $0) and
   create a key under **Dashboard → Keys**. Then:

   ```sh
   cp .env.example .env   # then paste your key after UBERLLM_API_KEY=
   ```

3. Name the models to compare:

   ```sh
   python crew.py openai/gpt-5.5 anthropic/claude-sonnet-5.5
   ```

## What is in it

| File | What it does |
|---|---|
| [`crew.py`](crew.py) | The tool, the model (`make_llm`) and the crew (`build_crew`): two agents, two tasks |
| [`test_crew.py`](test_crew.py) | `python test_crew.py` |

The model id is written as `"openai/" + <UberLLM id>` with `custom_openai=True`.
The prefix picks CrewAI's OpenAI client and is removed before the request, so
UberLLM receives its own id, also for ids that start with `openai/`.

`.env.example` turns CrewAI's anonymous usage data and trace sharing off
([what CrewAI collects](https://docs.crewai.com/en/telemetry)). Delete those two
lines to turn them back on.

## Test

```sh
python test_crew.py
```

Without a key it needs no network: the price tool and the whole crew run against
stand-ins for the price list and the chat API. With `UBERLLM_API_KEY` set it
also calls the real API (about a cent).

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

Version: `crewai` 1.15.41.
