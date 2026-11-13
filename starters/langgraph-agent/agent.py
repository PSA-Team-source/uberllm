"""A LangGraph agent on UberLLM: the model calls tools in a loop until it can answer.

    python agent.py "What would 3 million output tokens of openai/gpt-5.5 cost?"

The graph is the standard LangGraph agent loop (model -> tools -> model):
https://docs.langchain.com/oss/python/langgraph/quickstart
UberLLM speaks the OpenAI wire format, so the model is LangChain's ChatOpenAI
with base_url set: https://uberllm.dev/docs/langchain
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

# The key is only ever sent here. Passing base_url in code wins over an
# OPENAI_BASE_URL in your shell.
BASE_URL = "https://api.uberllm.dev/v1"
PRICES_URL = "https://api.uberllm.dev/api/v1/public/prices"  # public, sent without the key
DEFAULT_MODEL = "deepseek/deepseek-v4-flash"  # any chat model that takes tools: https://uberllm.dev/models

SYSTEM = (
    "You answer questions about AI model prices. Look prices up with model_price, "
    "never quote one from memory, and use multiply for the arithmetic."
)


@tool
def model_price(model: str) -> dict:
    """Look up the current price of an AI model on UberLLM, in US dollars (text models: per 1M tokens).

    Args:
        model: The model id as "maker/name", for example "openai/gpt-5.5".
    """
    # UberLLM's public price list; no key needed. It is the price the model's
    # page and the README badge show: https://uberllm.dev/docs/price-api
    url = f"{PRICES_URL}?{urllib.parse.urlencode({'model': model})}"
    try:
        with urllib.request.urlopen(url, timeout=20) as res:
            models = json.load(res)["models"]
    except (OSError, ValueError, KeyError) as err:
        # Timeout, no network, an error page: tell the model, do not end the run.
        return {"error": f"Could not reach the price list ({type(err).__name__}). Try again."}
    if not models:
        # An unknown id, or a model nobody serves right now, is an empty list.
        return {"error": f"There is no model called {model} on UberLLM right now."}
    keys = ("id", "name", "unit", "input_per_m", "output_per_m", "list_input_per_m", "list_output_per_m",
            "price", "list_price", "discount_pct")  # the API leaves out fields with no value
    return {k: models[0][k] for k in keys if k in models[0]}


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


TOOLS = [model_price, multiply]


def make_llm(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("UBERLLM_MODEL") or DEFAULT_MODEL,
        base_url=BASE_URL,
        api_key=os.environ["UBERLLM_API_KEY"],
        **kwargs,
    )


def build_agent(llm: ChatOpenAI):
    llm_with_tools = llm.bind_tools(TOOLS)

    def call_model(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([SystemMessage(SYSTEM), *state["messages"]])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", call_model)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "model")
    graph.add_conditional_edges("model", tools_condition)  # tool calls -> "tools", otherwise the end
    graph.add_edge("tools", "model")
    return graph.compile()


def main() -> None:
    load_dotenv()  # reads .env when there is one
    if not os.environ.get("UBERLLM_API_KEY"):
        sys.exit("Set UBERLLM_API_KEY first (copy .env.example to .env). Create a key at https://uberllm.dev/dashboard/keys")
    question = " ".join(sys.argv[1:]).strip() or "What would 3 million output tokens of openai/gpt-5.5 cost?"

    agent = build_agent(make_llm())
    result = agent.invoke({"messages": [HumanMessage(question)]})
    for message in result["messages"]:
        for call in getattr(message, "tool_calls", None) or []:
            print(f"-> {call['name']} {json.dumps(call['args'])}", file=sys.stderr)
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
