# 2026-10-13T19:00:49.070380Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'def render_ultron(text):\n    """British voice only, slow, slightly low and distorted; returns a wav path (last 5 kept)."""\n    import frankie_voice as fv\n    ULTRON_DIR.mkdir(exist_ok=True)\n    out = ULTRON_DIR / f"u{int(time.time())}.wav"\n    raw = str(out) + ".raw.wav"\n    fv._synth(fv.BRITISH, te'
cd ~/tony-tests && cp frankie_pipe.py .frankie_pipe.py.bak-1201 && sed -n 436,452p frankie_pipe.py && python3 - <<'EOF'
p="/home/spauly/tony-tests/frankie_pipe.py"; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:50]; s=s.replace(a,b)
rep('ULTRON_EVERY = 45.0     # Tony STEM-day outdoors: 75→45','ULTRON_EVERY = 15.0     # Tony 12:01: describe the scene every 15 s (was 45)')
rep('            if AMBIENT_LINES and random.random() < 0.5:','            if AMBIENT_LINES and random.random() < 0.25:  # Tony 12:01: mostly live AI scene (was 0.5)')
rep('''    howl = Path.home() / "tony-tests" / "howl.wav"  # reverb wolf howl opens every Ultron line (Tony 11:17)
    if howl.is_file():''','''    howl = Path.home() / "tony-tests" / "howl.wav"  # reverb wolf howl, now ~1 in 4 scan lines (every 15 s would be too much)
    if howl.is_file() and random.random() < 0.25:''')
rep('''    "(a booth at Clovis Community College STEM day) and the strings, tape and wires holding you. PG-13, plain words, "
    "no emojis, no stage directions."
)''','''    "(a booth at Clovis Community College STEM day) and the strings, tape and wires holding you. PG-13, plain words, "
    "no emojis, no stage directions."
    # Tony 12:01: every 15 s, Halloween, self-aware, crass and sassy
    " NEW STYLE, overrides the one-sentence rule: describe the scene you see RIGHT NOW in up to 2 sentences, 25 words:"
    " spooky Halloween framing, VERY self-aware (you are a taped robot bear outdoors on the grass watching the booths),"
    " crass and sassy diva-bear attitude: blunt, rude-funny, eye-rolling, roast the scene. No slurs, nothing sexual,"
    " never about anyone's body, race, gender or age. Never repeat your last lines."
)''')
open(p,"w").write(s)
EOF
python3 -m py_compile frankie_pipe.py && grep -n "words\]\|split()\[:16\]" frankie_pipe.py | head -3
