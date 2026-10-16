"""Spooky-but-friendly sound effects for the evil teddy bear (audio only).

Every effect is a *recipe*: a short list of sox / Piper steps run in a scratch
directory that must leave ``out.wav`` behind. The result is then trimmed,
converted to mono 22050 Hz and loudness-normalised (``gain -n -1``) into
``fx_cache/<name>.wav``. A manifest stores a hash of each recipe, so effects
are rendered once and re-rendered only when their recipe changes.

Python API::

    import creepy_fx
    creepy_fx.render_all()            # {name: path} of the effects that rendered
    creepy_fx.play("heartbeat")       # True / False, never raises
    creepy_fx.play_random(exclude=("thunder",))
    creepy_fx.duration("music_box")   # seconds or None
    creepy_fx.NAMES

CLI::

    $PY creepy_fx.py list | render | play NAME | demo

Kid-safe by design: no screams, no violence words, nothing gory.
"""
import hashlib
import json
import logging
import os
import random
import subprocess
import sys
import tempfile
import time
import wave

sys.dont_write_bytecode = True

log = logging.getLogger("creepy_fx")

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "fx_cache")
MANIFEST = "manifest.json"
BEAR_REPO = os.path.expanduser("~/Desktop/barnaby/evil-autonomous-bear-proj")
PIPER_BIN = os.environ.get("CREEPY_FX_PIPER", os.path.join(BEAR_REPO, ".venv/bin/piper"))
PIPER_VOICE = os.environ.get("CREEPY_FX_VOICE", os.path.join(BEAR_REPO, "voices/en_US-ryan-medium.onnx"))
RATE = 22050
MAX_SECONDS = 5.8
STEP_TIMEOUT = 60
XDG_RUNTIME_DIR = "/run/user/%d" % os.getuid()

# Every synth step starts with this: a silent null input, mono, 22050 Hz.
N = ["-n", "-r", str(RATE), "-c", "1"]
# Applied to every effect's out.wav (after the recipe) before caching.
FINAL_CHAIN = ["rate", str(RATE), "trim", "0", str(MAX_SECONDS),
               "fade", "t", "0.005", "-0", "0.08", "gain", "-n", "-1"]
# Loudness levelling: effects whose RMS (after peak-normalising) is below QUIET_RMS
# are run through this fast compressor first, so sparse/peaky sounds (clock ticks,
# music box, voices) come out closer in loudness to the dense drones, which are
# already above the threshold and therefore left untouched.
QUIET_RMS = 0.2
COMPAND = ["compand", "0.0005,0.03", "-70,-62,-45,-22,-20,-9,0,-4", "-2", "-90", "0.001"]


def sox(*args):
    """A recipe step running ``sox args...`` inside the scratch directory."""
    return ("sox",) + tuple(str(a) for a in args)


def piper(text, out):
    """A recipe step speaking ``text`` with the bear's Piper voice into ``out``."""
    return ("piper", text, out)


def _concat(parts, out, *effects):
    """sox step joining wav files end to end, then applying ``effects``."""
    return sox(*parts, out, *effects)


# --------------------------------------------------------------------------
# Recipes. Each returns a list of steps; the last step must write out.wav.
# --------------------------------------------------------------------------

def _heartbeat():
    """Slow 'lub-dub' heartbeat: low sine thumps separated by silence."""
    return [
        sox(*N, "thump.wav", "synth", 0.16, "sine", "95/45", "fade", "q", 0.006, 0.16, 0.13),
        sox("thump.wav", "lub.wav", "pad", 0, 0.12),
        sox("thump.wav", "dub.wav", "vol", 0.65, "pad", 0, 0.62),
        _concat(["lub.wav", "dub.wav"] * 3, "out.wav", "overdrive", 6, "lowpass", 400, "bass", "+6"),
    ]


def _creaky_door():
    """Old door slowly creaking open: buzzy sawtooth glide chopped by fast tremolo."""
    return [
        sox(*N, "creak.wav", "synth", 2.4, "sawtooth", "95:170", "synth", 2.4, "sine", "amod", "11:28",
            "tremolo", 3, 60, "bandpass", 900, "400h", "lowpass", 2800, "reverb", 30),
        sox("creak.wav", "out.wav", "fade", "q", 0.25, 2.4, 0.4, "pad", 0, 0.3),
    ]


def _howling_wind():
    """Howling wind: band-filtered pink noise breathing in and out, with a faint whistle."""
    return [
        sox(*N, "air.wav", "synth", 4.5, "pinknoise", "band", 500, 350, "tremolo", 0.35, 70,
            "flanger", 0, 6, 0, 70, 0.3, "fade", "q", 1.0, 4.5, 1.3),
        sox(*N, "w1.wav", "synth", 2.2, "sine", "380:620", "vol", 0.18),
        sox(*N, "w2.wav", "synth", 2.3, "sine", "620:330", "vol", 0.18),
        _concat(["w1.wav", "w2.wav"], "whistle.wav", "tremolo", 0.6, 60, "fade", "q", 0.8, 4.5, 1.2),
        sox("-m", "air.wav", "whistle.wav", "out.wav", "reverb", 50),
    ]


def _ghost_moan():
    """Ghost going 'Whooo': slowed, pitched-down voice over a wavering sine glide."""
    return [
        piper("Whoooooo. Ooooooooh.", "v.wav"),
        sox("v.wav", "voice.wav", "tempo", 0.6, "pitch", -500, "chorus", 0.6, 0.9, 55, 0.4, 0.25, 2, "-t",
            "reverb", 80),
        sox(*N, "g1.wav", "synth", 1.4, "sine", "280:440", "vol", 0.25),
        sox(*N, "g2.wav", "synth", 1.8, "sine", "440:230", "vol", 0.25),
        _concat(["g1.wav", "g2.wav"], "glide.wav", "tremolo", 5, 30, "fade", "q", 0.4, 3.2, 1.0),
        sox("-m", "voice.wav", "glide.wav", "out.wav", "reverb", 70),
    ]


# A short minor-key music-box tune (Hz): E6 G6 B6 A6 G6 F#6 E6 D#6 E6.
_MUSIC_BOX_NOTES = [1318.5, 1568.0, 1975.5, 1760.0, 1568.0, 1480.0, 1318.5, 1244.5, 1318.5]


def _music_box():
    """Broken music box: high plucked tune, slightly detuned, slowing and warbling."""
    steps, parts = [], []
    for i, freq in enumerate(_MUSIC_BOX_NOTES):
        length = 0.55 if i == len(_MUSIC_BOX_NOTES) - 1 else 0.3 + 0.015 * i  # winding down
        name = "n%d.wav" % i
        steps.append(sox(*N, name, "synth", length, "pluck", freq, "synth", "sine", "mix", round(freq * 1.006, 1),
                         "fade", "l", 0.003, length, length - 0.01))
        parts.append(name)
    steps.append(_concat(parts, "tune.wav", "speed", 0.97, "tremolo", 5, 15))
    steps.append(sox("tune.wav", "out.wav", "pad", 0, 0.5, "reverb", 60))
    return steps


def _evil_giggle():
    """Mischievous high giggle with a bouncing echo."""
    return [
        piper("Hee hee hee hee hee!", "v.wav"),
        sox("v.wav", "out.wav", "pitch", 450, "tempo", 1.15, "echos", 0.8, 0.6, 180, 0.35, 360, 0.2,
            "pad", 0, 0.6, "reverb", 30),
    ]


def _evil_laugh():
    """Deep villain 'mwa-ha-ha' laugh in a big hall."""
    return [
        piper("Mwa ha ha ha ha!", "v.wav"),
        sox("v.wav", "out.wav", "pitch", -450, "tempo", 0.9, "overdrive", 4, "pad", 0, 0.7, "reverb", 70),
    ]


def _whisper_chorus():
    """Two ghostly voices, offset, murmuring 'come and play with us'."""
    return [
        piper("Come and play with us.", "v.wav"),
        sox("v.wav", "a.wav", "pitch", -350, "highpass", 250, "tremolo", 6, 45),
        sox("v.wav", "b.wav", "pitch", -650, "tempo", 0.92, "highpass", 200, "tremolo", 4, 45, "pad", 0.3, 0),
        sox("-m", "a.wav", "b.wav", "out.wav", "pad", 0, 0.6, "reverb", 90),
    ]


def _thunder():
    """Distant thunder: a soft crack then a long low rumble."""
    return [
        sox(*N, "crack.wav", "synth", 0.35, "brownnoise", "lowpass", 1500, "fade", "q", 0.01, 0.35, 0.3),
        sox(*N, "rumble.wav", "synth", 4.2, "brownnoise", "lowpass", 220, "lowpass", 220,
            "tremolo", 2.5, 50, "fade", "q", 0.15, 4.2, 3.2, "pad", 0.1, 0),
        sox("-m", "crack.wav", "rumble.wav", "out.wav", "bass", "+6", "reverb", 40),
    ]


def _clock_slowdown():
    """Tick-tock clock that slows down... and stops."""
    gaps = [0.32, 0.36, 0.42, 0.5, 0.6, 0.74, 0.95]
    steps = [
        sox(*N, "tick.wav", "synth", 0.06, "sine", 1100, "synth", 0.06, "square", "mix", 1900,
            "fade", "q", 0, 0.06, 0.055, "highpass", 500),
        sox(*N, "tock.wav", "synth", 0.06, "sine", 800, "synth", 0.06, "square", "mix", 1350,
            "fade", "q", 0, 0.06, 0.055, "highpass", 400),
    ]
    parts = []
    for i, gap in enumerate(gaps):
        name = "t%d.wav" % i
        steps.append(sox("tick.wav" if i % 2 == 0 else "tock.wav", name, "pad", 0, gap))
        parts.append(name)
    steps.append(_concat(parts, "out.wav", "reverb", 60, 50, 60, 100, 0))
    return steps


def _radio_static():
    """Crackly old radio picking up a voice: 'Is anybody out there?'"""
    return [
        piper("Is anybody... out there?", "v.wav"),
        sox("v.wav", "voice.wav", "pitch", -150, "highpass", 500, "lowpass", 2600, "overdrive", 12,
            "tremolo", 9, 35, "pad", 0.5, 0.4),
        sox(*N, "hiss.wav", "synth", 3.6, "whitenoise", "vol", 0.22, "bandpass", 1800, 1500,
            "tremolo", 13, 60, "fade", "q", 0.1, 3.6, 0.3),
        sox("-m", "voice.wav", "hiss.wav", "out.wav"),
    ]


def _deep_drone():
    """Ominous drone of slightly detuned low tones that throb against each other."""
    return [
        sox(*N, "out.wav", "synth", 4.0, "sine", 110, "synth", "sine", "mix", 112.5,
            "synth", "sine", "mix", 165.4, "synth", "sawtooth", "mix", 55.3,
            "overdrive", 8, "lowpass", 900, "tremolo", 0.5, 30, "fade", "q", 0.8, 4.0, 1.2),
    ]


def _rising_sweep():
    """'Something's coming...': a rising, phasing sweep that cuts off suddenly."""
    return [
        sox(*N, "tone.wav", "synth", 3.0, "sawtooth", "70/900", "lowpass", 2500, "phaser", 0.8, 0.74, 3, 0.4, 0.6, "-t"),
        sox(*N, "noise.wav", "synth", 3.0, "pinknoise", "vol", 0.25, "highpass", 600),
        sox("-m", "tone.wav", "noise.wav", "rise.wav", "fade", "p", 2.8, 3.0, 0.02),
        sox("rise.wav", "out.wav", "pad", 0, 0.5, "reverb", 50),
    ]


def _footsteps():
    """Heavy footsteps slowly getting closer."""
    volumes = [0.25, 0.4, 0.55, 0.75, 1.0]
    steps = [sox(*N, "thud.wav", "synth", 0.22, "brownnoise", "synth", 0.22, "sine", "mix", "150/60",
                 "lowpass", 700, "overdrive", 5, "fade", "q", 0.004, 0.22, 0.19)]
    parts = []
    for i, vol in enumerate(volumes):
        name = "s%d.wav" % i
        steps.append(sox("thud.wav", name, "vol", vol, "pad", 0, 0.48))
        parts.append(name)
    steps.append(_concat(parts, "out.wav", "bass", "+5", "reverb", 35))
    return steps


# --------------------------------------------------------------------------
# Scary pack: creepier, unsettling, still no screams / gore / violence words.
# reverb args: reverberance HF-damping room-scale stereo-depth pre-delay(ms)
# --------------------------------------------------------------------------

def _baby_cry():
    """Distant, wrong-sounding baby cry: pitched-up wails, warbling, a reversed ghost underneath."""
    return [
        piper("Waaaaaah. Waaaaaaah.", "v.wav"),
        sox("v.wav", "c1.wav", "pitch", 850, "tempo", 0.55, "pad", 0, 0.25),
        sox("v.wav", "c2.wav", "pitch", 720, "tempo", 0.5, "bend", "0.9,-250,0.8"),
        _concat(["c1.wav", "c2.wav"], "cry.wav", "tremolo", 6.7, 40, "pad", 0.2, 0),
        sox("cry.wav", "ghost.wav", "reverse", "pitch", -300, "vol", 0.35),
        sox("-m", "cry.wav", "ghost.wav", "mix.wav", "lowpass", 2000, "highpass", 280),
        sox("mix.wav", "out.wav", "pad", 0, 1.0, "reverb", 95, 40, 100, 100, 60),
    ]


def _reversed_whispers():
    """Backwards murmuring that swells up out of nowhere into 'I can see you'."""
    return [
        piper("I can see you.", "v.wav"),
        sox("v.wav", "thin.wav", "pitch", -250, "highpass", 450, "tremolo", 11, 25),
        sox("thin.wav", "back.wav", "reverse", "reverb", 90, 50, 100, 100, 30, "vol", 0.7),
        # Reverse -> reverb -> reverse gives a reverb tail that rises *into* the words.
        sox("thin.wav", "swell.wav", "reverse", "pad", 0, 0.8, "reverb", 95, 30, 100, 100, 0, "reverse"),
        _concat(["back.wav", "swell.wav"], "both.wav"),
        sox("both.wav", "out.wav", "reverb", 60, 50, 80, 100, 20),
    ]


def _children_laugh_wrong():
    """A child's giggle that slows down and sags into an unnatural deep groan."""
    return [
        piper("Hee hee hee hee hee hee!", "v.wav"),
        sox("v.wav", "kid.wav", "pitch", 500),
        sox("kid.wav", "warp.wav", "speed", 0.6, "bend", "0.4,-700,1.8"),
        sox("warp.wav", "out.wav", "chorus", 0.6, 0.9, 50, 0.4, 0.25, 2, "-s",
            "pad", 0, 1.0, "reverb", 90, 50, 100, 100, 50),
    ]


def _breath(length, band, width, vol):
    return sox(*N, "b_%s_%s.wav" % (band, length), "synth", length, "pinknoise", "band", band, width,
               "fade", "q", length * 0.45, length, length * 0.5, "vol", vol)


def _breathing_close():
    """Slow heavy breathing right in your ear (dry)... then the last breath echoes away."""
    inhale, exhale = "b_1400_0.95.wav", "b_700_1.15.wav"
    return [
        _breath(0.95, 1400, 900, 0.7),
        _breath(1.15, 700, 500, 1.0),
        sox(inhale, "in.wav", "pad", 0, 0.1),
        sox(exhale, "out1.wav", "tremolo", 23, 20, "pad", 0, 0.3),
        sox(exhale, "tail.wav", "pad", 0, 0.9, "reverb", 100, 30, 100, 100, 80),
        _concat(["in.wav", "out1.wav", "in.wav", "tail.wav"], "out.wav"),
    ]


def _screech_scrape():
    """Metallic scrape: two clashing high tones grinding through a flanger."""
    return [
        sox(*N, "out.wav", "synth", 2.6, "sawtooth", "1900:2700", "synth", 2.6, "square", "mix", "2650:2050",
            "synth", 2.6, "sine", "amod", "7:19", "bandpass", 2300, 1400, "lowpass", 4200,
            "flanger", 2, 4, -40, 80, 1.3, "phaser", 0.8, 0.74, 4, 0.5, 2, "-t",
            "fade", "q", 0.3, 2.6, 0.5, "pad", 0, 0.6, "reverb", 70, 50, 100, 100, 20),
    ]


def _heartbeat_racing():
    """Heartbeat that races faster and faster... then stops dead."""
    gaps = [0.5, 0.38, 0.3, 0.24, 0.2, 0.17, 0.15]
    steps = [
        sox(*N, "thump.wav", "synth", 0.12, "sine", "110/50", "fade", "q", 0.004, 0.12, 0.1),
        sox("thump.wav", "lub.wav", "pad", 0, 0.08),
    ]
    parts = []
    for i, gap in enumerate(gaps):
        name = "dub%d.wav" % i
        steps.append(sox("thump.wav", name, "vol", 0.65, "pad", 0, gap))
        parts += ["lub.wav", name]
    steps.append(_concat(parts, "beats.wav", "overdrive", 8, "lowpass", 500, "bass", "+6"))
    steps.append(sox("beats.wav", "out.wav", "pad", 0, 0.9))  # ...silence
    return steps


def _dissonant_choir():
    """A ghost choir of 'Aaaah's at clashing pitches in a huge cathedral."""
    shifts = [-1000, -600, -100, 500]  # deliberately clashing intervals
    steps = [piper("Aaaaaaaaaaaah.", "v.wav"),
             sox("v.wav", "long.wav", "tempo", 0.5, "fade", "q", 0.3, "-0", 0.4)]
    parts = []
    for i, cents in enumerate(shifts):
        name = "c%d.wav" % i
        steps.append(sox("long.wav", name, "pitch", cents, "pad", 0.12 * i, 0))
        parts.append(name)
    steps.append(sox("-m", *parts, "mix.wav", "chorus", 0.5, 0.9, 50, 0.4, 0.25, 2, "-t",
                     "60", 0.32, 0.4, 2.3, "-t"))
    steps.append(sox("mix.wav", "out.wav", "pad", 0, 1.5, "reverb", 100, 40, 100, 100, 90))
    return steps


def _bell_toll(name, length):
    """One out-of-tune bell strike: inharmonic sine partials with a long decay."""
    return sox(*N, name, "synth", length, "sine", 110, "synth", length, "sine", "mix", 221.5,
               "synth", length, "sine", "mix", 262, "synth", length, "sine", "mix", 333,
               "synth", length, "sine", "mix", 447, "synth", length, "sine", "mix", 591,
               "fade", "l", 0.003, length, length - 0.01)


def _distant_bell():
    """Slow, detuned church bell tolling twice far away, with a long tail."""
    return [
        _bell_toll("t1.wav", 3.4),
        sox("t1.wav", "t2.wav", "pitch", -35, "pad", 1.9, 0),
        sox("-m", "t1.wav", "t2.wav", "bells.wav", "lowpass", 2500, "tremolo", 3.3, 15),
        sox("bells.wav", "out.wav", "reverb", 95, 60, 100, 100, 40),
    ]


def _static_voice_glitch():
    """Broken radio voice 'We... are... here' that stutters and cuts out."""
    return [
        piper("We... are... here.", "v.wav"),
        sox("v.wav", "voice.wav", "pitch", -250, "highpass", 450, "lowpass", 2600, "overdrive", 15),
        sox("voice.wav", "stut.wav", "trim", 0, 0.16, "repeat", 3, "pad", 0, 0.15),
        sox("voice.wav", "p1.wav", "trim", 0, 0.75),
        sox("voice.wav", "drop.wav", "trim", 0.75, 0.2, "vol", 0),
        sox("voice.wav", "p2.wav", "trim", 0.95, 0.25, "repeat", 1),
        sox("voice.wav", "p3.wav", "trim", 1.2),
        _concat(["stut.wav", "p1.wav", "drop.wav", "p2.wav", "p3.wav"], "glitch.wav",
                "tremolo", 31, 40, "pad", 0.3, 0.4),
        sox(*N, "hiss.wav", "synth", 4.6, "whitenoise", "vol", 0.2, "bandpass", 1800, 1500,
            "tremolo", 17, 70, "fade", "q", 0.1, 4.6, 0.3),
        sox("-m", "glitch.wav", "hiss.wav", "mixed.wav"),
        sox("mixed.wav", "out.wav", "trim", 0, 4.6, "reverb", 40, 50, 60, 100, 10),
    ]


def _sudden_sting():
    """Jump-scare sting: a moment of silence, then a dissonant orchestral-ish stab."""
    return [
        sox(*N, "stab.wav", "synth", 2.4, "sawtooth", 220, "synth", 2.4, "sawtooth", "mix", 233,
            "synth", 2.4, "sawtooth", "mix", 311, "synth", 2.4, "sawtooth", "mix", 466,
            "synth", 2.4, "square", "mix", "82/41",
            "overdrive", 4, "lowpass", 2800, "fade", "l", 0.004, 2.4, 2.3),
        sox("stab.wav", "out.wav", "pad", 1.2, 0.5, "reverb", 90, 40, 100, 100, 10),
    ]


# name -> (one-line description, recipe builder). Order = demo order.
EFFECTS = {
    "heartbeat": ("slow lub-dub heartbeat", _heartbeat),
    "creaky_door": ("old door creaking open", _creaky_door),
    "howling_wind": ("howling wind with a faint whistle", _howling_wind),
    "ghost_moan": ("ghostly 'whooo' moan", _ghost_moan),
    "music_box": ("detuned, winding-down music box tune", _music_box),
    "evil_giggle": ("high mischievous giggle with echo", _evil_giggle),
    "whisper_chorus": ("two ghost voices: 'come and play with us'", _whisper_chorus),
    "thunder": ("distant thunder crack and rumble", _thunder),
    "clock_slowdown": ("tick-tock clock slowing to a stop", _clock_slowdown),
    "radio_static": ("crackly radio voice: 'is anybody out there?'", _radio_static),
    "deep_drone": ("ominous throbbing low drone", _deep_drone),
    "rising_sweep": ("'something's coming' rising sweep", _rising_sweep),
    "footsteps": ("heavy footsteps getting closer", _footsteps),
    "evil_laugh": ("deep villain 'mwa-ha-ha' laugh", _evil_laugh),
    # scary pack
    "baby_cry": ("distant, warbling baby cry drowned in reverb", _baby_cry),
    "reversed_whispers": ("backwards murmur swelling into 'I can see you'", _reversed_whispers),
    "children_laugh_wrong": ("child's giggle slowing and sagging into a deep groan", _children_laugh_wrong),
    "breathing_close": ("heavy breathing in your ear, last breath echoes away", _breathing_close),
    "screech_scrape": ("metallic screeching scrape", _screech_scrape),
    "heartbeat_racing": ("heartbeat racing faster... then stopping dead", _heartbeat_racing),
    "dissonant_choir": ("ghost choir 'Aaaah' at clashing pitches", _dissonant_choir),
    "distant_bell": ("detuned church bell tolling far away", _distant_bell),
    "static_voice_glitch": ("glitching radio voice: 'we... are... here'", _static_voice_glitch),
    "sudden_sting": ("silence, then a dissonant jump-scare stab", _sudden_sting),
}
NAMES = list(EFFECTS)
# The creepier "scary pack" (subset of NAMES), e.g. for play_random(exclude=SCARY_NAMES) with small kids.
SCARY_NAMES = NAMES[NAMES.index("baby_cry"):]


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def path(name):
    """Cache path of an effect's WAV (whether or not it exists yet)."""
    return os.path.join(CACHE_DIR, name + ".wav")


def recipe_hash(name):
    """Short hash of everything that determines how ``name`` sounds."""
    recipe = EFFECTS[name][1]()
    uses_voice = any(step[0] == "piper" for step in recipe)
    blob = json.dumps([recipe, FINAL_CHAIN, COMPAND, QUIET_RMS, RATE, os.path.basename(PIPER_VOICE) if uses_voice else None])
    return hashlib.sha1(blob.encode()).hexdigest()[:16]


def _load_manifest():
    try:
        with open(os.path.join(CACHE_DIR, MANIFEST)) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_manifest(manifest):
    tmp = os.path.join(CACHE_DIR, MANIFEST + ".part")
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    os.replace(tmp, os.path.join(CACHE_DIR, MANIFEST))


def _run_step(step, workdir):
    """Run one recipe step in ``workdir``; raises on failure."""
    if step[0] == "sox":
        cmd, stdin = ["sox", "-V1"] + list(step[1:]), None
    elif step[0] == "piper":
        _, text, out = step
        cmd, stdin = [PIPER_BIN, "-m", PIPER_VOICE, "-f", out], text
    else:
        raise ValueError("unknown step kind %r" % (step[0],))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    res = subprocess.run(cmd, cwd=workdir, input=stdin, capture_output=True, text=True,
                         timeout=STEP_TIMEOUT, env=env)
    if res.returncode != 0:
        raise RuntimeError("%s failed (%d): %s" % (cmd[0], res.returncode, res.stderr.strip()[-300:]))


def _render_one(name, dest):
    """Run ``name``'s recipe and write the normalised result to ``dest`` atomically."""
    with tempfile.TemporaryDirectory(prefix="creepy_fx_") as work:
        for step in EFFECTS[name][1]():
            _run_step(step, work)
        _run_step(sox("out.wav", "-c", 1, "-b", 16, "pre.wav", "rate", RATE, "gain", "-n", "-1"), work)
        level = COMPAND if rms(os.path.join(work, "pre.wav")) < QUIET_RMS else []
        part = dest + ".part.wav"
        _run_step(sox("pre.wav", part, *(level + FINAL_CHAIN)), work)
        os.replace(part, dest)


def rms(wav):
    """RMS amplitude (0..1) of a WAV file, from ``sox stat``; 0.0 if it can't be measured."""
    res = subprocess.run(["sox", wav, "-n", "stat"], capture_output=True, text=True, timeout=STEP_TIMEOUT)
    for line in res.stderr.splitlines():
        if line.startswith("RMS") and "amplitude" in line:
            return float(line.split(":")[1])
    return 0.0


def is_fresh(name, manifest=None):
    """True if ``name`` is cached and was rendered from its current recipe."""
    manifest = _load_manifest() if manifest is None else manifest
    return os.path.isfile(path(name)) and manifest.get(name) == recipe_hash(name)


def render(name, force=False):
    """Render one effect into the cache if needed. Returns its path, or None on failure."""
    if name not in EFFECTS:
        log.error("unknown effect %r", name)
        return None
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        if not force and is_fresh(name):
            return path(name)
        t0 = time.time()
        _render_one(name, path(name))
        manifest = _load_manifest()
        manifest[name] = recipe_hash(name)
        _save_manifest(manifest)
        log.info("rendered %s in %.1fs", name, time.time() - t0)
        return path(name)
    except Exception as exc:  # one bad effect must never take down the show
        log.error("could not render %s: %s", name, exc)
        return None


def render_all(force=False):
    """Render every effect that is missing or stale. Returns {name: path} of the usable ones."""
    out = {}
    for name in NAMES:
        p = render(name, force=force)
        if p:
            out[name] = p
    return out


def duration(name):
    """Length of a rendered effect in seconds, or None if it is not available."""
    try:
        with wave.open(path(name)) as w:
            return w.getnframes() / float(w.getframerate())
    except (OSError, EOFError, wave.Error, KeyError):
        return None


# --------------------------------------------------------------------------
# Playback
# --------------------------------------------------------------------------

def play(name, wait=True):
    """Play an effect with pw-play (rendering it first if needed).

    With ``wait`` it blocks until playback ends. Returns True if playback
    succeeded (or started, when ``wait`` is False) and False on any failure.
    """
    try:
        p = render(name) if name in EFFECTS else None
        if not p:
            log.error("cannot play %r", name)
            return False
        env = dict(os.environ)
        env.setdefault("XDG_RUNTIME_DIR", XDG_RUNTIME_DIR)
        cmd = ["pw-play", p]
        if wait:
            res = subprocess.run(cmd, env=env, capture_output=True, text=True,
                                 timeout=(duration(name) or MAX_SECONDS) + 15)
            if res.returncode != 0:
                log.error("pw-play %s failed: %s", name, res.stderr.strip())
            return res.returncode == 0
        subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as exc:
        log.error("play %s failed: %s", name, exc)
        return False


def play_random(rng=None, exclude=(), wait=True):
    """Play a random effect not in ``exclude``. Returns its name, or None on failure."""
    rng = rng or random
    choices = [n for n in NAMES if n not in set(exclude)]
    if not choices:
        return None
    name = rng.choice(choices)
    return name if play(name, wait=wait) else None


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _cmd_list():
    for name in NAMES:
        d = duration(name)
        print("%-15s %-6s %s" % (name, "%.1fs" % d if d else "-", EFFECTS[name][0]))
    return 0


def _cmd_render():
    done = render_all()
    print("rendered %d/%d effects into %s" % (len(done), len(NAMES), CACHE_DIR))
    return 0 if len(done) == len(NAMES) else 1


def _cmd_demo(gap=1.0):
    done = render_all()
    t0 = time.time()
    for name in NAMES:
        if name not in done:
            continue
        print("Now playing: %s (%s)" % (name.replace("_", " "), EFFECTS[name][0]), flush=True)
        play(name)
        time.sleep(gap)
    print("demo finished in %.1fs" % (time.time() - t0))
    return 0


def main(argv):
    logging.basicConfig(level=logging.INFO, format="creepy_fx: %(message)s")
    if argv[:1] == ["list"]:
        return _cmd_list()
    if argv[:1] == ["render"]:
        return _cmd_render()
    if argv[:1] == ["demo"]:
        return _cmd_demo()
    if len(argv) == 2 and argv[0] == "play":
        return 0 if play(argv[1]) else 1
    print("usage: creepy_fx.py list | render | play NAME | demo\neffects: " + ", ".join(NAMES))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
