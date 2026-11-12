"""LiteLLM on UberLLM: use the openai/ prefix plus api_base. The rest of
the model name is the UberLLM model id, so "openai/deepseek/deepseek-v4-flash"
calls deepseek/deepseek-v4-flash.

    pip install litellm
    export UBERLLM_API_KEY=ull_...
    python chat.py

LiteLLM proxy (config.yaml), same idea:

    model_list:
      - model_name: deepseek-v4-flash
        litellm_params:
          model: openai/deepseek/deepseek-v4-flash
          api_base: https://api.uberllm.dev/v1
          api_key: os.environ/UBERLLM_API_KEY
"""
import os

import litellm

MODEL = "openai/" + os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash")
KW = {"api_base": "https://api.uberllm.dev/v1", "api_key": os.environ["UBERLLM_API_KEY"]}

resp = litellm.completion(
    model=MODEL,
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    **KW,
)
print(resp.choices[0].message.content)

for chunk in litellm.completion(
    model=MODEL,
    messages=[{"role": "user", "content": "Count from 1 to 5, separated by commas."}],
    stream=True,
    **KW,
):
    print(chunk.choices[0].delta.content or "", end="", flush=True)
print()

# Router with a fallback model: if the first deployment errors, LiteLLM tries the next.
router = litellm.Router(
    model_list=[
        {"model_name": "fast", "litellm_params": {"model": MODEL, **KW}},
        {"model_name": "backup", "litellm_params": {"model": "openai/google/gemini-3.1-flash-lite", **KW}},
    ],
    fallbacks=[{"fast": ["backup"]}],
)
r = router.completion(model="fast", messages=[{"role": "user", "content": "One word for happy?"}])
print(r.choices[0].message.content)
