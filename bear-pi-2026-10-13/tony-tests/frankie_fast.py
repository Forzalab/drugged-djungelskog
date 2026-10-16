"""frankie_fast.py — reaction-speed add-on for frankie.py (2026-10-13, agent C). Nothing here touches McKay's repo.

FastVoice  drop-in for frankie.Voice (say / play_file / stop / busy / q) with
           * a persistent pre-render cache (same dir + md5 key as frankie.prerender → SEXY files are shared),
             filled in a background thread at start: scripted gesture lines play instantly (~0.1 s) instead of
             1.2–1.6 s render (+7 s Piper model load after a crash-restart),
           * a two-stage pipeline (render thread → play thread): the next line renders while the current one plays,
           * a ≤3 s cap per line (MAX_SEC): longer audio is sped up (tempo ≤1.35) then trimmed with a fade,
           * cut=True   = gesture: drops queued/playing SCENE lines, lets a playing gesture line finish, keeps queued
                          gesture lines → several detections each get their reaction,
             cut="all"  = open palm: everything stops.
race(fns)  run Gemini and OpenRouter at the same time, first good answer wins (Gemini was timing out at 25 s every
           call this morning → roasts arrived ~26 s late; OR answers in ~1 s).
shorten()  cap a roast at N words on a sentence boundary before rendering.
"""
import hashlib, os, queue, subprocess, sys, tempfile, threading, time, wave
from pathlib import Path

MAX_SEC = 3.0       # Tony: every voice line ≤ 3 s
MAX_TEMPO = 1.35    # speed-up allowed before we just trim
MAX_WORDS = 9       # roast word cap (≈3 s of Alan at tempo 0.95)
PLAYER = ["pw-play"]


def _log(msg):
    print(f"{time.strftime('%H:%M:%S')} [fast] {msg}", file=sys.stderr, flush=True)


def wav_len(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def key_path(cache_dir, text):
    """Same scheme as frankie._pre_path so the two caches are one."""
    return Path(cache_dir) / (hashlib.md5(text.encode()).hexdigest()[:12] + ".wav")


def cap(src, dst, max_sec=MAX_SEC):
    """Make dst ≤ max_sec: tempo up to MAX_TEMPO, then hard trim with a 0.15 s fade. Returns dst (or src if short)."""
    dur = wav_len(src)
    if dur <= max_sec + 0.05:
        return str(src)
    fx = []
    factor = dur / max_sec
    if factor <= MAX_TEMPO:
        fx += ["tempo", "-s", f"{factor + 0.01:.3f}"]
    else:
        fx += ["tempo", "-s", f"{MAX_TEMPO:.3f}"]
    fx += ["trim", "0", f"{max_sec:.2f}", "fade", "t", "0", f"{max_sec:.2f}", "0.15"]
    subprocess.run(["sox", str(src), str(dst), *fx], check=True, timeout=30,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(dst)


def shorten(text, n=MAX_WORDS):
    """First sentence(s) up to n words; a long first sentence is cut at n words."""
    import re
    words_total, out = 0, []
    sents = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    if len(sents) >= 2 and re.search(r"play a game|make your choice|game over", sents[0], re.I):
        sents = sents[1:]  # skip the generic Jigsaw opener, keep the actual roast
    for s in sents:
        w = len(s.split())
        if words_total + w > n:
            break
        out.append(s)
        words_total += w
    if not out:  # first (real) sentence alone is too long: hard cut at n words
        w = (sents[0] if sents else text).split()[:n]
        while len(w) > 3 and w[-1].lower().strip(",;:") in ("or", "and", "but", "the", "a", "an", "of", "to", "with",
                                                             "for", "so", "because", "like", "your", "my"):
            w.pop()  # don't end on a dangling conjunction / article
        out = [" ".join(w).rstrip(",;:.") + "."]
    return " ".join(out)


def race(fns, timeout=8.0):
    """fns: {name: zero-arg callable}. Run all in daemon threads, return (name, result) of the first that returns
    without raising. Losers keep running in the background (daemon) and are ignored."""
    q = queue.Queue()

    def run(name, fn):
        try:
            q.put((name, fn(), None))
        except Exception as e:
            q.put((name, None, e))

    for name, fn in fns.items():
        threading.Thread(target=run, args=(name, fn), daemon=True, name=f"race-{name}").start()
    deadline, errors, left = time.monotonic() + timeout, {}, len(fns)
    while left:
        try:
            name, result, err = q.get(timeout=max(0.0, deadline - time.monotonic()))
        except queue.Empty:
            break
        left -= 1
        if err is None:
            return name, result
        errors[name] = f"{type(err).__name__}"
    raise RuntimeError(f"race: all failed/timed out {errors}")


class FastVoice:
    """Same interface as frankie.Voice. Items carry a kind: 'gesture' (cut=True / play_file) or 'scene'."""

    def __init__(self, render, cache_dir, prerender=(), log=_log, max_sec=MAX_SEC):
        self.render, self.cache, self.log, self.max_sec = render, Path(cache_dir), log, max_sec
        self.cache.mkdir(exist_ok=True)
        self.known = set(prerender)          # texts we cache (scripted); everything else renders to a temp file
        self.order = list(prerender)        # prerender order (most likely first gesture first)
        self.rq, self.pq = queue.Queue(), queue.Queue()  # (text, fx_or_path, kind, t0)  /  (wav, kind, t0, tmpdir)
        self.q = self.rq                      # frankie checks voice.q.empty()
        self.proc, self.playing, self.rendering = None, None, None
        self.cut_scene, self.cut_all = 0.0, 0.0
        self._locks, self._lock = {}, threading.Lock()
        threading.Thread(target=self._render_loop, daemon=True, name="fast-render").start()
        threading.Thread(target=self._play_loop, daemon=True, name="fast-play").start()

    # ---- public --------------------------------------------------------------------------------------------------
    @property
    def busy(self):
        return bool(self.playing or self.rendering or not self.rq.empty() or not self.pq.empty())

    def say(self, text, fx=None, cut=False):
        kind = "gesture" if cut else "scene"
        if cut:
            self.stop(everything=(cut == "all"))
        self.rq.put((text, fx, kind, time.monotonic()))

    def play_file(self, path, cut=False):
        if cut:
            self.stop(everything=(cut == "all"))
        self.rq.put((None, str(path), "gesture", time.monotonic()))

    def stop(self, everything=True):
        """everything=True: cut all (open palm). False: drop scene lines only; gesture lines keep their turn."""
        now = time.monotonic()
        if everything:
            self.cut_all = now
        else:
            self.cut_scene = now
        for q in (self.rq, self.pq):
            keep = []
            while True:
                try:
                    item = q.get_nowait()
                except queue.Empty:
                    break
                if not self._dead(item[-2] if q is self.rq else item[1], item[-1] if q is self.rq else item[2]):
                    keep.append(item)
            for item in keep:
                q.put(item)
        p = self.proc
        if p and p.poll() is None and (everything or self.playing == "scene"):
            p.terminate()

    def start_prerender(self, lines=None):
        threading.Thread(target=self._prerender, args=(list(lines or self.order),), daemon=True,
                         name="fast-prerender").start()

    # ---- internals -----------------------------------------------------------------------------------------------
    def _dead(self, kind, t0):
        return t0 < self.cut_all or (kind == "scene" and t0 < self.cut_scene)

    def _key_lock(self, k):
        with self._lock:
            return self._locks.setdefault(k, threading.Lock())

    def _cached(self, text, fx):
        """Uncapped render in the shared cache (same file frankie.prerender would write), then a capped twin."""
        out = key_path(self.cache, text)
        with self._key_lock(str(out)):
            if not out.is_file():
                tmp = str(out) + f".fast{os.getpid()}.wav"
                self.render(text, fx, tmp)
                os.replace(tmp, out)
            capped = out.with_name(out.stem + f"-{self.max_sec:g}s.wav")
            if not capped.is_file():
                tmp = str(capped) + ".tmp.wav"
                res = cap(out, tmp, self.max_sec)
                if res == str(out):
                    return str(out)  # already short enough
                os.replace(tmp, capped)
        return str(capped)

    def _prerender(self, lines):
        t = time.monotonic()
        n = 0
        for line in lines:
            try:
                self._cached(line, None)
                n += 1
            except Exception as e:
                self.log(f"prerender error ({line[:30]}): {e!r}")
        self.log(f"prerendered {n}/{len(lines)} lines in {time.monotonic() - t:.1f}s → {self.cache}")

    def _render_loop(self):
        while True:
            text, fx, kind, t0 = self.rq.get()
            if self._dead(kind, t0):
                continue
            self.rendering = kind
            tmpdir = None
            try:
                if text is None:
                    wav = fx  # ready-made file
                elif text in self.known:
                    wav = self._cached(text, fx)
                else:
                    tmpdir = tempfile.mkdtemp(prefix="fast-")
                    raw = f"{tmpdir}/raw.wav"
                    self.render(text, fx, raw)
                    wav = cap(raw, f"{tmpdir}/line.wav", self.max_sec)
                if self._dead(kind, t0):
                    continue
                self.pq.put((wav, kind, t0, tmpdir))
                tmpdir = None
            except Exception as e:
                self.log(f"render error: {e!r}")
            finally:
                self.rendering = None
                if tmpdir:
                    subprocess.run(["rm", "-rf", tmpdir])

    def _play_loop(self):
        while True:
            wav, kind, t0, tmpdir = self.pq.get()
            try:
                if self._dead(kind, t0):
                    continue
                self.playing = kind
                self.proc = subprocess.Popen(PLAYER + [wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    self.proc.wait(timeout=240)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    raise
            except Exception as e:
                self.log(f"play error: {e!r}")
            finally:
                self.proc, self.playing = None, None
                if tmpdir:
                    subprocess.run(["rm", "-rf", tmpdir])
