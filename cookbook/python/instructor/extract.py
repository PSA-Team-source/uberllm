"""Instructor on UberLLM: typed extraction with validation and automatic
retries. Wrap the OpenAI client pointed at UberLLM.

    pip install instructor openai
    export UBERLLM_API_KEY=ull_...
    python extract.py
"""
import os

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

client = instructor.from_openai(
    OpenAI(base_url="https://api.uberllm.dev/v1", api_key=os.environ["UBERLLM_API_KEY"]),
    mode=instructor.Mode.TOOLS,
)


class Contact(BaseModel):
    name: str
    email: str
    company: str | None = None
    phone_e164: str | None = Field(None, description="Phone in E.164 format, e.g. +14155550100")

    @field_validator("email")
    @classmethod
    def email_has_at(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("not an email address")
        return v.lower()


text = "Hi, it's Dana Whitfield from Northwind Traders. Reach me at DANA.W@northwind.example or (415) 555-0100."

contact = client.chat.completions.create(
    model=os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    response_model=Contact,
    max_retries=2,  # re-asks the model if validation fails
    messages=[{"role": "user", "content": f"Extract the contact:\n{text}"}],
)
print(contact.model_dump_json(indent=2))
