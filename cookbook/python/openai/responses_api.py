"""The OpenAI Responses API (client.responses.create) on UberLLM.

Works on every chat model. UberLLM stores nothing, so there is no
previous_response_id: send the whole conversation in `input` each time.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python responses_api.py
"""
import os

from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)
MODEL = os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash")

conversation = [{"role": "user", "content": "Name one planet with rings."}]
first = client.responses.create(
    model=MODEL,
    instructions="Answer in one short sentence.",
    input=conversation,
)
print("1:", first.output_text)

# Next turn: append the answer and the new question, send it all again.
conversation += [
    {"role": "assistant", "content": first.output_text},
    {"role": "user", "content": "Name another one."},
]
second = client.responses.create(
    model=MODEL,
    instructions="Answer in one short sentence.",
    input=conversation,
)
print("2:", second.output_text)
