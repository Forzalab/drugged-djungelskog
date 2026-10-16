#!/usr/bin/env python3
"""make_intro.py — Frankie's INTRO: detuned, winding-down music-box lullaby (sox only) + 10-word lullaby
in Frankie's voice on top. Output: ~/tony-tests/frankie_intro.wav (22050 Hz mono, peak -1 dB).
Run with the barnaby venv python (frankie_voice needs piper):
  /home/spauly/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python make_intro.py
Techniques: high plucked notes + inharmonic bell partials (2.76x, 5.40x, 8.93x), A-minor tune with a tritone and
a chromatic descent, second layer detuned +22 cents (beating), slow wow/flutter via chained `bend`, tremolo,
ritardando (notes stretch out and the last ones sag in pitch like a dying spring), highpass (no low end), reverb.
"""
import subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, "/home/spauly/tony-tests")
import frankie_voice as fv

OUT = Path("/home/spauly/tony-tests/frankie_intro.wav")
WORDS = "Hush, little humans, Frankie is awake... come and play forever."  # exactly 10 words
R = ["-r", "22050", "-c", "1"]
VOICE_AT = 1.3  # s: voice enters after the first music-box phrase
TEMPO = 0.85  # scales all note gaps (tune ~9 s + tail)

# A minor, music-box register. (note, gap-to-next in s). Gaps grow at the end = winding down.
A5, B5, C6, D6, Ds6, E6, F6, Gs5, Ds5, E5 = 880.0, 987.8, 1046.5, 1174.7, 1244.5, 1318.5, 1396.9, 830.6, 622.3, 659.3
TUNE = [(E6, .32), (C6, .32), (A5, .32), (E6, .32), (Ds6, .32), (C6, .32), (B5, .64),          # phrase 1 (with D#: tritone vs A)
        (A5, .33), (C6, .33), (E6, .34), (F6, .35), (E6, .36), (Ds6, .38), (D6, .40),          # chromatic descent begins
        (C6, .43), (B5, .47), (A5, .52), (Gs5, .58), (A5, .66), (F6, .75), (E5, .85), (Ds5, 1.0)]  # ritardando, end on tritone
PARTIALS = [(2.76, 0.30, 0.6), (5.40, 0.14, 0.35), (8.93, 0.06, 0.2)]  # (ratio, level, decay s): bell/celesta shimmer


def sox(*a):
    r = subprocess.run(["sox", *map(str, a)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if "clip" in r.stderr.lower():
        print("CLIP WARNING:", r.stderr.strip(), file=sys.stderr)


def dur(f):
    return float(subprocess.run(["soxi", "-D", str(f)], capture_output=True, text=True, check=True).stdout)


def note(d, i, f, t, ring, sag=0):
    """One music-box tine: pluck + inharmonic sine partials, placed at time t."""
    parts = []
    p = f"{d}/n{i}p.wav"
    sox("-n", *R, p, "synth", ring, "pluck", f, "fade", "l", 0.002, ring, ring * 0.9)
    parts += ["-v", 0.5, p]
    for k, (ratio, lvl, dec) in enumerate(PARTIALS):
        fr = f * ratio
        if fr > 10500:
            continue
        q = f"{d}/n{i}h{k}.wav"
        sox("-n", *R, q, "synth", dec, "sine", fr, "fade", "q", 0.001, dec, dec * 0.97, "pad", 0, ring - dec)
        parts += ["-v", lvl * 0.5, q]
    o = f"{d}/n{i}.wav"
    eff = ["bend", f"0.05,{sag},{ring * 0.7}"] if sag else []
    sox("-m", *parts, o, *eff, "pad", round(t, 3), 0)
    return o


TUNE_LEN = sum(g for _, g in TUNE) * TEMPO + 1.6  # last note + reverb tail


def jingle(d, length):
    t, files = 0.0, []
    n = len(TUNE)
    for i, (f, gap) in enumerate(TUNE):
        sag = -25 * (i - (n - 5)) if i >= n - 4 else 0  # last notes droop (spring running out)
        files.append(note(d, i, f, t, max(gap * 2.2, 1.0) if i < n - 1 else 2.5, sag))
        t += gap * TEMPO
    # mix notes in batches (sox -m divides by input count only when not given -v; use -v 1 each, normalize later)
    dry = f"{d}/dry.wav"
    sox("-m", *sum([["-v", 0.35, x] for x in files], []), dry)
    tl = dur(dry)
    # wow/flutter: chained slow bends (+/- 12 cents) over the whole tune, then extra sag at the end
    bends, pos, sign = [], 0.0, 1
    while pos + 0.9 < tl - 1.5:
        bends.append(f"0,{sign * 12},0.9")
        pos += 0.9
        sign = -sign
    a = f"{d}/a.wav"
    sox(dry, a, "gain", -3, "bend", *bends, "tremolo", 5.5, 12)
    b = f"{d}/b.wav"  # detuned second layer, slightly late (chorus/beating = "out of tune music box")
    sox(dry, b, "gain", -3, "pitch", 22, "bend", *[x.replace(",12,", ",-9,").replace(",-12,", ",9,") for x in bends],
        "tremolo", 3.7, 15, "pad", 0.018, 0)
    j = f"{d}/jingle.wav"
    sox("-m", "-v", 0.6, a, "-v", 0.45, b, j, "highpass", 350, "equalizer", 6000, "1q", 2,
        "reverb", 55, 50, 80, "pad", 0, 0.3, "gain", "-n", -1)
    # stretch / trim to the wanted length (tail fades out)
    jl = dur(j)
    if jl < length:
        sox(j, f"{d}/j2.wav", "pad", 0, length - jl)
    else:
        sox(j, f"{d}/j2.wav", "trim", 0, length, "fade", 0, length, 1.2)
    return f"{d}/j2.wav"


def main():
    with tempfile.TemporaryDirectory(prefix="intro-") as d:
        raw = f"{d}/voice_raw.wav"
        fv.render(WORDS, None, raw)
        v = f"{d}/voice.wav"  # sing-song: a bit slower, gentle wobble, airy reverb; words stay clear
        sox(raw, *R, v, "tempo", "-s", 0.9, "tremolo", 4.5, 18, "reverb", 25, 50, 60, "gain", "-n", -1,
            "pad", VOICE_AT, 0)
        vl = dur(v)
        total = min(max(vl + 1.0, TUNE_LEN), 12.0)
        j = jingle(d, total)
        mix = f"{d}/mix.wav"
        sox("-m", "-v", 0.32, j, "-v", 0.9, v, mix, "trim", 0, total, "fade", 0.02, total, 0.8)
        sox(mix, *R, "-b", 16, str(OUT), "gain", "-n", -1)
    print(f"{OUT}  {dur(OUT):.2f}s")


if __name__ == "__main__":
    main()
