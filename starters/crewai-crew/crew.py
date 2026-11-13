"""A CrewAI crew on UberLLM: one agent looks up live model prices, a second
one writes a short buying note from them.

    python crew.py openai/gpt-5.5 anthropic/claude-sonnet-5.5

UberLLM speaks the OpenAI wire format, so the model is CrewAI's LLM pointed at
a custom OpenAI-compatible endpoint: https://docs.crewai.com/en/concepts/llms
"""
import json
import logging
import os
import sys
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()  # reads .env when there is one; before crewai is imported, so its settings apply

from crewai import LLM, Agent, Crew, Process, Task  # noqa: E402
from crewai.tools import tool  # noqa: E402

# CrewAI estimates the size of each request before it sends it, and for a model
# it has no token counter for it prints the same warning every time. The
# estimate is fine; this hides only that line.
logging.getLogger("crewai.llms.base_llm").addFilter(lambda r: "approximate input token count" not in r.getMessage())

# The key is only ever sent here. Passing base_url in code wins over an
# OPENAI_BASE_URL in your shell.
BASE_URL = "https://api.uberllm.dev/v1"
PRICES_URL = "https://api.uberllm.dev/api/v1/public/prices"  # public, sent without the key
DEFAULT_MODEL = "deepseek/deepseek-v4-flash"  # any chat model that takes tools: https://uberllm.dev/models


@tool("model_price")
def model_price(model: str) -> str:
    """Look up the current price of an AI model on UberLLM, in US dollars (text models: per 1M tokens).
    Takes the model id as "maker/name", for example "openai/gpt-5.5"."""
    # UberLLM's public price list; no key needed. It is the price the model's
    # page and the README badge show: https://uberllm.dev/docs/price-api
    url = f"{PRICES_URL}?{urllib.parse.urlencode({'model': model})}"
    try:
        with urllib.request.urlopen(url, timeout=20) as res:
            models = json.load(res)["models"]
    except (OSError, ValueError, KeyError) as err:
        # Timeout, no network, an error page: tell the model, do not end the run.
        return f"Could not reach the price list ({type(err).__name__}). Try again."
    if not models:
        # An unknown id, or a model nobody serves right now, is an empty list.
        return f"There is no model called {model} on UberLLM right now."
    keys = ("id", "name", "unit", "input_per_m", "output_per_m", "list_input_per_m", "list_output_per_m",
            "price", "list_price", "discount_pct")  # the API leaves out fields with no value
    return json.dumps({k: models[0][k] for k in keys if k in models[0]})


def make_llm() -> LLM:
    return LLM(
        # "openai/" tells CrewAI to use its OpenAI client; it is taken off again
        # before the request, so UberLLM gets its own id (which may itself start
        # with "openai/", as in "openai/gpt-5.5").
        model="openai/" + (os.environ.get("UBERLLM_MODEL") or DEFAULT_MODEL),
        custom_openai=True,
        base_url=BASE_URL,
        api_key=os.environ["UBERLLM_API_KEY"],
        temperature=0.3,
    )


def build_crew(llm: LLM) -> Crew:
    researcher = Agent(
        role="Price researcher",
        goal="Report the current price of each model in this list: {models}",
        backstory="You look every price up with the model_price tool and never quote one from memory.",
        tools=[model_price],
        llm=llm,
    )
    writer = Agent(
        role="Writer",
        goal="Turn price notes into a short, plain note that helps a developer choose",
        backstory="You write plain, concrete English and only use the numbers you were given.",
        llm=llm,
    )
    research = Task(
        description="Look up the price of each of these models: {models}.",
        expected_output="One line per model: id, input price and output price in US dollars per 1M tokens.",
        agent=researcher,
    )
    write = Task(
        description="From the price notes, write a note of at most 80 words: which model is cheapest, and by how much.",
        expected_output="One paragraph, at most 80 words.",
        agent=writer,
        context=[research],
    )
    return Crew(agents=[researcher, writer], tasks=[research, write], process=Process.sequential)


def main() -> None:
    if not os.environ.get("UBERLLM_API_KEY"):
        sys.exit("Set UBERLLM_API_KEY first (copy .env.example to .env). Create a key at https://uberllm.dev/dashboard/keys")
    models = sys.argv[1:] or ["openai/gpt-5.5", "anthropic/claude-sonnet-5.5"]

    result = build_crew(make_llm()).kickoff(inputs={"models": ", ".join(models)})
    print(result.raw)
    print(result.token_usage, file=sys.stderr)


if __name__ == "__main__":
    main()
