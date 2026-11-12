"""Make an image with the OpenAI Python SDK on UberLLM and save it.

Image models: GET /v1/models?type=image, or https://uberllm.dev/models
(Images). Ask for b64_json to get the picture inside the answer; a url
answer points at UberLLM and is kept for about 15 minutes.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python image_generate.py "a red bicycle on a white background"
"""
import base64
import os
import sys

from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)

prompt = " ".join(sys.argv[1:]) or "a red bicycle on a white background, studio photo"
result = client.images.generate(
    model=os.environ.get("UBERLLM_IMAGE_MODEL", "black-forest-labs/flux.2-klein-4b"),
    prompt=prompt,
    size="1024x1024",
    n=1,
    response_format="b64_json",
    # UberLLM's own field: refuse (and charge nothing) if it could cost more.
    extra_body={"max_cost": 0.10},
)

with open("image.png", "wb") as f:
    f.write(base64.b64decode(result.data[0].b64_json))

cost = (result.model_dump().get("usage") or {}).get("cost_usd")
print(f"saved image.png  cost: ${cost}")
