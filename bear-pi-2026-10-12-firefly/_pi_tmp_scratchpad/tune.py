import os, random, subprocess, sys

D = "/tmp/claude-1000/-home-spauly/13fd41a3-e900-5f1e-92e6-713e284d19d2/scratchpad/tunes"
RATE = 22050

def sox(*args):
    subprocess.run(["sox", "-q", *args], check=True)

def make_tune(name, root_hz, steps, lo, hi, n_notes, tempo_scale, seed):
    rnd = random.Random(seed)
    # steps: semitone offsets of the scale; build a 2-octave pitch table
    table = []
    for octv in range(2):
        for s in steps:
            table.append(root_hz * 2 ** ((s + 12 * octv) / 12.0))
    idx = rnd.randrange(len(table) // 2)
    parts = []
    bass_parts = []
    beat_t = 0.0
    bar_t = 0.0
    bar_notes = 0
    bass_hz = root_hz / 2
    bar_start = 0.0
    n = 0
    i = 0
    while i < n_notes:
        if rnd.random() < 0.12:
            dur = rnd.uniform(0.25, 0.45) * tempo_scale
            p = f"{D}/{name}_{i:03d}_rest.wav"
            sox("-n", "-r", str(RATE), "-c", "1", p, "trim", "0", f"{dur:.3f}")
            parts.append(p)
            beat_t += dur
            i += 1
            continue
        step = rnd.choice([-2, -1, -1, 1, 1, 2, 0])
        idx = min(max(idx + step, 0), len(table) - 1)
        freq = table[idx]
        dur = rnd.uniform(0.15, 0.35) * tempo_scale
        p = f"{D}/{name}_{i:03d}.wav"
        sox("-n", "-r", str(RATE), "-c", "1", p,
            "synth", f"{dur:.3f}", "pluck", f"{freq:.2f}",
            "fade", "0", f"{dur:.3f}", "0.02", "0.10", "vol", "0.5")
        parts.append(p)
        beat_t += dur
        i += 1
    melody = f"{D}/{name}_melody.wav"
    sox(*parts, melody)
    total = beat_t
    # bass: one note per ~1.2 s bar, sine with soft fade
    t = 0.0
    k = 0
    bparts = []
    bar_len = 1.2 * tempo_scale
    while t < total:
        bp = f"{D}/{name}_bass_{k:03d}.wav"
        sox("-n", "-r", str(RATE), "-c", "1", bp,
            "synth", f"{bar_len:.3f}", "sine", f"{bass_hz:.2f}",
            "fade", "0", f"{bar_len:.3f}", "0.05", "0.20", "vol", "0.5")
        bparts.append(bp)
        t += bar_len
        k += 1
        bass_hz = root_hz / 2 * (2 ** (rnd.choice(steps) / 12.0))
    bass = f"{D}/{name}_bass.wav"
    sox(*bparts, bass)
    mixed = f"{D}/{name}_mix.wav"
    # mix melody (louder) with bass (quieter), trim to melody length, reverb, quiet
    bass_t = f"{D}/{name}_bass_t.wav"
    sox(bass, bass_t, "trim", "0", f"{total:.3f}")
    sox("-m", melody, "-v", "0.3", bass_t, mixed, "reverb", "25", "vol", "0.25")
    out = f"{D}/{name}.wav"
    sox(mixed, out, "vol", "0.25")
    return out, total

# Tune A: C major pentatonic, quicker tempo
C_PENT = [0, 2, 4, 7, 9]
# Tune B: G major pentatonic, relaxed tempo
G_PENT = [0, 2, 4, 7, 9]
seed = random.SystemRandom().randrange(1, 10**9)
a, la = make_tune("tuneA", 261.63, C_PENT, 0, 9, 52, 1.0, seed)
b, lb = make_tune("tuneB", 392.00, G_PENT, 0, 9, 48, 1.0, seed + 1)

gap = f"{D}/gap.wav"
sox("-n", "-r", str(RATE), "-c", "1", gap, "trim", "0", "1")
final = f"{D}/cheer.wav"
sox(a, gap, b, final)
print(f"tuneA {la:.2f}s tuneB {lb:.2f}s total~{la+lb+1:.2f}s")
