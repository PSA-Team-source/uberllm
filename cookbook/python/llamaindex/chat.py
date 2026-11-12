"""LlamaIndex on UberLLM through OpenAILike (llama-index-llms-openai-like):
complete, chat, stream and a function-calling agent.

UberLLM serves chat, image, video, music and speech models; it has no
embeddings endpoint, so pair it with any embedding model for RAG.

    pip install llama-index-core llama-index-llms-openai-like
    export UBERLLM_API_KEY=ull_...
    python chat.py
"""
import asyncio
import os

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai_like import OpenAILike

llm = OpenAILike(
    model=os.environ.get("UBERLLM_MODEL", "deepseek/deepseek-v4-flash"),
    api_base="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
    is_chat_model=True,
    is_function_calling_model=True,
    context_window=128000,  # see context_length in GET /v1/models
)

print(llm.complete("Say hello in one sentence.").text)

reply = llm.chat([
    ChatMessage(role="system", content="You are terse."),
    ChatMessage(role="user", content="Name three primary colors."),
])
print(reply.message.content)

for delta in llm.stream_complete("Count from 1 to 5, separated by commas."):
    print(delta.delta, end="", flush=True)
print()


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


async def main() -> None:
    agent = FunctionAgent(tools=[multiply], llm=llm, system_prompt="Use tools for arithmetic.")
    print(await agent.run("What is 17 times 23?"))


asyncio.run(main())
