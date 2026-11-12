"""Make a music track (or sound effect) on UberLLM. Same job flow as video:
start at POST /v1/music/generations, poll, download.

    pip install httpx
    export UBERLLM_API_KEY=ull_...
    python music.py "calm lo-fi beat with soft piano, 90 bpm"

Music models: GET /v1/models?type=music or https://uberllm.dev/models
"""
import os
import sys
import time
import uuid

import httpx

API = "https://api.uberllm.dev/v1"
http = httpx.Client(
    headers={"Authorization": f"Bearer {os.environ['UBERLLM_API_KEY']}"},
    timeout=60,
    follow_redirects=True,
)


def check(r: httpx.Response) -> dict:
    """Return the JSON body, or stop with UberLLM's error message (it says why, in plain words)."""
    if r.is_error:
        try:
            err = r.json()["error"]
            sys.exit(f"{r.status_code} {err.get('code')}: {err.get('message')}")
        except (ValueError, KeyError):
            r.raise_for_status()
    return r.json()

start = http.post(
    f"{API}/music/generations",
    json={
        "model": os.environ.get("UBERLLM_MUSIC_MODEL", "sonilo/sonilo-music-v1-1"),
        "prompt": " ".join(sys.argv[1:]) or "calm lo-fi beat with soft piano, 90 bpm",
        "max_cost": 0.50,  # refuse, at no charge, if it could cost more
    },
    headers={"Idempotency-Key": str(uuid.uuid4())},
)
job = check(start)
print(f"job {job['id']} {job['status']}")

deadline = time.time() + 10 * 60
while job["status"] in ("queued", "running"):
    if time.time() > deadline:
        sys.exit("still running after 10 minutes; poll it later: " + job["id"])
    time.sleep(5)
    job = check(http.get(f"{API}/music/generations/{job['id']}"))

if job["status"] != "succeeded":
    sys.exit(f"job {job['status']}: {job.get('error')}")

result = job["results"][0]
content_type = (result.get("content_type") or "audio/mpeg").split(";")[0]
ext = {"audio/mpeg": ".mp3", "audio/mp4": ".m4a", "audio/x-m4a": ".m4a", "audio/wav": ".wav",
       "audio/x-wav": ".wav", "audio/flac": ".flac", "audio/ogg": ".ogg"}.get(content_type, ".audio")
r = http.get(result["url"])
r.raise_for_status()
with open(f"track{ext}", "wb") as f:
    f.write(r.content)

usage = job.get("usage") or {}
cost = "still settling, see Dashboard -> Activity" if usage.get("cost_pending") else f"${usage.get('cost_usd')}"
print(f"saved track{ext} ({len(r.content)} bytes, {content_type})  cost: {cost}")
