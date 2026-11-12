"""Ask a vision model about a picture. OpenAI Python SDK on UberLLM.

Pick a model whose input_modalities include "image" (GET /v1/models).
Pass a public https:// link or a local file; a local file is sent inline
as a data:image/...;base64 URI.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python vision.py                     # a sample picture
    python vision.py photo.jpg           # a local file
    python vision.py https://.../a.png   # a public link
"""
import base64
import mimetypes
import os
import sys

from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)

source = sys.argv[1] if len(sys.argv) > 1 else (
    "https://raw.githubusercontent.com/PSA-Team-source/uberllm/main/assets/icon.png"
)
if source.startswith("https://"):
    image_url = source
else:
    mime = mimetypes.guess_type(source)[0] or "image/png"
    with open(source, "rb") as f:
        image_url = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

resp = client.chat.completions.create(
    model=os.environ.get("UBERLLM_VISION_MODEL", "google/gemini-3.1-flash-lite"),
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this picture? One sentence."},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ],
)
print(resp.choices[0].message.content)
