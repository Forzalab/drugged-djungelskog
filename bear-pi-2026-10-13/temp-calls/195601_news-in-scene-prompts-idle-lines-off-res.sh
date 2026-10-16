# 2026-10-13T19:56:01.385356Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '1\nrestarting'
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1257 && cp frankie_pipe.py .frankie_pipe.py.bak-1257 && sed -i 's|            if AMBIENT_LINES and random.random() < 1.01:  # 12:05: hardcoded only; scene_cam.py does the live AI scene|            if AMBIENT_LINES and random.random() < 0.0:  # Tony 12:57: no scripted lines, live AI only|' frankie_pipe.py && grep -c "random() < 0.0:" frankie_pipe.py && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''    " never about bodies, race, gender, age or disability. Never mention Claude."
)'''
b='''    " never about bodies, race, gender, age or disability. Never mention Claude."
    # Tony 12:57: report today's news — light, neutral items only (searched 2026-10-13; heavy stories left out on purpose)
    " About one line in three, work in TODAY'S NEWS (Tuesday, October 13, 2026) like a sassy news anchor bear: Netflix is"
    " reportedly cutting about 5 percent of its staff before its October 20 earnings; the US midterm elections are"
    " in November, so everyone is campaigning; Halloween is 18 days away. Stay nonpartisan, never name or mock"
    " politicians, and never joke about deaths, accidents, war or violence."
)'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
python3 -m py_compile scene_cam.py frankie_pipe.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*(scene_cam|frankie)') && echo restarting
