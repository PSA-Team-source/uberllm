"""Streaming chat with the OpenAI Python SDK on UberLLM.

UberLLM asks the provider for usage on every stream, so the last chunk
carries token counts and usage.cost_usd.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python stream.py
"""
import os

from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)

stream = client.chat.completions.create(
    model=os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    messages=[{"role": "user", "content": "Count from 1 to 10, one number per line."}],
    stream=True,
)

usage = None
for chunk in stream:
    if chunk.choices:
        print(chunk.choices[0].delta.content or "", end="", flush=True)
    if chunk.usage:
        usage = chunk.usage.model_dump()

print()
if usage:
    print(f"tokens in/out: {usage['prompt_tokens']}/{usage['completion_tokens']}  cost: ${usage.get('cost_usd')}")
