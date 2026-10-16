# 2026-10-13T19:21:09.091171Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'restarting via guardian (≤30 s)'
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1222 && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:50]; s=s.replace(a,b)
rep('''    "If the camera window is not visible, reply exactly: NONE"
)''','''    "If the camera window is not visible, reply exactly: NONE"
    # Tony 12:22: the crowd LOVES 'morons' and 'idiots' — more crass, stand-up comedy style
    " STYLE: stand-up comic doing crowd work: a quick setup then a punchline that lands, roast the crowd and the scene,"
    " crass and blunt; calling people morons, idiots, clowns or nerds is welcome. Still never slurs, nothing sexual,"
    " never about bodies, race, gender, age or disability."
)
if PROVIDER == "gemini":  # Tony 12:22: let it speak Russian — this narrator is the Russian one
    PROMPT += (" You speak with a thick Russian accent persona: sprinkle 1-2 real Russian words per line (da, nyet,"
               " comrade, tovarishch, bozhe moi, babushka), Soviet-robot-bear jokes welcome. Mostly English so people understand.")''')
rep('''        fv._synth(fv.BRITISH, text, raw)
        fv._sox(raw, "-r", "22050", "-c", "1", out, "tempo", "0.88", "pitch", "-120", "overdrive", "4", "8",''',
'''        russian = PROVIDER == "gemini"
        fv._synth(fv.RUSSIAN if russian else fv.BRITISH, text, raw)
        fv._sox(raw, "-r", "22050", "-c", "1", out, "tempo", "0.9" if russian else "0.88",
                "pitch", "-200" if russian else "-120", "overdrive", "5" if russian else "4", "8",''')
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py') && echo "restarting via guardian (≤30 s)"
