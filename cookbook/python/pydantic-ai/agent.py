"""Pydantic AI on UberLLM: an agent with a tool and a typed result.
OpenAIChatModel + OpenAIProvider pointed at the UberLLM base URL.

    pip install "pydantic-ai-slim[openai]"
    export UBERLLM_API_KEY=ull_...
    python agent.py
"""
import os

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    provider=OpenAIProvider(
        base_url="https://api.uberllm.dev/v1",
        api_key=os.environ["UBERLLM_API_KEY"],
    ),
)


class TripCost(BaseModel):
    city: str
    nights: int
    total_usd: float


agent = Agent(
    model,
    deps_type=dict,
    output_type=TripCost,
    system_prompt="Work out trip costs. Always look up the hotel rate with the tool.",
)


@agent.tool
def hotel_rate(ctx: RunContext[dict], city: str) -> float:
    """Nightly hotel rate in US dollars for a city."""
    return ctx.deps.get(city.lower(), 150.0)


result = agent.run_sync("How much are 3 nights in Lisbon?", deps={"lisbon": 120.0})
print(result.output)
print(result.usage)
assert abs(result.output.total_usd - 360.0) < 0.01
