"""Chat completion with the official OpenAI Python SDK on UberLLM.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python chat.py
"""
import os

from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)

resp = client.chat.completions.create(
    model=os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    messages=[
        {"role": "system", "content": "You answer in one short paragraph."},
        {"role": "user", "content": "What is a context window?"},
    ],
)

print(resp.choices[0].message.content)
# UberLLM adds what the call cost, in US dollars, to the usage block.
usage = resp.usage.model_dump()
print(f"\ntokens in/out: {usage['prompt_tokens']}/{usage['completion_tokens']}  cost: ${usage.get('cost_usd')}")
