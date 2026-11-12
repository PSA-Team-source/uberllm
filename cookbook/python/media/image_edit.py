"""Edit a picture with the OpenAI Python SDK on UberLLM (POST /v1/images/edits).

Use an editing model (ids usually end in -edit, or list endpoints
["/v1/images/edits"] in GET /v1/models?type=image). The source picture
is uploaded as a file here; an https:// link in "image" works too.
Masks (inpainting) are not supported.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python image_edit.py photo.png "make the background a sunset"
"""
import base64
import os
import sys

import httpx
from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)

if len(sys.argv) < 3:
    sys.exit("usage: python image_edit.py <picture> <instruction>")
source, instruction = sys.argv[1], " ".join(sys.argv[2:])

with open(source, "rb") as f:
    result = client.images.edit(
        model=os.environ.get("UBERLLM_EDIT_MODEL", "bytedance/seedream-v4-edit"),
        image=f,
        prompt=instruction,
        # Backups, tried in order only if the first model has no free provider right now.
        extra_body={"models": ["google/nano-banana-2-lite-edit", "venice/grok-imagine-edit"]},
    )

item = result.data[0]
if item.b64_json:
    data = base64.b64decode(item.b64_json)
else:
    # A url answer is on UberLLM: download it with the same key.
    r = httpx.get(item.url, headers={"Authorization": f"Bearer {client.api_key}"}, follow_redirects=True)
    r.raise_for_status()
    data = r.content

with open("edited.png", "wb") as f:
    f.write(data)
print(f"saved edited.png ({len(data)} bytes)")
