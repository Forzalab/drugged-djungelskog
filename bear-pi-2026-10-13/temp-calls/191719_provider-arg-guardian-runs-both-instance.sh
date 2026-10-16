# 2026-10-13T19:17:19.237618Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '2:# guardian.sh — keep the show running forever: every 30 s make sure bear_loop.sh (→ frankie.py) and scene_cam.py run.\n15:        if [ ! -e "$T/NO_SCENE" ] && ! pgrep -f "^[^ ]*python -u [^ ]*scene_cam[.]py $prov\\$" >/dev/null; then\n16:            log "starting scene_cam $prov"\n17:            (cd /'
cd ~/tony-tests && sed -i 's|^PROVIDER = os.environ.get("SCENE_PROVIDER", "or")|PROVIDER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SCENE_PROVIDER", "or")  # arg: or / gemini|' scene_cam.py && python3 -m py_compile scene_cam.py && cp guardian.sh .guardian.sh.bak-1218 && python3 - <<'EOF'
p="/home/spauly/tony-tests/guardian.sh"; s=open(p).read()
a='''    if [ ! -e "$T/NO_SCENE" ] && ! pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py$' >/dev/null; then
        log "starting scene_cam"
        (cd /home/spauly/Desktop/barnaby/evil-autonomous-bear-proj && setsid nohup "$PY" -u "$T/scene_cam.py" >/dev/null 2>&1 < /dev/null &)
    fi'''
b='''    for prov in or gemini; do  # two independent scene narrators (12:18): OpenRouter every 10 s, Gemini every 15 s
        if [ ! -e "$T/NO_SCENE" ] && ! pgrep -f "^[^ ]*python -u [^ ]*scene_cam[.]py $prov\\$" >/dev/null; then
            log "starting scene_cam $prov"
            (cd /home/spauly/Desktop/barnaby/evil-autonomous-bear-proj && setsid nohup "$PY" -u "$T/scene_cam.py" "$prov" >/dev/null 2>&1 < /dev/null &)
        fi
    done'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
bash -n guardian.sh && grep -n 'scene_cam' guardian.sh; grep -n "def race\|_gemini(frame" frankie_pipe.py | head
