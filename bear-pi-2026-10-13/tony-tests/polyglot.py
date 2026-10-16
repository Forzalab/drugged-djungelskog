"""polyglot.py — Frankie's random side-show (STEM day 2026-10-13): every 25-45 s says ONE of
 (a) a sassy professor-bear 2-sentence Dijkstra lecture (English, en_GB alan), or
 (b) a short Halloween/self-aware bear line in Arabic / Mandarin / Russian / English / German / Japanese, HIGH baby voice.
Renders first, THEN queues on the shared speaker lock like scene_cam.py speak() (flock .speak.lock, wait for no pw-play
up to 30 s, drop if stale > 45 s). Log: polyglot.log. Stop file: NO_POLY.
Japanese: Piper has no ja voice and espeak-ng is not installed -> en_GB alan reads romaji (baby-pitched).
"""
import fcntl, random, shutil, subprocess, sys, tempfile, time, wave
from pathlib import Path

HERE = Path("/home/spauly/tony-tests")
VOICES = HERE / "voices"
LOCK = HERE / ".speak.lock"
LOGF = HERE / "polyglot.log"
STOP = HERE / "NO_POLY"

V = {  # language -> piper model (first existing one wins)
    "en": ["en_GB-alan-medium"],
    "ru": ["ru_RU-dmitri-medium", "ru_RU-denis-medium"],
    "ar": ["ar_JO-kareem-medium", "ar_JO-kareem-low"],
    "zh": ["zh_CN-huayan-x_low", "zh_CN-huayan-medium"],
    "de": ["de_DE-eva_k-x_low", "de_DE-thorsten-medium"],
    "ja": ["en_GB-alan-medium"],  # reads romaji
}

DIJKSTRA = [
    "Listen up, cubs: Dijkstra's algorithm is greedy. It always settles the closest unvisited node next, and with non-negative weights that greedy choice is never wrong.",
    "Pop quiz, humans. Dijkstra keeps unfinished nodes in a min-priority queue keyed by tentative distance, so the next node to finalize is always the one on top of the heap.",
    "Relaxation, darlings, is the whole trick. For each edge from u to v, if dist of u plus the weight beats dist of v, you lower dist of v and remember u as its parent.",
    "With a binary min-heap, Dijkstra runs in big O of V plus E, times log V. Use a plain array instead and you get V squared, which is actually fine for dense graphs.",
    "Dijkstra demands non-negative edge weights. A negative edge could make a node you already finalized cheaper later, and the greedy algorithm never goes back to fix it.",
    "Got negative edges? Then put Dijkstra down and use Bellman-Ford, which relaxes every edge V minus one times and can even detect negative cycles.",
    "Keep the parent pointers from each successful relaxation, and Dijkstra hands you a shortest-path tree. Every node's path back to the source is a shortest path.",
    "Here's the invariant, sweethearts: once a node is popped from the priority queue, its distance is final. Nothing cheaper can ever reach it afterwards, as long as weights are non-negative.",
    "Dijkstra starts with the source at distance zero and everyone else at infinity. Then it repeatedly pops the smallest distance and relaxes that node's outgoing edges.",
    "On an unweighted graph, Dijkstra behaves just like breadth-first search. The priority queue simply pops nodes in order of hop count.",
    "Your GPS and internet routers use Dijkstra's idea, the OSPF protocol for example. Shortest paths from one source, computed greedily, settled one node at a time.",
    "Want only one destination? Stop Dijkstra the moment the target is popped from the queue. Add a good heuristic and congratulations, you've reinvented A-star.",
]

LINES = {  # (text to speak, text to log) — native script for all but Japanese, which is spoken as romaji
    "ar": [
        "أنا دبٌّ آليّ، وأخاف من الأشباح!",
        "عيد هالوين سعيد! أين الحلوى؟",
        "أنا لست دبًّا حقيقيًّا، أنا روبوت جائع.",
        "احذروا! الدبّ يرى كلّ شيء.",
        "بطاريتي ضعيفة، أعطوني قطعة شوكولاتة.",
        "هل رأيتم القرع؟ أريد أن آكله!",
    ],
    "zh": [
        "我是一只机器熊，我也怕鬼！",
        "万圣节快乐！糖果在哪里？",
        "我不是真的熊，我是饿了的机器人。",
        "小心！熊熊在看着你。",
        "我的电池快没电了，给我巧克力！",
        "不给糖就捣蛋，熊熊说的！",
    ],
    "ru": [
        "Я робот-медведь, и я боюсь привидений!",
        "С Хэллоуином! Где мои конфеты?",
        "Я не настоящий медведь, я голодный робот.",
        "Осторожно! Медведь всё видит.",
        "Моя батарейка садится, дайте шоколадку!",
        "Кошелёк или жизнь! Так говорит медведь.",
    ],
    "en": [
        "I'm a robot bear, and I'm scared of ghosts!",
        "Happy Halloween! Where is my candy?",
        "I'm not a real bear. I'm a hungry robot.",
        "Careful! The bear sees everything.",
        "My battery is low. Feed me chocolate!",
        "Trick or treat! The bear has spoken.",
    ],
    "de": [
        "Ich bin ein Roboterbär und habe Angst vor Geistern!",
        "Fröhliches Halloween! Wo sind meine Süßigkeiten?",
        "Ich bin kein echter Bär, ich bin ein hungriger Roboter.",
        "Vorsicht! Der Bär sieht alles.",
        "Mein Akku ist fast leer. Gebt mir Schokolade!",
        "Süßes oder Saures! Sagt der Bär.",
    ],
    "ja": [
        ("Boku wa robotto no kuma. Obake ga kowai!", "ぼくはロボットのくま。おばけがこわい！"),
        ("Happii Harowiin! Okashi wa doko?", "ハッピーハロウィン！おかしはどこ？"),
        ("Boku wa hontou no kuma ja nai. Onaka ga suita robotto da yo.", "ぼくはほんとうのくまじゃない。おなかがすいたロボットだよ。"),
        ("Ki o tsukete! Kuma wa zenbu mite iru yo.", "きをつけて！くまはぜんぶみているよ。"),
        ("Denchi ga nai yo. Chokoreeto choudai!", "でんちがないよ。チョコレートちょうだい！"),
        ("Torikku oa toriito! Kuma ga itta yo.", "トリック・オア・トリート！くまがいったよ。"),
    ],
}
LANGS = list(LINES)
P_DIJKSTRA = 0.35
EVERY = (25, 45)

BABY = ["pitch", "+700", "tempo", "0.85"]
PROF = ["pitch", "-60", "tempo", "0.97"]
SHARED = ["highpass", "150", "overdrive", "3", "6",
          "compand", "0.005,0.08", "6:-60,-30,-15", "-4", "-90", "0.01",
          "equalizer", "2800", "1.0q", "+6", "gain", "-n", "-1"]

_loaded = {}


def log(msg):
    line = f"{time.strftime('%F %T')} polyglot: {msg}"
    print(line, flush=True)
    with open(LOGF, "a") as f:
        f.write(line + "\n")


def model(lang):
    for n in V[lang]:
        p = VOICES / f"{n}.onnx"
        if p.is_file() and (VOICES / f"{n}.onnx.json").is_file():
            return p
    return None


def synth(path, text, out):
    if path not in _loaded:
        from piper import PiperVoice
        _loaded[path] = PiperVoice.load(str(path))
    with wave.open(out, "wb") as wf:
        _loaded[path].synthesize_wav(text, wf)


def sox(*args):
    subprocess.run(["sox", *args], check=True, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dur(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def render(kind, lang, text, out):
    """kind 'dijkstra' (English professor) or 'baby'. Writes final wav to out."""
    m = model("en" if kind == "dijkstra" else lang)
    if m is None:
        raise RuntimeError(f"no voice for {lang}")
    with tempfile.TemporaryDirectory(prefix="poly-") as d:
        raw = f"{d}/raw.wav"
        synth(m, text, raw)
        sox(raw, "-r", "22050", "-c", "1", out, *(PROF if kind == "dijkstra" else BABY), *SHARED)
    return out


def pick(rng=random):
    if rng.random() < P_DIJKSTRA:
        t = rng.choice(DIJKSTRA)
        return "dijkstra", "en", t, t
    langs = [l for l in LANGS if model(l) is not None]
    lang = rng.choice(langs)
    item = rng.choice(LINES[lang])
    spoken, shown = item if isinstance(item, tuple) else (item, item)
    return "baby", lang, spoken, shown


def sound_playing():
    return subprocess.run(["pgrep", "-x", "pw-play"], stdout=subprocess.DEVNULL).returncode == 0


def play(wav, t_made, label):
    with open(LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)  # queue behind Frankie / scene narrators
        for _ in range(60):  # then wait up to ~30 s for silence
            if not sound_playing():
                break
            time.sleep(0.5)
        if time.monotonic() - t_made > 45:
            log(f"dropped stale (waited too long): {label}")
            return False
        subprocess.run(["pw-play", wav], timeout=90)
        return True


def once(rng=random):
    kind, lang, spoken, shown = pick(rng)
    with tempfile.TemporaryDirectory(prefix="poly-") as d:
        out = render(kind, lang, spoken, f"{d}/out.wav")
        t_made = time.monotonic()
        label = f"[{kind}/{lang} {dur(out):.1f}s] {shown}"
        if play(out, t_made, label):
            log(f"said {label}")


def main():
    log(f"start (pid {__import__("os").getpid()}, every {EVERY[0]}-{EVERY[1]} s); voices: "
        + ", ".join(f"{l}={model(l).stem if model(l) else 'MISSING'}" for l in V))
    while not STOP.exists():
        time.sleep(random.uniform(*EVERY))
        if STOP.exists():
            break
        try:
            once()
        except Exception as e:
            log(f"error: {e!r}")
            time.sleep(5)
    log("NO_POLY found, stopping")


if __name__ == "__main__":
    main()
