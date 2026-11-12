"""A LangChain agent (langchain.agents.create_agent) running on an UberLLM
model. The agent loops: call tools until it can answer.

    pip install langchain langchain-openai
    export UBERLLM_API_KEY=ull_...
    python agent.py
"""
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model=os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)


@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


agent = create_agent(llm, tools=[add, multiply], system_prompt="Use the tools for all arithmetic.")
result = agent.invoke({"messages": [{"role": "user", "content": "What is (12 + 30) * 3?"}]})
print(result["messages"][-1].content)
