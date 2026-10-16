"""horror.py — Frankie the bear's ~60 s spooky-fun horror show (kid-safe): drone, heartbeat, footsteps, whispers,
jump scare + dance, gremlin giggles, music box, a glitch, dance again, then a baby goodbye from Frankie.
Frankie = high, baby-like 'baby' voice. Ambient fx get extra reverb (cached in fx_verb/).
Voices: bear_voices.say() (clear EQ). Sounds: creepy_fx's cached wavs. Dance: dance_gpio17.sh. No wheels.
Run:  ~/tony-tests/horror            (wrapper: McKay's venv python, read-only use)
Env:  DRY=1 log every step on a simulated clock (no GPIO, no sound)   NO_DANCE=1 skip the two dances
Log:  stdout + ~/tony-tests/horror.log
"""
import logging, os, random, signal, subprocess, sys, time
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
HERE = Path.home() / "tony-tests"
sys.path.insert(0, str(HERE))
import creepy_fx
import gremlin_show as g  # only DRY + voice() preload (NOT its dance/wheels/idle_pins: old pins)
import bear_voices as bv

LOG = HERE / "horror.log"
DANCE_SH = HERE / "dance_gpio17.sh"
DRY = g.DRY
NO_DANCE = os.environ.get("NO_DANCE") == "1"
VERB_DIR = HERE / "fx_verb"  # reverbed copies of the creepy_fx wavs (made on first use)
VERB = ["pad", "0", "2.5", "reverb", "90", "40", "100", "100", "20", "0", "gain", "-n", "-1"]
# Frankie: high, slow, baby-like (+ the same legibility EQ as every bear_voices voice)
bv.VOICES["baby"] = ["pitch", "+750", "tempo", "0.8", "tremolo", "5", "8", "reverb", "20"] + bv.CLEAR
LOCKOUT = 25.0  # Try Me button ignores presses for ~25 s after a dance
# Seconds per word for each voice (measured on the Pi incl. Piper synth time), only used for the DRY clock.
VOICE_RATE = {"baby": 0.6, "ghost": 0.47, "zombie": 0.5, "narrator": 0.38, "gremlin": 0.42, "kawaii": 0.57}
rng = random.Random(31)  # fixed seed: the glitch sounds the same every show


def meta_line(word):
    """(voice, text) of the bear_voices.LINES entry containing ``word``."""
    return next(line for line in bv.LINES if word in line[1])


T0 = time.monotonic()
_skipped = 0.0      # simulated seconds added by pause() in DRY
_bg = []            # pw-play processes started by under(), killed on exit
_last_dance = None  # show time of the last dance


def now():
    return time.monotonic() - T0 + _skipped


def pause(secs):
    """Sleep LIVE; in DRY just advance the simulated show clock."""
    global _skipped
    if secs <= 0:
        return
    if DRY:
        _skipped += secs
    else:
        time.sleep(secs)


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} [+{now():5.1f}s] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def safe(label, fn, *args):
    """Run one show step; a failure is logged and the show goes on."""
    try:
        fn(*args)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log(f"  ! {label} failed: {e!r}")


# ---------------------------------------------------------------- sound + voice

def verb(name):
    """Path of the reverbed copy of an effect (sox once, then cached in fx_verb/)."""
    src = creepy_fx.path(name)
    if not os.path.isfile(src):
        src = creepy_fx.render(name)
    out = VERB_DIR / f"{name}.wav"
    if not out.is_file() or out.stat().st_mtime < os.path.getmtime(src):
        VERB_DIR.mkdir(exist_ok=True)
        subprocess.run(["sox", src, str(out), *VERB], check=True, timeout=60,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(out)


def _fx(name):
    dur = creepy_fx.duration(name) or 2.0
    log(f"FX: {name} ({dur:.1f}s)")
    if DRY:
        pause(dur)
        return
    _bg.append(subprocess.Popen(["pw-play", verb(name)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    time.sleep(dur)  # move on at the dry end; the reverb tail rings under the next step


def _bg_fx(name):
    log(f"FX bg: {name} ({creepy_fx.duration(name) or 0:.1f}s)")
    if DRY:
        return
    _bg.append(subprocess.Popen(["pw-play", verb(name)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))


def play(name):
    """Play a cached effect and wait for it."""
    safe(f"fx {name}", _fx, name)


def under(name):
    """Start an effect in the background (layered under what follows) and return immediately."""
    safe(f"bg {name}", _bg_fx, name)


def say(voice, text):
    log(f'{voice.upper()}: "{text}"')
    if DRY:
        pause(0.2 + VOICE_RATE.get(voice, 0.45) * len(text.split()))
    else:
        bv.say(voice, text)  # never raises


def glitch(text):
    log(f'GLITCH: "{text}"')
    if DRY:
        pause(0.5 + 0.5 * len(text.split()))
    else:
        bv.glitch_say(text, rng)  # never raises


# ---------------------------------------------------------------- bear

def dance(n):
    """Press Try Me via the GPIO17 relay; waits out the ~25 s lockout if the last dance was too recent."""
    global _last_dance
    if _last_dance is not None and now() - _last_dance < LOCKOUT:
        wait = LOCKOUT - (now() - _last_dance)
        log(f"WAIT {wait:.1f}s (Try Me lockout: dance #{n} >= {LOCKOUT:.0f}s after the last)")
        pause(wait)
    _last_dance = now()
    if NO_DANCE:
        log(f"DANCE #{n} skipped (NO_DANCE=1)")
        return
    log(f"DANCE #{n} (dance_gpio17.sh)")
    if DRY:
        pause(0.4)
        return
    try:
        subprocess.run([str(DANCE_SH)], check=True, timeout=10)
    except Exception as e:
        log(f"  ! dance #{n} failed: {e!r}")


# ---------------------------------------------------------------- show

def show():
    log("--- ACT 1: the dark ---")
    under("deep_drone")
    if not DRY:
        safe("load voice", g.voice)  # ~3.5 s Piper load, hidden under the drone
    play("heartbeat")
    under("footsteps")
    pause(2.0)
    under("creaky_door")
    pause(0.6)
    say("ghost", "Frankie is waking up...")
    pause(0.5)
    say("zombie", "I can see you...")
    under("rising_sweep")
    pause(1.85)
    under("sudden_sting")            # 1.2 s of silence, then the stab: lands right as the sweep cuts off
    pause(1.15)

    log("--- ACT 2: the scare ---")
    under("thunder")
    dance(1)
    play("evil_laugh")
    say("baby", "Hiii! I'm Frankie! I'm a baby bear! I was born yesterday!")
    say("baby", "Wanna dance with me? Hehehe!")
    under("music_box")
    say("narrator", "Listen... the music box plays all by itself...")
    pause(0.8)
    play("evil_giggle")
    say(*meta_line("tape"))          # gremlin: held together with tape
    play("reversed_whispers")
    play("clock_slowdown")           # tick... tock... stops. Silence until the button unlocks.

    log("--- ACT 3: finale ---")
    under("dissonant_choir")
    dance(2)
    pause(2.0)
    glitch("The toys are waking up... all of them...")
    say(*meta_line("Happy Halloween"))  # ghost: did I scare you? I am one day old.
    under("distant_bell")
    say("gremlin", "Hehehe... Frankie never sleeps...")
    pause(1.0)
    say("baby", "Bye bye, friends! Frankie loves you! Come back soon!")


# ---------------------------------------------------------------- cleanup

def cleanup():
    for p in _bg:
        try:
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    p.kill()
        except Exception as e:
            log(f"  ! could not stop pw-play {p.pid}: {e!r}")
    cmds = [["pinctrl", "set", "13,16,19,20,21,26", "ip", "pd"],  # wheel pins idle
            ["pinctrl", "set", "17", "op", "dh"]]                  # relay rest state (held closed)
    for cmd in cmds:
        if DRY:
            log(f"CLEANUP (dry): would run {' '.join(cmd)}")
            continue
        try:
            subprocess.run(cmd, timeout=5)
            log(f"CLEANUP: {' '.join(cmd)}")
        except Exception as e:
            log(f"  ! cleanup {' '.join(cmd)} failed: {e!r}")


def on_signal(sig, frame):
    raise KeyboardInterrupt


def main():
    global T0
    logging.basicConfig(level=logging.WARNING, format="creepy_fx: %(message)s")
    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, on_signal)
    T0 = time.monotonic()
    mode = "DRY, simulated clock" if DRY else "LIVE"
    log(f"=== horror show start ({mode}, dances {'off' if NO_DANCE else 'ON'}) ===")
    try:
        show()
        log("=== show complete ===")
    except KeyboardInterrupt:
        log("INTERRUPTED")
    except Exception as e:
        log(f"ERROR: {e!r}")
    finally:
        for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(s, signal.SIG_IGN)  # a second Ctrl-C must not skip the cleanup
        cleanup()
        log(f"=== end, total {now():.1f}s ===")


if __name__ == "__main__":
    main()
