# 2026-10-13T20:18:53.053361Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'filter on, detectors restarting via guardian'
cd ~/tony-tests && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''r"the image|in this image|i'm sorry|clearly enough|describe", text, re.I):'''
b='''r"the image|in this image|i'm sorry|clearly enough|describe|word limit|headline|riff|prompt|lo siento|"
                               r"no puedo|solicitud|instructions|I can't|I won't|sorry", text, re.I):'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
python3 -m py_compile scene_cam.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py') && echo "filter on, detectors restarting via guardian"
