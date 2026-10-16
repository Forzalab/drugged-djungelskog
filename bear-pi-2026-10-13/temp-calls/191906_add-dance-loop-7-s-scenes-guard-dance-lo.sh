# 2026-10-13T19:19:06.494288Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '25:EVERY = float(os.environ.get("SCENE_EVERY", "7"))  # prod mode 12:20: both every 7 s (Gemini 8.6/min < 10)\nguardian-ok'
cd ~/tony-tests && cat > dance_loop.sh <<'EOF'
#!/bin/bash
# dance_loop.sh — prod mode (Tony 12:20): press Try Me every DANCE_EVERY s (default 35; the bear locks ~25 s after a dance).
# Gesture dances from frankie.py still work on top. Stop: touch ~/tony-tests/NO_DANCE. Started/kept alive by guardian.sh.
T=/home/spauly/tony-tests
while [ ! -e "$T/NO_DANCE" ]; do
    "$T/dance_gpio17.sh"
    echo "$(date '+%T') dance_loop: auto dance" >> "$T/pulse_seq.log"
    sleep "${DANCE_EVERY:-35}"
done
EOF
chmod +x dance_loop.sh && bash -n dance_loop.sh && sed -i 's|^EVERY = float(os.environ.get("SCENE_EVERY", "15" if PROVIDER == "gemini" else "10"))|EVERY = float(os.environ.get("SCENE_EVERY", "7"))  # prod mode 12:20: both every 7 s (Gemini 8.6/min < 10)|' scene_cam.py && grep -n '^EVERY' scene_cam.py && python3 -m py_compile scene_cam.py && cp guardian.sh .guardian.sh.bak-1220 && python3 - <<'EOF'
p="/home/spauly/tony-tests/guardian.sh"; s=open(p).read()
a='''    sleep 30
done'''
b='''    if [ ! -e "$T/NO_DANCE" ] && ! pgrep -f '^/bin/bash .*dance_loop[.]sh$' >/dev/null; then
        log "starting dance_loop"
        setsid nohup "$T/dance_loop.sh" >/dev/null 2>&1 < /dev/null &
    fi
    sleep 30
done'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
bash -n guardian.sh && echo guardian-ok
