"""Smoke test.  python test_crew.py

The first two checks need no key and no network: the price tool and the crew
run with stand-ins for the price list and the chat API. The last one calls
the real API and runs only when UBERLLM_API_KEY is set (about a cent).
"""
import io
import json
import os
import urllib.error
from unittest import mock

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

import httpx  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()
LIVE = bool(os.environ.get("UBERLLM_API_KEY"))
os.environ.setdefault("UBERLLM_API_KEY", "offline-test-key")

import crew  # noqa: E402


PRICE_ROW = {"id": "deepseek/deepseek-v4-flash", "name": "DeepSeek V4 Flash", "type": "text", "unit": "1M tokens", "input_per_m": 0.0091, "output_per_m": 0.0182, "list_input_per_m": 0.09, "list_output_per_m": 0.18, "discount_pct": 89.9, "page_url": "https://uberllm.dev/models/deepseek/deepseek-v4-flash"}


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
    asked, patch = price_list({"updated_at": "2026-01-01T00:00:00Z", "models": [PRICE_ROW]})
    with patch:
        price = json.loads(crew.model_price.run(model="deepseek/deepseek-v4-flash"))
    assert asked == ["https://api.uberllm.dev/api/v1/public/prices?model=deepseek%2Fdeepseek-v4-flash"], asked
    assert price["output_per_m"] == 0.0182 and price["discount_pct"] == 89.9 and "page_url" not in price, price
    with price_list({"models": []})[1]:
        assert "no model called nobody/no-such-model" in crew.model_price.run(model="nobody/no-such-model")
    # A network failure is an answer for the agent, not the end of the run.
    with price_list(urllib.error.URLError("timed out"))[1]:
        assert "Could not reach the price list" in crew.model_price.run(model="openai/gpt-5.5")
    print("ok  model_price reads the public price list and survives a network failure")


def check_crew_run():
    """Both agents run, with the chat API replaced by canned answers."""
    sent = []

    def reply(message, finish):
        return httpx.Response(200, json={
            "id": "c1", "object": "chat.completion", "created": 0, "model": crew.DEFAULT_MODEL,
            "choices": [{"index": 0, "message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://api.uberllm.dev/v1/chat/completions", request.url
        assert request.headers["authorization"] == "Bearer " + os.environ["UBERLLM_API_KEY"]
        body = json.loads(request.content)
        sent.append(body)
        if len(sent) == 1:  # the researcher asks for a price
            call = {"id": "call_1", "type": "function", "function": {"name": "model_price", "arguments": '{"model": "deepseek/deepseek-v4-flash"}'}}
            return reply({"role": "assistant", "content": None, "tool_calls": [call]}, "tool_calls")
        if len(sent) == 2:  # the researcher reports
            return reply({"role": "assistant", "content": "deepseek/deepseek-v4-flash: see tool result."}, "stop")
        return reply({"role": "assistant", "content": "DeepSeek V4 Flash is the cheapest."}, "stop")  # the writer

    def send(self, request, **kwargs):
        response = handler(request)
        response.request = request
        return response

    with mock.patch.object(httpx.Client, "send", send), price_list({"models": [PRICE_ROW]})[1]:
        result = crew.build_crew(crew.make_llm()).kickoff(inputs={"models": "deepseek/deepseek-v4-flash"})

    assert result.raw == "DeepSeek V4 Flash is the cheapest.", result.raw
    assert len(sent) == 3, len(sent)
    assert all(body["model"] == crew.DEFAULT_MODEL for body in sent), [b["model"] for b in sent]
    assert sent[0]["tools"][0]["function"]["name"] == "model_price", sent[0].get("tools")
    tool_turn = sent[1]["messages"][-1]
    assert tool_turn["role"] == "tool" and "output_per_m" in tool_turn["content"], tool_turn  # the price went back
    print("ok  the crew runs both agents and the tool, and sends UberLLM its own model id")


def check_live():
    result = crew.build_crew(crew.make_llm()).kickoff(inputs={"models": "deepseek/deepseek-v4-flash, openai/gpt-5.5"})
    assert result.raw.strip(), "the crew answered"
    assert result.token_usage.total_tokens > 0
    print("ok  live: the crew answered:", result.raw.strip()[:160])


if __name__ == "__main__":
    assert httpx.URL(crew.BASE_URL).host == "api.uberllm.dev"
    check_price_tool()
    check_crew_run()
    if LIVE:
        check_live()
    else:
        print("skip  live check: UBERLLM_API_KEY is not set")
