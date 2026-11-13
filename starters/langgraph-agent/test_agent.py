"""Smoke test.  python test_agent.py

The first two checks need no key and no network: the price tool and the graph
run with stand-ins for the price list and the chat API. The last one calls
the real API and runs only when UBERLLM_API_KEY is set (a fraction of a cent).
"""
import io
import json
import os
import urllib.error
from unittest import mock

import httpx
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage

load_dotenv()
LIVE = bool(os.environ.get("UBERLLM_API_KEY"))
os.environ.setdefault("UBERLLM_API_KEY", "offline-test-key")

import agent  # noqa: E402


def price_list(answer):
    """Stand-in for the public price list: records the address, returns `answer` (or raises it)."""
    asked = []

    def urlopen(url, timeout=None):
        asked.append(url)
        if isinstance(answer, Exception):
            raise answer
        return io.BytesIO(json.dumps(answer).encode())

    return asked, mock.patch("urllib.request.urlopen", urlopen)


def check_price_tool():
    row = {"id": "deepseek/deepseek-v4-flash", "name": "DeepSeek V4 Flash", "type": "text", "unit": "1M tokens", "input_per_m": 0.0091, "output_per_m": 0.0182, "list_input_per_m": 0.09, "list_output_per_m": 0.18, "discount_pct": 89.9, "page_url": "https://uberllm.dev/models/deepseek/deepseek-v4-flash"}
    asked, patch = price_list({"updated_at": "2026-01-01T00:00:00Z", "models": [row]})
    with patch:
        price = agent.model_price.invoke({"model": "deepseek/deepseek-v4-flash"})
    assert asked == ["https://api.uberllm.dev/api/v1/public/prices?model=deepseek%2Fdeepseek-v4-flash"], asked
    assert price["output_per_m"] == 0.0182 and price["discount_pct"] == 89.9 and "page_url" not in price, price
    with price_list({"models": []})[1]:
        missing = agent.model_price.invoke({"model": "nobody/no-such-model"})
    assert "no model called nobody/no-such-model" in missing["error"], missing
    # A network failure is an answer for the model, not the end of the run.
    with price_list(urllib.error.URLError("timed out"))[1]:
        down = agent.model_price.invoke({"model": "openai/gpt-5.5"})
    assert "Could not reach the price list" in down["error"], down
    print("ok  model_price reads the public price list and survives a network failure")


def check_graph_loop():
    """model -> tools -> model, with the chat API replaced by canned answers."""
    sent = []

    def reply(message, finish):
        return httpx.Response(200, json={
            "id": "c1", "object": "chat.completion", "created": 0, "model": agent.DEFAULT_MODEL,
            "choices": [{"index": 0, "message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.uberllm.dev/v1/chat/completions", request.url
        assert request.headers["authorization"] == "Bearer " + os.environ["UBERLLM_API_KEY"]
        sent.append(json.loads(request.content))
        if len(sent) == 1:
            call = {"id": "call_1", "type": "function", "function": {"name": "multiply", "arguments": '{"a": 6, "b": 7}'}}
            return reply({"role": "assistant", "content": None, "tool_calls": [call]}, "tool_calls")
        return reply({"role": "assistant", "content": "The answer is 42."}, "stop")

    llm = agent.make_llm(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    result = agent.build_agent(llm).invoke({"messages": [HumanMessage("What is 6 times 7?")]})

    assert result["messages"][-1].content == "The answer is 42."
    assert [t["function"]["name"] for t in sent[0]["tools"]] == ["model_price", "multiply"]
    tool_turn = sent[1]["messages"][-1]
    assert tool_turn["role"] == "tool" and float(tool_turn["content"]) == 42.0, tool_turn
    print("ok  the graph runs the tool and sends the result back to the model")


def check_live():
    result = agent.build_agent(agent.make_llm()).invoke(
        {"messages": [HumanMessage("What would 2 million output tokens of deepseek/deepseek-v4-flash cost? Look the price up.")]}
    )
    used = [m.name for m in result["messages"] if isinstance(m, ToolMessage)]
    assert "model_price" in used, used
    prices = [m.content for m in result["messages"] if isinstance(m, ToolMessage) and m.name == "model_price"]
    assert any("output_per_m" in p for p in prices), prices  # the real price list answered
    assert result["messages"][-1].content.strip(), "the agent answered"
    print("ok  live: the agent looked the price up and answered:", result["messages"][-1].content.strip()[:120])


if __name__ == "__main__":
    assert httpx.URL(agent.BASE_URL).host == "api.uberllm.dev"
    check_price_tool()
    check_graph_loop()
    if LIVE:
        check_live()
    else:
        print("skip  live check: UBERLLM_API_KEY is not set")
