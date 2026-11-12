"""The official Anthropic Python SDK on UberLLM: Claude or any other model
in the catalog, through the Anthropic Messages API (/v1/messages).

Base URL has no /v1 here: the SDK adds /v1/messages itself.

    pip install anthropic
    export UBERLLM_API_KEY=ull_...
    python messages.py
"""
import os

from anthropic import Anthropic

client = Anthropic(
    base_url="https://api.uberllm.dev",
    api_key=os.environ["UBERLLM_API_KEY"],
)
MODEL = os.environ.get("UBERLLM_MODEL", "anthropic/claude-haiku-4.5")

# 1. One reply
msg = client.messages.create(
    model=MODEL,
    max_tokens=300,
    system="You answer in one sentence.",
    messages=[{"role": "user", "content": "Why is the sky blue?"}],
)
print(msg.content[0].text)
print(f"tokens in/out: {msg.usage.input_tokens}/{msg.usage.output_tokens}\n")

# 2. Streaming
with client.messages.stream(
    model=MODEL,
    max_tokens=300,
    messages=[{"role": "user", "content": "Count from 1 to 5, separated by commas."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print()
