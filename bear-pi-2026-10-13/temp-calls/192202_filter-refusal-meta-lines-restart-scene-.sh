# 2026-10-13T19:22:02.548184Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'restarting via guardian'
cd ~/tony-tests && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''                elif text.lower() in (r.lower() for r in recent):'''
b='''                elif re.search(r"camera feed|can't (make out|see|tell)|cannot|unable to|as an ai|screenshot|"
                               r"the image|in this image|i'm sorry|clearly enough|describe", text, re.I):
                    log(f"skipped AI-speak: {text}")
                elif text.lower() in (r.lower() for r in recent):'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
python3 -m py_compile scene_cam.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py') && echo "restarting via guardian"
