"""OpenRouter FALLBACK for Frankie's camera roasts (used only when Gemini fails).

    from or_scene import describe
    text = describe(frame_bgr, prompt, timeout=5.0)   # str, or raises RuntimeError

Fires the same request at 3 fast vision models in parallel and returns the first
valid reply. The API key is never printed or logged.
"""
import base64
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import requests

# Chosen 2026-10-13 from the live https://openrouter.ai/api/v1/models list (all have
# "image" in architecture.input_modalities). Hard-coded: no list fetch at runtime.
MODELS = [
    # Newest Gemini flash-lite: cheapest/fastest Gemini vision tier, same family as primary.
    "google/gemini-3.5-flash-lite",
    # Grok has no image-capable "fast" variant on OR today; grok-4.20 is the one xAI
    # bills as "industry-leading speed" and accepts images.
    "x-ai/grok-4.20",
    # Small, fast vision model that is strong at staying in character / dry humor.
    "anthropic/claude-haiku-5.5",
]

# Gemini 3.x / Grok 4.7 on OR reject reasoning-off ("Reasoning is mandatory"), so ask for
# the smallest thinking budget instead and give room for it on top of the ~80 reply tokens.
_EXTRA = {
    "google/gemini-3.5-flash-lite": {"reasoning": {"effort": "minimal"}, "max_tokens": 400},
    "google/gemini-3.8-flash": {"reasoning": {"effort": "minimal"}, "max_tokens": 400},
    "x-ai/grok-4.7": {"reasoning": {"effort": "low"}, "max_tokens": 400},
}

URL = "https://openrouter.ai/api/v1/chat/completions"
LOG = os.path.expanduser("~/tony-tests/or_detect.log")
ENV_FILE = os.path.expanduser("~/tony-tests/.or_env")
MAX_WORDS = 40

_log_lock = threading.Lock()
_session = requests.Session()

# Hard profanity / slurs only (PG-13: "damn", "hell", "crap" are fine).
_BLOCK = re.compile(
    r"\b(fuck\w*|motherf\w*|shit\w*|bullshit|cunt\w*|cock\w*|dick(head)?s?|pussy|pussies|"
    r"bitch\w*|bastard\w*|whore\w*|slut\w*|asshole\w*|nigg\w*|fag\w*|faggot\w*|retard\w*|"
    r"tranny|trannies|spic\w*|chink\w*|kike\w*|wetback\w*|dyke\w*|twat\w*|wank\w*|rape\w*|"
    r"porn\w*|nazi\w*)\b",
    re.I,
)
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\U0000200D\U00002B00-\U00002BFF]"
)
_URL = re.compile(r"(https?://|www\.|\]\(|\b\w+\.(com|org|net|io|ai)\b)", re.I)
_MD = re.compile(r"(^\s*#|^\s*[-*]\s|```|`|\|)", re.M)


def _key():
    k = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not k:
        try:
            with open(ENV_FILE) as f:
                for line in f:
                    m = re.match(r"\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.+)", line)
                    if m:
                        k = m.group(1).strip().strip("'\"")
                        break
        except OSError:
            pass
    if not k:
        raise RuntimeError("no OR key")
    return k


def _data_url(frame):
    h, w = frame.shape[:2]
    if w > 512:
        frame = cv2.resize(frame, (512, max(1, int(h * 512 / w))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
    if not ok:
        raise RuntimeError("jpeg encode failed")
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def _clean(text):
    """Return a speakable reply or None if it fails the checks."""
    if not text:
        return None
    t = text.replace("*", "").replace("_", " ")
    t = _EMOJI.sub("", t)
    t = re.sub(r"\s+", " ", t).strip().strip('"').strip()
    # Normalise "no person" answers to exactly NONE (some models explain instead).
    if re.search(r"\bNONE\b", t) or re.search(r"\b(no|not a|without a) (person|human|people)\b", t, re.I):
        return "NONE"
    if not t or _URL.search(t) or _MD.search(t) or _BLOCK.search(t):
        return None
    if len(t.split()) > MAX_WORDS:
        return None
    return t


def _log(model, dt, ok, text):
    snippet = (text or "").replace("\n", " ")[:80]
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {model} {dt:.2f}s {'ok' if ok else 'fail'} | {snippet}\n"
    with _log_lock:
        try:
            with open(LOG, "a") as f:
                f.write(line)
        except OSError:
            pass


def _call(model, key, prompt, data_url, timeout):
    t0 = time.monotonic()
    raw = ""
    try:
        r = _session.post(
            URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "X-Title": "Frankie bear"},
            json={
                "model": model,
                "max_tokens": 80,
                **_EXTRA.get(model, {"reasoning": {"enabled": False}}),
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]}],
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            raw = f"HTTP {r.status_code}: {r.text[:60]}"
            raise ValueError(raw)
        raw = (r.json()["choices"][0]["message"].get("content") or "")
        out = _clean(raw)
        if out is None:
            raise ValueError("rejected")
        _log(model, time.monotonic() - t0, True, out)
        return model, out, time.monotonic() - t0
    except Exception as e:
        _log(model, time.monotonic() - t0, False, raw or f"{type(e).__name__}")
        raise


last_winner = None  # (model, latency) of the most recent successful describe()


def describe(frame, prompt: str, timeout: float = 5.0) -> str:
    global last_winner
    key = _key()
    data_url = _data_url(frame)
    pool = ThreadPoolExecutor(max_workers=len(MODELS))
    futs = [pool.submit(_call, m, key, prompt, data_url, timeout) for m in MODELS]
    try:
        for f in as_completed(futs, timeout=timeout + 1.0):
            try:
                model, text, dt = f.result()
            except Exception:
                continue
            last_winner = (model, dt)
            return text
    except Exception:
        pass
    finally:
        pool.shutdown(wait=False)  # losers finish in background and still get logged
    raise RuntimeError("all OR models failed")
