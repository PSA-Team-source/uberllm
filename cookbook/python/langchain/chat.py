"""LangChain on UberLLM with ChatOpenAI (langchain-openai): invoke,
stream, tool calling and structured output.

    pip install langchain-openai
    export UBERLLM_API_KEY=ull_...
    python chat.py
"""
import os

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

llm = ChatOpenAI(
    model=os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    base_url="https://api.uberllm.dev/v1",  # wins over OPENAI_BASE_URL
    api_key=os.environ["UBERLLM_API_KEY"],
)

# 1. Invoke
print(llm.invoke("Say hello in one sentence.").content)

# 2. Stream
for chunk in llm.stream("Count from 1 to 5, separated by commas."):
    print(chunk.content, end="", flush=True)
print()


# 3. Tools: the model decides to call get_weather
@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    return f"Sunny and 21C in {city}."


ai_msg = llm.bind_tools([get_weather]).invoke("What's the weather in Paris?")
for call in ai_msg.tool_calls:
    print(call["name"], call["args"], "->", get_weather.invoke(call["args"]))


# 4. Structured output
class Movie(BaseModel):
    title: str
    year: int
    director: str


movie = llm.with_structured_output(Movie).invoke("The 1999 film where Neo takes the red pill.")
print(movie)
