# 2026-10-13T19:12:01.155285Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '12:12:03 [scene_cam] start\n12:12:06 [scene_cam] SAY (3.0s): my glorious god.'
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1212 && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:50]; s=s.replace(a,b)
rep('''                h, w = frame.shape[:2]  # crop the middle where the 'Barnaby Bear' preview window sits (512-px upload)
                frame = frame[int(h * 0.30):int(h * 0.72), int(w * 0.36):int(w * 0.64)]
''','''                # 12:12: no crop — the 'Barnaby Bear' window may be small or maximised; the prompt finds it
''')
rep('''"This is a screenshot of a Raspberry Pi desktop. The small window titled 'Barnaby Bear' is the live camera of "''',
    '''"This is a screenshot of a Raspberry Pi desktop. The window titled 'Barnaby Bear' (small or maximised) shows the live camera of "''')
rep('''"window shows.''','''"window shows (the photo-like outdoor image).''')
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py$') && L=scene_cam.log && S=$(($(wc -l < $L)+1)) && until tail -n +$S $L | grep -q "SAY" || [ $SECONDS -gt 100 ]; do sleep 3; done; tail -n +$S $L | cut -c1-160
