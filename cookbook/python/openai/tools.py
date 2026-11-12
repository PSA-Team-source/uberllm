"""Tool calling, the full loop: the model asks for a tool, we run it, the
model answers with the result. OpenAI Python SDK on UberLLM.

Any model with "supports_tools": true in GET /v1/models works.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python tools.py
"""
import json
import os

from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)
MODEL = os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash")


def get_weather(city: str) -> dict:
    # Replace with a real weather API call.
    return {"city": city, "celsius": 21, "sky": "clear"}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name"}},
                "required": ["city"],
            },
        },
    }
]
FUNCTIONS = {"get_weather": get_weather}

messages = [{"role": "user", "content": "What's the weather in Paris and in Tokyo?"}]

for _ in range(5):  # stop after 5 rounds whatever happens
    resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
    msg = resp.choices[0].message
    if not msg.tool_calls:
        print(msg.content)
        break
    # Send the assistant turn back exactly as received: some models (Gemini)
    # put a signature in it that they need on the next turn.
    messages.append(msg.model_dump(exclude_none=True))
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments or "{}")
        result = FUNCTIONS[call.function.name](**args)
        print(f"-> {call.function.name}({args}) = {result}")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)})
