"""DSPy on UberLLM: dspy.LM with the openai/ prefix and api_base, then a
typed signature and a ChainOfThought module.

    pip install dspy
    export UBERLLM_API_KEY=ull_...
    python program.py
"""
import os
from typing import Literal

import dspy

lm = dspy.LM(
    "openai/" + os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    api_base="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
    max_tokens=4000,
)
dspy.configure(lm=lm)


class TicketTriage(dspy.Signature):
    """Route a customer support ticket."""

    ticket: str = dspy.InputField()
    category: Literal["billing", "bug", "feature_request", "account"] = dspy.OutputField()
    urgent: bool = dspy.OutputField()
    reply: str = dspy.OutputField(desc="one-sentence first reply to the customer")


triage = dspy.ChainOfThought(TicketTriage)
out = triage(ticket="I was charged twice for my November invoice and need the duplicate refunded today.")
print("category:", out.category)
print("urgent:  ", out.urgent)
print("reply:   ", out.reply)
assert out.category == "billing"
