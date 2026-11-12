"""Routing options on UberLLM, through the OpenAI Python SDK's extra_body:

- provider.max_price: the most you pay per 1M tokens, in US dollars. The
  call only goes to providers at or under it and is never billed above it.
  If nobody sells that cheap right now: 400 max_price_exceeded, $0 charged.
- models: fallback models, tried in order when nobody can serve the first.
- metadata: tags stored with the request (Dashboard -> Activity), never
  sent to the provider.

Docs: https://uberllm.dev/docs/models-and-routing

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python routing.py
"""
import os

import openai
from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)

# GET /v1/balance. The SDK's generic get() sends the key for us.
balance = client.get("/balance", cast_to=object)
print(f"available: ${balance['available_usd']:.4f}")

try:
    resp = client.chat.completions.create(
        model="deepseek/deepseek-v4-flash",
        messages=[{"role": "user", "content": "Give me one tip for writing commit messages."}],
        extra_body={
            "provider": {"max_price": {"prompt": 0.5, "completion": 1.0}},
            "models": ["google/gemini-3.1-flash-lite"],
            "metadata": {"project": "cookbook", "example": "routing"},
        },
    )
    usage = resp.usage.model_dump()
    print(resp.choices[0].message.content)
    print(f"answered by {resp.model}, cost ${usage.get('cost_usd')}")
except openai.BadRequestError as e:
    # max_price_exceeded: nobody sells under your ceiling right now. Nothing charged.
    print(f"refused: {e.message}")
except openai.APIStatusError as e:
    # 402 = not enough credit. See https://uberllm.dev/docs/errors
    print(f"refused ({e.status_code}): {e.message}")
