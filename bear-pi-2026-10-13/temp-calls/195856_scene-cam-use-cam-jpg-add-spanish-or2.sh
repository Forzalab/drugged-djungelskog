# 2026-10-13T19:58:56.875584Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '50:if PROVIDER == "or2":  # 13:00: third detector, Spanish\n113:        if PROVIDER == "or2":  # 13:00: third detector speaks Spanish\n143:            if frame is None:'
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1300 && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:50]; s=s.replace(a,b)
rep('''            with tempfile.TemporaryDirectory(prefix="scam-") as d:
                png = f"{d}/s.png"
                subprocess.run(["grim", png], check=True, timeout=10)
                frame = cv2.imread(png)
            prompt = PROMPT''','''            cam = HERE / "cam.jpg"  # 13:00: plain camera frame from cam_view.py (no McKay code); screenshot as fallback
            frame = cv2.imread(str(cam)) if cam.is_file() and time.time() - cam.stat().st_mtime < 5 else None
            if frame is None:
                with tempfile.TemporaryDirectory(prefix="scam-") as d:
                    png = f"{d}/s.png"
                    subprocess.run(["grim", png], check=True, timeout=10)
                    frame = cv2.imread(png)
            prompt = PROMPT''')
rep('''        russian = PROVIDER == "gemini"
        fv._synth(fv.RUSSIAN if russian else fv.BRITISH, text, raw)''','''        russian = PROVIDER == "gemini"
        voice = fv.RUSSIAN if russian else fv.BRITISH
        if PROVIDER == "or2":  # 13:00: third detector speaks Spanish
            voice = fv.VOICES / "es_MX-ald-medium.onnx"
        fv._synth(voice, text, raw)''')
rep('''if PROVIDER == "gemini":  # Tony 12:22''','''if PROVIDER == "or2":  # 13:00: third detector, Spanish
    PROMPT += " Reply ENTIRELY in Spanish (Mexican Spanish), same crass sassy stand-up style."
if PROVIDER == "gemini":  # Tony 12:22''')
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py cam_view.py && grep -n "frame is None\|or2" scene_cam.py | head
