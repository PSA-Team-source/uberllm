"""List UberLLM models and pick by price and features.

GET /v1/models returns the chat models you can call right now, with
price per 1M tokens (pricing.input_usd / pricing.output_usd), the list
price it is compared with, context_length and supports_tools.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python list_models.py            # 15 cheapest chat models that take tools
    python list_models.py image      # image models (also: video, music, speech, all)
"""
import os
import sys

from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)

kind = sys.argv[1] if len(sys.argv) > 1 else "chat"
page = client.models.list(extra_query={"type": kind})
models = [m.model_dump() for m in page.data]

if kind == "chat":
    usable = [m for m in models if m.get("available") and m.get("supports_tools")]
    usable.sort(key=lambda m: m["pricing"]["input_usd"] + m["pricing"]["output_usd"])
    print(f"{'model':55} {'in $/M':>8} {'out $/M':>8} {'context':>9}")
    for m in usable[:15]:
        p = m["pricing"]
        print(f"{m['id']:55} {p['input_usd']:8.4f} {p['output_usd']:8.4f} {m.get('context_length', 0):9d}")
else:
    for m in models:
        p = m.get("pricing", {})
        print(f"{m['id']:55} ${p.get('usd')} per {p.get('unit')}")

print(f"\n{len(models)} {kind} models. Live prices: https://uberllm.dev/models")
