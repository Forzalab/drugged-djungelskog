# 2026-10-13T20:06:42.291476Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'ok'
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1308 && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:50]; s=s.replace(a,b)
rep('''if PROVIDER == "gemini":  # Tony 12:22''','''if False and PROVIDER == "gemini":  # 13:08: Russian off (Tony: English + Spanish only); was 12:22''')
rep('''        russian = PROVIDER == "gemini"''','''        russian = False  # 13:08: English + Spanish only''')
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py && echo ok
