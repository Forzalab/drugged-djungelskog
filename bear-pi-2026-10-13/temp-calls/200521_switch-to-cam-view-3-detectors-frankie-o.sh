# 2026-10-13T20:05:21.908999Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'cam_view.py\nscene_cam.py or\nscene_cam.py gemini\nscene_cam.py or2\n8134 13:05:46 cam.jpg\n2026-10-13 12:56:13 guardian: starting scene_cam gemini\n2026-10-13 13:05:26 guardian: start (pid 13901)\n2026-10-13 13:05:26 guardian: starting cam_view\n2026-10-13 13:05:26 guardian: starting scene_cam or\n2026-10-1'
cd ~/tony-tests && cp guardian.sh .guardian.sh.bak-1304 && python3 - <<'EOF'
p="/home/spauly/tony-tests/guardian.sh"; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:50]; s=s.replace(a,b)
rep('''    for prov in or gemini; do''','''    # 13:04: plain camera feed for the detectors when Frankie (McKay code) is off. One camera = one process.
    if [ -e "$T/NO_BEAR" ] && [ ! -e "$T/NO_CAM" ] && ! pgrep -f '^[^ ]*python -u [^ ]*cam_view[.]py$' >/dev/null \\
       && ! pgrep -f '^[^ ]*python -u [^ ]*frankie[.]py' >/dev/null; then
        log "starting cam_view"
        setsid nohup "$PY" -u "$T/cam_view.py" >/dev/null 2>&1 < /dev/null &
    fi
    for prov in or gemini or2; do''')
open(p,"w").write(s)
EOF
bash -n guardian.sh && touch NO_BEAR && kill $(pgrep -f '^/bin/bash /home/spauly/tony-tests/guardian[.]sh$') 2>/dev/null; kill $(pgrep -f '^/bin/bash .*bear_loop[.]sh$') $(pgrep -f '^[^ ]*python -u [^ ]*(frankie|scene_cam)') 2>/dev/null; sleep 4; setsid nohup /home/spauly/tony-tests/guardian.sh >/dev/null 2>&1 < /dev/null & sleep 20; pgrep -af '^/bin/bash .*(dance_loop|bear_loop)[.]sh$|^[^ ]*python -u [^ ]*(scene_cam|frankie|polyglot|cam_view)' | sed 's|.*tony-tests/||'; ls -la --time-style=+%T cam.jpg | cut -c30-; tail -6 boot.log | grep guardian
