"""Structured output: get a typed Pydantic object back instead of text.
OpenAI Python SDK on UberLLM (response_format with a JSON schema).

Models that list "structured_outputs" in supported_parameters
(GET /v1/models) follow the schema.

    pip install openai pydantic
    export UBERLLM_API_KEY=ull_...
    python structured_output.py
"""
import os

from openai import OpenAI
from pydantic import BaseModel

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)


class Invoice(BaseModel):
    vendor: str
    invoice_number: str
    total_usd: float
    line_items: list[str]


text = """ACME Corp - Invoice #INV-2041
2x USB-C cable ........ $18.00
1x 27in monitor ....... $229.00
Total due: $247.00"""

completion = client.chat.completions.parse(
    model=os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    messages=[
        {"role": "system", "content": "Extract the invoice fields."},
        {"role": "user", "content": text},
    ],
    response_format=Invoice,
)

invoice = completion.choices[0].message.parsed
print(invoice)
assert invoice is not None and abs(invoice.total_usd - 247.0) < 0.01
