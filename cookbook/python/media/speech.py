"""Text to speech and speech to text with the OpenAI Python SDK on UberLLM.

Speech is billed per started 1K characters, transcription per minute of
audio. Voices differ per model: GET /v1/models/<model id> lists them.

    pip install openai
    export UBERLLM_API_KEY=ull_...
    python speech.py "Your order has shipped and will arrive on Friday."
"""
import os
import sys

from openai import OpenAI

client = OpenAI(
    base_url="https://api.uberllm.dev/v1",
    api_key=os.environ["UBERLLM_API_KEY"],
)

text = " ".join(sys.argv[1:]) or "Your order has shipped and will arrive on Friday."

# Text -> speech.mp3. with_raw_response gives us the cost header too.
raw = client.audio.speech.with_raw_response.create(
    model=os.environ.get("UBERLLM_TTS_MODEL", "venice/kokoro-tts"),
    voice="af_heart",
    input=text,
    response_format="mp3",
)
raw.parse().write_to_file("speech.mp3")
print(f"saved speech.mp3  cost: ${raw.headers.get('x-uberllm-cost-usd')}")

# speech.mp3 -> text
with open("speech.mp3", "rb") as f:
    transcript = client.audio.transcriptions.create(
        model=os.environ.get("UBERLLM_STT_MODEL", "venice/whisper-large-v3"),
        file=f,
    )
print("transcript:", transcript.text)
