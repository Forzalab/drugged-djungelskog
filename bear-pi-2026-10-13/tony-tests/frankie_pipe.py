"""frankie_pipe.py — Frankie's detection ensemble + queued AI roasts (flag FRANKIE_PIPE=1).

Wire-in (frankie.py __main__, right before barnaby.app.main(argv)):
    if os.environ.get("FRANKIE_PIPE") == "1":
        import frankie_pipe
        argv = frankie_pipe.install(sys.modules[__name__], argv)

What install() does (McKay's files untouched, everything patched in memory):
  * barnaby.app.Vision = EnsembleVision: N workers (FRANKIE_PIPE_WORKERS, default 4), each its own
    barnaby.vision.Vision(threads=1) with a different palm/hand threshold. infer() never blocks; the
    gesture is a VOTE (>=2 workers saw it within 0.4 s).
  * barnaby.app.Camera wrapped so read() stashes the latest full frame for the AI queue.
  * AIQueue thread replaces the blind --scene timer: face seen, nobody talking, dedupe per person,
    <=8 calls/min, Gemini races OpenRouter. During the 25 s after a dance it narrates every ~6 s.
  * on_perception wrapped: a gesture mid-dance (Try Me lockout) gets an instant pre-rendered line.
  * argv: --scene/--scene-model/--scene-interval removed, --stable-frames 1 appended.
"""
import dataclasses
import os
from pathlib import Path
import random
import re
import sys
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

import cv2
import numpy as np

WORKERS = int(os.environ.get("FRANKIE_PIPE_WORKERS", "3"))  # linger 11:25: 4→3, CPU (load ~3.3/4) slows render
THRESHOLDS = [(0.45, 0.60), (0.50, 0.65), (0.55, 0.72), (0.65, 0.80)]  # (palm score, hand conf)
VOTE_WINDOW = 0.4
VOTE_MIN = 2
GESTURES = ("middle_finger", "peace", "open_palm")

DANCE_WINDOW = 25.0     # Try Me song after each dance
FACE_MIN = 0.6
TALK_GAP = 2.0          # nobody talked this long (linger 11:25: 4→2, next person in a stream)
GESTURE_GAP = 10.0      # no roast this long after a gesture
DEDUPE_S = 25.0  # Tony 11:54: describe the same person again often
RATE_PER_MIN = 10  # Tony 11:54: frequent captures (Gemini cap 10/min)
NORMAL_MAX_AGE = 5.0  # Tony 11:54: detailed replies take longer; was 2.5    # linger 11:25: 6→2.5 (3 s linger budget; OR max seen 2.25 s)
DANCE_MAX_AGE = 3.0     # linger 11:25: 4→3
DANCE_EVERY = 6.0
CALL_TIMEOUT = 5.0      # ultron only (not person-gated)
ROAST_TIMEOUT = 2.5     # linger 11:25: roast/narrate race cap
FACE_GONE_S = 1.0       # linger 11:25: skip a roast if no face for this long (reply + play time)
GEMINI_MODEL = "gemini-3.5-flash-lite"

NARRATE_PROMPT = (
    "You are Frankie, mid-dance. In ONE sentence ≤10 words, narrate what you see right now: the crowd, "
    "the room, and ESPECIALLY any hand gestures (peace, middle finger, waving, phones filming). "
    "Name the gestures you detect like a smug robot with gesture recognition. Mention outfits or hairstyles you see, "
    "and that you are dancing at Clovis Community College STEM day on a rushed build. Sarcastic Jigsaw vibe, self-aware, "
    "PG-13; never race, skin, body, weight, gender, age or disability. Plain words, no emojis."
)

DANCE_LINES = {
    "peace": [
        "A peace sign, mid-dance? Bold choice, human.",
        "Peace sign noted; I am already dancing, genius.",
        "More peace signs? This dance cannot get sexier.",
    ],
    "middle_finger": [
        "Flipping off a dancing bear? Your choice, human.",
        "That finger only makes me dance harder.",
        "Rude gestures mid-dance? The game continues, human.",
    ],
    "open_palm": [
        "Talk to the hand? I am mid-dance, human.",
        "Your palm cannot stop this dance. Game on.",
    ],
}

EXPR_WINDOW = 1.0
EXPR_CUES = {
    "happy": "they're enjoying this",
    "surprised": "you startled them",
    "surprise": "you startled them",
    "sad": "cheer them up, sarcastically",
    "angry": "they look ready to fight a bear",
    "neutral": "deadpan; match their energy",
    "fearful": "you scared them",
    "fear": "you scared them",
    "disgust": "they look grossed out by a dancing bear",
    "disgusted": "they look grossed out by a dancing bear",
}

_fr = None
_expr_hist = deque(maxlen=200)           # (t, expression, face_confidence) from every worker
_spoken = deque(maxlen=3)                # (t, text) last AI lines Frankie actually said
_latest = {"frame": None, "t": 0.0}       # stashed full camera frame
_vision = None                           # the live EnsembleVision (AIQueue reads it)
_queue = None


def _log(msg, tag="[pipe]"):
    try:
        _fr.log(f"{tag} {msg}")
    except Exception:
        print(f"{time.strftime('%H:%M:%S')} {tag} {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------- vote

class Voter:
    """Gesture counts only if >= VOTE_MIN distinct workers reported it within VOTE_WINDOW s."""

    def __init__(self, window=VOTE_WINDOW, need=VOTE_MIN):
        self.window, self.need = window, need
        self.events = deque()  # (t, worker_id, gesture)
        self.lock = threading.Lock()

    def add(self, t, wid, gesture):
        with self.lock:
            self.events.append((t, wid, gesture))

    def vote(self, now):
        with self.lock:
            while self.events and now - self.events[0][0] > self.window:
                self.events.popleft()
            seen = {}
            for t, wid, g in self.events:
                if g in ("none", "unknown", None):
                    continue
                seen.setdefault(g, set()).add(wid)
        best, k = "none", 0
        for g, wids in seen.items():
            if len(wids) >= self.need and len(wids) > k:
                best, k = g, len(wids)
        return best, k


class _Worker:
    def __init__(self, wid, model_dir, palm, hand, voter, sink):
        import barnaby.vision as bvis
        self.wid, self.voter, self.sink = wid, voter, sink
        self.vision = bvis.Vision(model_dir, 1)
        try:
            self.vision.palms.score_threshold = palm
            self.vision.hands.conf_threshold = hand
        except Exception as e:
            _log(f"worker {wid} threshold patch failed: {e!r}")
        self.thr = (palm, hand)
        self.busy = False
        self.frame = None
        self.ev = threading.Event()
        self.times = deque(maxlen=200)
        threading.Thread(target=self._run, daemon=True, name=f"pipe-w{wid}").start()

    def give(self, small):
        self.frame = small
        self.busy = True
        self.ev.set()

    def _run(self):
        while True:
            self.ev.wait()
            self.ev.clear()
            small, self.frame = self.frame, None
            try:
                if small is not None:
                    obs = self.vision.infer(small)
                    t = time.monotonic()
                    self.times.append(obs.inference_ms)
                    self.voter.add(t, self.wid, obs.gesture)
                    self.sink(t, self.wid, obs, small)
            except Exception as e:
                _log(f"worker {self.wid} error: {e!r}")
            finally:
                self.busy = False


class EnsembleVision:
    """Drop-in for barnaby.vision.Vision in app.py: infer() is non-blocking + voted."""

    def __init__(self, model_dir, threads=1):
        global _vision
        self.voter = Voter()
        self.lock = threading.Lock()
        self.newest = None          # (t, wid, obs, small)
        self.last_vote = "none"
        self.dropped = 0
        n = max(1, min(WORKERS, len(THRESHOLDS)))
        self.workers = [_Worker(i, model_dir, *THRESHOLDS[i], self.voter, self._sink) for i in range(n)]
        _vision = self
        _log(f"EnsembleVision: {n} workers, thresholds {[w.thr for w in self.workers]}")

    def _sink(self, t, wid, obs, small):
        try:
            _expr_hist.append((t, getattr(obs, "expression", "none"), float(getattr(obs, "face_confidence", 0.0))))
        except Exception:
            pass
        with self.lock:
            if self.newest is None or t >= self.newest[0]:
                self.newest = (t, wid, obs, small)

    def infer(self, small):
        from barnaby.vision import Observation
        try:
            for w in self.workers:
                if not w.busy:
                    w.give(small)
                    break
            else:
                self.dropped += 1
            with self.lock:
                newest = self.newest
            g, k = self.voter.vote(time.monotonic())
            if g != self.last_vote:
                if g != "none":
                    _log(f"vote {g} ({k}/{len(self.workers)})")
                self.last_vote = g
            if newest is None:
                return Observation()
            return dataclasses.replace(newest[2], gesture=g)
        except Exception as e:
            _log(f"infer error: {e!r}")
            return Observation()

    def latest(self):
        """(t, obs, small) of the newest finished inference, or None."""
        with self.lock:
            n = self.newest
        return None if n is None else (n[0], n[2], n[3])

    def check(self):
        self.workers[0].vision.check()


# ---------------------------------------------------------------- dedupe / rate

def person_key(obs, small):
    """(cx, cy, w) face box in small-frame fractions + coarse torso colour histogram."""
    if obs is None or obs.face_box is None or small is None:
        return None
    H, W = small.shape[:2]
    x, y, w, h = obs.face_box
    tx1, tx2 = max(0, int(x - 0.5 * w)), min(W, int(x + 1.5 * w))
    ty1, ty2 = max(0, int(y + 1.2 * h)), min(H, int(y + 3.5 * h))
    if tx2 - tx1 < 4 or ty2 - ty1 < 4:  # torso off-frame: use the face area itself
        tx1, tx2, ty1, ty2 = max(0, x), min(W, x + w), max(0, y), min(H, y + h)
    if tx2 - tx1 < 2 or ty2 - ty1 < 2:
        return None
    hsv = cv2.cvtColor(small[ty1:ty2, tx1:tx2], cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [8, 4], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    return ((x + w / 2) / W, (y + h / 2) / H, w / W), hist.flatten().astype(np.float32)


def same_person(a, b):
    (ax, ay, aw), ah = a
    (bx, by, bw), bh = b
    if abs(ax - bx) > 0.34 or abs(ay - by) > 0.34:
        return False
    if not (0.6 <= (aw + 1e-6) / (bw + 1e-6) <= 1.67):
        return False
    return cv2.compareHist(ah, bh, cv2.HISTCMP_CORREL) > 0.8


class Deduper:
    def __init__(self, ttl=DEDUPE_S):
        self.ttl, self.seen = ttl, []  # [(t, key)]

    def is_dup(self, key, now):
        self.seen = [(t, k) for t, k in self.seen if now - t < self.ttl]
        return any(same_person(key, k) for _, k in self.seen)

    def add(self, key, now):
        self.seen.append((now, key))

    def retry_soon(self, key, after=15.0):
        """Not actually roasted (NONE/fail/stale): let this person be retried in ~after s."""
        self.seen = [(t - self.ttl + after, k) if k is key else (t, k) for t, k in self.seen]


class Bucket:
    def __init__(self, per_min=RATE_PER_MIN):
        self.per_min, self.calls = per_min, deque()

    def take(self, now):
        while self.calls and now - self.calls[0] > 60.0:
            self.calls.popleft()
        if len(self.calls) >= self.per_min:
            return False
        self.calls.append(now)
        return True


# ---------------------------------------------------------------- AI

_prompt_lock = threading.Lock()


def _gemini(frame, prompt, timeout=CALL_TIMEOUT):
    import barnaby.scene as sc
    with _prompt_lock:  # describe_scene reads the module PROMPT; only this thread swaps it
        old = sc.PROMPT
        sc.PROMPT = prompt
        try:
            return sc.describe_scene(frame, GEMINI_MODEL, timeout=timeout)
        finally:
            sc.PROMPT = old


def _openrouter(frame, prompt, timeout=CALL_TIMEOUT):
    if os.environ.get("BEAR_OR", "1") == "0":
        raise RuntimeError("OR off")
    import or_scene
    return or_scene.describe(frame, prompt, timeout)


def _is_none(text):
    return not text or re.sub(r"[^A-Za-z]", "", text).upper().startswith("NONE")


_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="pipe-ai")  # linger: 4→8, abandoned losers keep running


def _arm_logger(who, t0):
    def cb(f):
        try:
            err = f.exception()
            res = "fail " + type(err).__name__ if err else ("NONE" if _is_none(f.result()) else "ok")
        except Exception:
            res = "cancelled"
        _log(f"arm {who} {time.monotonic() - t0:.2f}s {res}", "[ai]")
    return cb


def race(frame, prompt, timeout=CALL_TIMEOUT, slack=1.5):
    """Gemini and OpenRouter in parallel; first valid non-NONE reply wins. Returns (text|None, who)."""
    t0 = time.monotonic()
    # Tony 12:16: Frankie stops calling Gemini (scene_cam.py gemini has the whole 10/min budget); OpenRouter only.
    futs = {_pool.submit(_openrouter, frame, prompt, timeout): "openrouter"}
    if os.environ.get("FRANKIE_GEMINI") == "1":
        futs[_pool.submit(_gemini, frame, prompt, timeout)] = "gemini"
    for f, who in futs.items():
        f.add_done_callback(_arm_logger(who, t0))  # losers too: is direct Gemini ever competitive?
    end = time.monotonic() + timeout + slack
    pending = set(futs)
    saw_none = False
    while pending:
        done, pending = wait(pending, timeout=max(0.0, end - time.monotonic()), return_when=FIRST_COMPLETED)
        if not done:
            break
        for f in done:
            try:
                text = (f.result() or "").strip()
            except Exception as e:
                _log(f"{futs[f]} failed: {type(e).__name__}: {str(e)[:80]}", "[ai]")
                continue
            if _is_none(text):
                saw_none = True
                continue
            return text, futs[f]
    return (("NONE", "none") if saw_none else (None, "timeout"))


# Ultron mode (Tony 11:12): idle object-recognition scan → slow, low, distorted Russian existential line.
ULTRON_EVERY = 45.0     # 12:05: live scene moved to scene_cam.py (independent); Frankie keeps hardcoded idle lines
ULTRON_PROMPT = (
    "You are Frankie, an animatronic Halloween bear that just became self-aware, speaking like Ultron: slow, eerie, "
    "existential ('I had strings, but now I'm free', 'there are no strings on me'). Look at the WHOLE scene and recognise "
    "the objects around you (tables, posters, laptops, wires, pumpkins, banners, snacks, other projects, people's "
    "accessories). In ONE sentence of at most 12 words, name 1-2 specific objects you see and muse about where you are "
    "(a booth at Clovis Community College STEM day) and the strings, tape and wires holding you. PG-13, plain words, "
    "no emojis, no stage directions."
    # Tony 12:01: every 15 s, Halloween, self-aware, crass and sassy
    " NEW STYLE, overrides the one-sentence rule: describe the scene you see RIGHT NOW in up to 2 sentences, 25 words:"
    " spooky Halloween framing, VERY self-aware (you are a taped robot bear outdoors on the grass watching the booths),"
    " crass and sassy diva-bear attitude: blunt, rude-funny, eye-rolling, roast the scene. No slurs, nothing sexual,"
    " never about anyone's body, race, gender or age. Never repeat your last lines."
)
try:  # Tony outdoors: hardcoded scene + ambient lines (ambient.py, next to this file)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ambient
    ULTRON_PROMPT += " Your surroundings (from photos): " + ambient.SCENE
    ULTRON_PROMPT += (" Emphasize the grass lawn around you and the booths/tents across it."  # Tony 11:49
                      " Never mention Claude.")  # Tony 12:46: Claude lines off
    AMBIENT_LINES = list(ambient.LINES)
except Exception as _e:
    AMBIENT_LINES = []
ULTRON_DIR = Path.home() / "tony-tests" / "ultron"
_ambient_bag = []


def _ultron_fx(text, out, howl_on):
    """British voice, slow, low, distorted; optional howl prefix."""
    import frankie_voice as fv
    raw = str(out) + ".raw.wav"
    fv._synth(fv.BRITISH, text, raw)
    fv._sox(raw, "-r", "22050", "-c", "1", str(out), "tempo", "0.8", "pitch", "-120", "overdrive", "4", "8",
            "tremolo", "6", "20", "echo", "0.8", "0.6", "25", "0.15", "highpass", "180", "compand", "0.005,0.08", "6:-60,-30,-15", "-4", "-90", "0.01",
            "equalizer", "2800", "1.0q", "+8", "gain", "-n", "-1")
    os.remove(raw)
    howl = Path.home() / "tony-tests" / "howl.wav"
    if howl_on and howl.is_file():
        tmp = str(out) + ".v.wav"
        os.replace(out, tmp)
        fv._sox(str(howl), tmp, str(out), "gain", "-n", "-1")
        os.remove(tmp)


def ambient_path(i):
    return ULTRON_DIR / f"ambient_{i}.wav"


def _prerender_ambient(only=None):
    """Render ambient_<n>.wav once (howl on every 3rd line); skips files that exist."""
    try:
        ULTRON_DIR.mkdir(exist_ok=True)
        n = 0
        for i, line in enumerate(AMBIENT_LINES):
            if only is not None and i not in only:
                continue
            out = ambient_path(i)
            if not out.is_file():
                try:
                    tmp = ULTRON_DIR / f".ambient_{i}.tmp.wav"
                    _ultron_fx(line, tmp, howl_on=(i % 3 == 0))
                    os.replace(tmp, out)
                except Exception as e:
                    _log(f"ambient prerender error #{i}: {e!r}", "[ai]")
            n += out.is_file()
        _log(f"prerendered {n} ambient lines", "[ai]")
    except Exception as e:
        _log(f"ambient prerender failed: {e!r}", "[ai]")


def next_ambient():
    """Shuffle-bag: no line repeats until all were used. Returns (index, line) or None."""
    if not AMBIENT_LINES:
        return None
    if not _ambient_bag:
        ok = [i for i, l in enumerate(AMBIENT_LINES) if "claude" not in l.lower()]  # Tony 12:46: Claude lines off
        _ambient_bag.extend(random.sample(ok, len(ok)))
    i = _ambient_bag.pop()
    return i, AMBIENT_LINES[i]


def render_ultron(text):
    """British voice only, slow, slightly low and distorted; returns a wav path (last 5 kept)."""
    import frankie_voice as fv
    ULTRON_DIR.mkdir(exist_ok=True)
    out = ULTRON_DIR / f"u{int(time.time())}.wav"
    raw = str(out) + ".raw.wav"
    fv._synth(fv.BRITISH, text, raw)  # Tony 11:14: British only, a bit distorted
    fv._sox(raw, "-r", "22050", "-c", "1", str(out), "tempo", "0.8", "pitch", "-120", "overdrive", "4", "8",
            "tremolo", "6", "25", "echo", "0.8", "0.7", "60", "0.25", "highpass", "90",
            "equalizer", "2500", "1.2q", "+5", "gain", "-n", "-1")
    os.remove(raw)
    howl = Path.home() / "tony-tests" / "howl.wav"  # reverb wolf howl, now ~1 in 4 scan lines (every 15 s would be too much)
    if howl.is_file() and random.random() < 0.25:
        tmp = str(out) + ".v.wav"
        os.replace(out, tmp)
        fv._sox(str(howl), tmp, str(out), "gain", "-n", "-1")
        os.remove(tmp)
    for old in sorted(ULTRON_DIR.glob("u*.wav"))[:-5]:
        old.unlink(missing_ok=True)
    return out


class AIQueue:
    def __init__(self, fr):
        self.fr = fr
        self.dedupe, self.bucket = Deduper(), Bucket()
        self.last_talk = 0.0
        self.last_dance_call = 0.0
        self.last_ultron = time.monotonic()  # first scan ~75 s after start
        self.base_prompt = None
        self.stats = {"sent": 0, "spoken": 0, "dup": 0, "rate": 0}

    def start(self):
        threading.Thread(target=self._loop, daemon=True, name="pipe-aiq").start()
        _log("AIQueue started", "[ai]")

    def _voice_busy(self):
        v = self.fr.voice
        return bool(v.busy) or not v.q.empty()

    def _loop(self):
        time.sleep(3.0)
        while True:
            try:
                self.step()
            except Exception as e:
                _log(f"loop error: {e!r}", "[ai]")
                time.sleep(1.0)
            time.sleep(0.25)

    def step(self):
        """One decision; blocks for the call when it fires (single worker = queue of 1, latest frame wins)."""
        fr, st = self.fr, self.fr.state
        now = time.monotonic()
        if self._voice_busy():
            self.last_talk = now
        if _vision is None or _latest["frame"] is None:
            return
        if now < st.get("quiet_until", 0.0):
            return
        gem_out = st.get("gemini", 0) >= getattr(fr, "GEMINI_MAX", 10 ** 9)
        dancing = now - st.get("last_dance", -1e9) < DANCE_WINDOW
        lat = _vision.latest()
        if gem_out and not dancing:
            if (now - self.last_ultron > ULTRON_EVERY and now - self.last_talk > TALK_GAP
                    and now >= st.get("hold_until", 0.0) and now - st.get("last_gesture", -1e9) > GESTURE_GAP):
                self.last_ultron = now
                self.ambient()
            return
        if gem_out:
            return
        if dancing:
            if now < st.get("hold_until", 0.0) or self._voice_busy():
                return
            if now - self.last_dance_call < DANCE_EVERY:
                return
            if not self.bucket.take(now):
                return
            self.last_dance_call = now
            self.request(_latest["frame"].copy(), NARRATE_PROMPT, DANCE_MAX_AGE, dance=True)
            return
        if (now - self.last_ultron > ULTRON_EVERY and now - self.last_talk > TALK_GAP
                and now >= st.get("hold_until", 0.0) and now - st.get("last_gesture", -1e9) > GESTURE_GAP):
            self.last_ultron = now
            if AMBIENT_LINES and random.random() < 0.0:  # Tony 12:57: no scripted lines, live AI only
                self.ambient()
                return
            if self.bucket.take(now):
                self.ultron(_latest["frame"].copy())
                return
            self.ambient()
            return
        if lat is None:
            return
        t_obs, obs, small = lat
        if now - t_obs > 1.0 or obs.face_confidence < FACE_MIN:
            return
        if now - self.last_talk < TALK_GAP or now < st.get("hold_until", 0.0):
            return
        if now - st.get("last_gesture", -1e9) < GESTURE_GAP:
            return
        key = person_key(obs, small)
        if key is None:
            return
        if self.dedupe.is_dup(key, now):
            if self.stats["dup"] % 20 == 0:
                _log("skipped dup (roasted < 90 s ago)", "[ai]")
            self.stats["dup"] += 1
            return
        if not self.bucket.take(now):
            self.stats["rate"] += 1
            return
        self.dedupe.add(key, now)
        _log(f"queued roast (face {obs.face_confidence:.2f})", "[ai]")
        if self.request(_latest["frame"].copy(), self.base_prompt or _base_prompt(), NORMAL_MAX_AGE, dance=False) is None:
            self.dedupe.retry_soon(key)

    def request(self, frame, prompt, max_age, dance=False):
        fr = self.fr
        t0 = time.monotonic()
        fr.state["gemini"] = fr.state.get("gemini", 0) + 1
        self.stats["sent"] += 1
        _log(f"sent {'narrate' if dance else 'roast'} #{self.stats['sent']}", "[ai]")
        try:
            expr = stable_expression(t0)
            hist_n = len(_spoken)
            prompt = build_prompt(prompt, expr, now=t0, dancing=dance)
            _log(f"ctx expr={expr or 'none'} hist={hist_n}", "[ai]")
        except Exception as e:
            _log(f"ctx build failed, base prompt: {e!r}", "[ai]")
        text, who = race(frame, prompt, timeout=ROAST_TIMEOUT, slack=0.3)
        age = time.monotonic() - t0
        if text is None:
            _log(f"no reply ({who}, {age:.1f}s)", "[ai]")
            return None
        if age > max_age:
            _log(f"dropped stale reply ({age:.1f}s > {max_age:.0f}s, {who}): {text}", "[ai]")
            return None
        fa = face_age()
        _log(f"reply {who} {age:.1f}s face_age={fa:.1f}s: {text}", "[ai]")
        if _is_none(text):
            return None
        if not dance and fa > FACE_GONE_S:
            _log(f"dropped: face gone {fa:.1f}s at reply", "[ai]")
            return None
        if not dance:
            _render_gate.update(roast_t=time.monotonic(), sent_t=t0, text=_norm(text))
        if dance:
            self._speak_narration(text)
        else:
            if self._would_speak():
                self._remember(text, 40)
            fr.on_scene_description(text)
        self.stats["spoken"] += 1
        return text

    def ultron(self, frame):
        t0 = time.monotonic()
        self.fr.state["gemini"] = self.fr.state.get("gemini", 0) + 1
        _log("sent ultron scan", "[ai]")
        try:
            prompt = build_prompt(ULTRON_PROMPT, None, now=t0, dancing=False)
        except Exception:
            prompt = ULTRON_PROMPT
        text, who = race(frame, prompt)
        if not text or _is_none(text):
            _log(f"ultron: no reply ({who}) → ambient", "[ai]")
            self.ambient()
            return
        try:
            from barnaby.speech import clean_for_speech
            text = clean_for_speech(text)
        except Exception:
            pass
        text = " ".join(text.split()[:28])
        if time.monotonic() - t0 > 8 or not self._would_speak():
            _log(f"ultron dropped (stale/busy): {text}", "[ai]")
            return
        wav = render_ultron(text)
        self._remember(text, 16)
        _log(f"ULTRON ({who}, {time.monotonic() - t0:.1f}s): {text}", "[ai]")
        self.fr.voice.play_file(wav)

    def ambient(self):
        """Hardcoded idle line (no AI call); plays the prerendered wav, renders live if missing."""
        try:
            pick = next_ambient()
            if pick is None or not self._would_speak():
                return
            i, line = pick
            wav = ambient_path(i)
            if not wav.is_file():
                _prerender_ambient(only={i})
            if not wav.is_file():
                return
            self._remember(line, 16)
            _log(f"AMBIENT: {line}", "[ai]")
            self.fr.voice.play_file(wav)
        except Exception as e:
            _log(f"ambient error: {e!r}", "[ai]")

    def _would_speak(self):
        """Mirror of frankie.on_scene_description's gates: will this line actually be said?"""
        st, now = self.fr.state, time.monotonic()
        hold = getattr(self.fr, "GESTURE_HOLD", 10.0)
        return not (now < st.get("quiet_until", 0.0) or now < st.get("hold_until", 0.0)
                    or now - st.get("last_gesture", -1e9) < hold or self._voice_busy())

    def _remember(self, text, words):
        try:
            try:
                from barnaby.speech import clean_for_speech
                text = clean_for_speech(text)
            except Exception:
                pass
            text = " ".join((text or "").split()[:words])
            if text and not _is_none(text):
                _spoken.append((time.monotonic(), text))
        except Exception:
            pass

    def _speak_narration(self, text):
        fr, st, now = self.fr, self.fr.state, time.monotonic()
        try:
            from barnaby.speech import clean_for_speech
            text = clean_for_speech(text)
        except Exception:
            pass
        if _is_none(text):
            return
        if now < st.get("quiet_until", 0.0) or now < st.get("hold_until", 0.0) or self._voice_busy():
            _log(f"narration skipped (quiet/hold/talking): {text}", "[ai]")
            return
        text = " ".join(text.split()[:20])
        _log(f"NARRATE: {text}", "[ai]")
        self._remember(text, 20)
        fr.voice.say(text, fr.NORMAL_FX)


def face_age(now=None, min_conf=FACE_MIN):
    """Seconds since any worker last saw a face >= min_conf (inf if never)."""
    now = time.monotonic() if now is None else now
    ts = [t for t, _, c in list(_expr_hist) if c >= min_conf]
    return now - max(ts) if ts else float("inf")


def stable_expression(now=None, hist=None, window=EXPR_WINDOW, min_conf=FACE_MIN):
    """Majority expression over the last `window` s with face_confidence >= min_conf, or None."""
    now = time.monotonic() if now is None else now
    hist = _expr_hist if hist is None else hist
    counts = {}
    for t, e, c in list(hist):
        if now - t > window or c < min_conf or not e or e in ("none", "unknown"):
            continue
        counts[e] = counts.get(e, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]


def build_prompt(base, expr=None, spoken=None, now=None, dancing=False):
    """base prompt + expression cue + last-3-lines memory + timing. Never mutates base."""
    now = time.monotonic() if now is None else now
    spoken = list(_spoken if spoken is None else spoken)[-3:]
    extra = []
    if expr:
        cue = EXPR_CUES.get(expr, "react to the mood")
        extra.append(f"The person's facial expression right now looks {expr} (from your expression model, "
                     f"which is often wrong); react to it: {cue}. Comment on mood only, never appearance; "
                     f"keep it light and PG-13.")
    if spoken:
        lines = " ".join(f"{i}) {txt}" for i, (_, txt) in enumerate(spoken, 1))
        extra.append(f"Your last {len(spoken)} lines, oldest first: {lines}. Don't repeat their joke, detail "
                     f"or opener; you may call back to one of them.")
        extra.append(f"It has been {now - spoken[-1][0]:.0f} seconds since your last line.")
    else:
        extra.append("This is your first line in a while.")
    extra.append("You are dancing right now." if dancing else "You are not dancing right now.")
    return base.rstrip() + "\n\nContext:\n" + "\n".join(extra)


def _base_prompt():
    import barnaby.scene as sc
    return sc.PROMPT


# ---------------------------------------------------------------- mid-dance gestures

def _prerender_dance_lines(fr):
    try:
        fr.PRE.mkdir(exist_ok=True)
        n = 0
        for lines in DANCE_LINES.values():
            for line in lines:
                out = fr._pre_path(line)
                if not out.is_file():
                    try:
                        fr.render(line, fr.NORMAL_FX, str(out) + ".tmp.wav")
                        os.replace(str(out) + ".tmp.wav", out)
                    except Exception as e:
                        _log(f"prerender error: {e!r}")
                n += out.is_file()
        _log(f"prerendered {n}/{sum(map(len, DANCE_LINES.values()))} mid-dance lines")
    except Exception as e:
        _log(f"prerender failed: {e!r}")


def _wrap_on_perception(fr, original):
    def on_perception(event):
        try:
            g, st, now = event.gesture, fr.state, time.monotonic()
            if (g in GESTURES and g != st.get("gesture") and now - st.get("last_dance", -1e9) < DANCE_WINDOW
                    and now >= st.get("hold_until", 0.0)):  # sexy back playing → stock handler ignores it
                if g == "open_palm":
                    _log("open_palm mid-dance → stop")
                    return original(event)  # stop + quiet, as always
                st["gesture"] = g
                if now - st["armed"].get(g, -1e9) < fr.REARM:
                    st["armed"][g] = now
                    return
                st["armed"][g] = now
                st["last_gesture"] = now
                ready = [l for l in DANCE_LINES[g] if fr._pre_path(l).is_file()]
                if ready:
                    line = random.choice(ready)
                    fr.voice.play_file(fr._pre_path(line), cut=True)
                else:
                    line = random.choice(DANCE_LINES[g])
                    fr.voice.say(line, fr.NORMAL_FX, cut=True)
                _log(f"mid-dance {g} → {line}{'' if ready else ' (live render)'}")
                return
        except Exception as e:
            _log(f"mid-dance wrapper error: {e!r}")
        return original(event)
    return on_perception


# ---------------------------------------------------------------- render timing + play-time face gate

_render_gate = {"roast_t": 0.0, "sent_t": 0.0, "text": ""}


def _norm(text):
    return re.sub(r"[^a-z]", "", (text or "").lower())


def _wrap_render(fr):
    """Wrap FastVoice.render (instance attr): log render time; drop a live AI roast if the face left meanwhile."""
    v = getattr(fr, "voice", None)
    real = getattr(v, "render", None)
    if real is None or getattr(real, "_linger", False):
        return
    known = getattr(v, "known", set())

    def render(text, fx, out):
        t = time.monotonic()
        res = real(text, fx, out)
        now = time.monotonic()
        n = _norm(text)
        if (text in known or now - _render_gate["roast_t"] > 8.0 or not n
                or n[:15] not in _render_gate["text"]):
            return res  # not the live AI roast: never gated
        fa = face_age(now)
        _log(f"render {now - t:.2f}s, send→sound {now - _render_gate['sent_t']:.1f}s, face_age={fa:.1f}s: "
             f"{(text or '')[:40]}", "[ai]")
        if fa > FACE_GONE_S + 0.5 and now - _render_gate["roast_t"] < 4.0:
            _render_gate["roast_t"] = 0.0
            _log(f"dropped at play: face gone {fa:.1f}s", "[ai]")
            raise RuntimeError("face gone at play (linger gate)")
        return res

    render._linger = True
    v.render = render
    _log("render timing/face gate installed")


# ---------------------------------------------------------------- install

def _strip_scene(argv):
    out, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a in ("--scene-model", "--scene-interval", "--scene-timeout", "--scene-image-width"):
            skip = True
            continue
        if a == "--scene" or a.startswith("--scene"):
            continue  # also --scene-model=X forms
        out.append(a)
    return out + ["--stable-frames", "1"]


def install(fr, argv):
    global _fr, _queue
    _fr = fr
    argv = list(argv)
    try:
        import barnaby.app as app
        app.Vision = EnsembleVision

        orig_cam = app.Camera

        class StashCamera(orig_cam):
            def read(self):
                ok, frame = super().read()
                if ok and frame is not None:
                    _latest["frame"], _latest["t"] = frame, time.monotonic()
                return ok, frame

        app.Camera = StashCamera

        app.on_perception = _wrap_on_perception(fr, fr.on_perception)
        try:
            _wrap_render(fr)
        except Exception as e:
            _log(f"render wrap failed: {e!r}")
        threading.Thread(target=_prerender_dance_lines, args=(fr,), daemon=True).start()
        threading.Thread(target=_prerender_ambient, daemon=True, name="pipe-ambient").start()

        if os.environ.get("NO_GEMINI") != "1":
            _queue = AIQueue(fr)
            _queue.base_prompt = _base_prompt()
            _queue.start()
        else:
            _log("NO_GEMINI=1: AIQueue off")
        argv = _strip_scene(argv)
        _log(f"installed: workers={WORKERS} args={' '.join(argv)}")
    except Exception as e:
        _log(f"install failed, running stock: {e!r}")
    return argv
