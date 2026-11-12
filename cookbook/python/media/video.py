"""Make a video on UberLLM: check the price, start the job, wait, download.

A video is a job: POST /v1/video/generations answers 202 with a job id,
GET /v1/video/generations/<id> tells you how it is going, and the file
is downloaded from results[].url (kept about 3 hours). A failed,
canceled or expired job costs nothing.

    pip install httpx
    export UBERLLM_API_KEY=ull_...
    python video.py "a paper boat drifting down a rainy street"

Video models and prices: https://uberllm.dev/models (Video) or
GET /v1/models?type=video. Each model's clip lengths, resolutions and
shapes: GET /v1/models/<model id> (the "parameters" schema).
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

job_request = {
    "model": os.environ.get("UBERLLM_VIDEO_MODEL", "fal-ai/veo3.1/lite"),
    "prompt": " ".join(sys.argv[1:]) or "a paper boat drifting down a rainy street, cinematic",
    "duration_seconds": 4,
    "resolution": "720p",
    "aspect_ratio": "16:9",
    "audio": False,
    # Tried in order only if the first model has no free provider right now.
    "models": ["meituan/longcat-distilled-text-to-video"],
    "max_cost": 0.50,  # refuse, at no charge, if it could cost more
}

# 1. Price check: validate=true checks everything, makes nothing, charges nothing.
quote = http.post(f"{API}/video/generations", json={**job_request, "validate": True})
q = check(quote)
print(f"listed cost ${q['cost_usd']}, at most ${q['max_cost_usd']} held")

# 2. Start. The Idempotency-Key makes a retried POST return the same job.
start = http.post(
    f"{API}/video/generations",
    json=job_request,
    headers={"Idempotency-Key": str(uuid.uuid4())},
)
job = check(start)
print(f"job {job['id']} {job['status']} on {job['model']}")

# 3. Wait. Most videos take 1-5 minutes.
deadline = time.time() + 15 * 60
while job["status"] in ("queued", "running"):
    if time.time() > deadline:
        http.delete(f"{API}/video/generations/{job['id']}")
        sys.exit("gave up after 15 minutes and asked to stop the job")
    time.sleep(8)
    job = check(http.get(f"{API}/video/generations/{job['id']}"))
    print(f"  {job['status']} {job.get('progress') or ''}")

if job["status"] != "succeeded":
    sys.exit(f"job {job['status']}: {job.get('error')}")

# 4. Download with the same key.
url = job["results"][0]["url"]
with http.stream("GET", url) as r, open("video.mp4", "wb") as f:
    r.raise_for_status()
    for chunk in r.iter_bytes():
        f.write(chunk)
usage = job.get("usage") or {}
cost = "still settling, see Dashboard -> Activity" if usage.get("cost_pending") else f"${usage.get('cost_usd')}"
print(f"saved video.mp4  cost: {cost}")
