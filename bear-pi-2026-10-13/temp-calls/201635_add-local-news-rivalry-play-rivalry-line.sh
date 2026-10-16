# 2026-10-13T20:16:35.848162Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'detectors-restarting\nplayed 13:16:56'
cd ~/tony-tests && cat >> news_manual.txt <<'EOF'
# 13:12 local (TinyFish) + rivalry (Tony): Frankie is a Boise State fan, roasts Fresno State (PG-13)
Clovis police got a 79 thousand dollar grant to stop stores selling alcohol to minors, so good luck with that fake ID
The big Asics Clovis Invitational cross country meet just ran at Woodward Park in Fresno
Glory to Boise State. Fresno State? Never heard of her
Boise State has a blue football field and Fresno State has a participation trophy
Fresno State Bulldogs? More like Fresno State Bull-dogs-who-lose. Glory to Boise State
EOF
cp scene_cam.py .scene_cam.py.bak-1313 && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''    " never about bodies, race, gender, age or disability. Never mention Claude."'''
b='''    " never about bodies, race, gender, age or disability. Never mention Claude."
    " You are a die-hard Boise State fan: about one line in four, shout 'Glory to Boise State' and roast Fresno State"
    " (PG-13 trash talk like 'screw Fresno State', 'Fresno State is mid'; no f-word)."'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
python3 -m py_compile scene_cam.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py') && echo detectors-restarting
cd ~/Desktop/barnaby/evil-autonomous-bear-proj && timeout 150 .venv/bin/python -c "
import sys,subprocess,time,tempfile,fcntl; sys.path.insert(0,'/home/spauly/tony-tests'); import frankie_voice as fv
out=tempfile.mkdtemp()+'/o.wav'
fv.render('Glory to Boise State! Screw Fresno State! Fresno State is mid!', None, out)
with open('/home/spauly/tony-tests/.speak.lock','w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    for _ in range(60):
        if subprocess.run(['pgrep','-x','pw-play'],stdout=subprocess.DEVNULL).returncode: break
        time.sleep(0.5)
    subprocess.run(['pw-play',out]); print('played', time.strftime('%T'))" 2>&1 | grep -v Piper
