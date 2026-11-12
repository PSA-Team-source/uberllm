"""Tool use with the Anthropic Python SDK on UberLLM: the model calls a
tool, we run it and send back a tool_result, the model answers.

Works with Claude and with other tool-capable models in the catalog
(e.g. UBERLLM_MODEL=deepseek/deepseek-v4-flash).

    pip install anthropic
    export UBERLLM_API_KEY=ull_...
    python tools.py
"""
import os

from anthropic import Anthropic

client = Anthropic(
    base_url="https://api.uberllm.dev",
    api_key=os.environ["UBERLLM_API_KEY"],
)
MODEL = os.environ.get("UBERLLM_MODEL", "anthropic/claude-haiku-4.5")

tools = [
    {
        "name": "get_stock_price",
        "description": "Get the latest price of a stock ticker, in US dollars.",
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    }
]


def get_stock_price(ticker: str) -> str:
    # Replace with a real market data call.
    return {"AAPL": "231.40", "MSFT": "418.12"}.get(ticker.upper(), "unknown")


messages = [{"role": "user", "content": "What does one share of AAPL cost right now?"}]
for _ in range(5):
    resp = client.messages.create(model=MODEL, max_tokens=500, tools=tools, messages=messages)
    if resp.stop_reason != "tool_use":
        print("".join(b.text for b in resp.content if b.type == "text"))
        break
    messages.append({"role": "assistant", "content": resp.content})
    results = []
    for block in resp.content:
        if block.type == "tool_use":
            out = get_stock_price(**block.input)
            print(f"-> {block.name}({block.input}) = {out}")
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": out})
    messages.append({"role": "user", "content": results})
