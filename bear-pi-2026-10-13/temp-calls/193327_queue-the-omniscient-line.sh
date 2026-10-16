# 2026-10-13T19:33:27.120038Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'played 12:33:44'
cd ~/Desktop/barnaby/evil-autonomous-bear-proj && timeout 150 .venv/bin/python -c "
import sys,subprocess,time,tempfile,fcntl; sys.path.insert(0,'/home/spauly/tony-tests'); import frankie_voice as fv
out=tempfile.mkdtemp()+'/o.wav'
fv.render('I bet two people are standing behind me right now. I am omniscient.', None, out)
with open('/home/spauly/tony-tests/.speak.lock','w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    for _ in range(60):
        if subprocess.run(['pgrep','-x','pw-play'],stdout=subprocess.DEVNULL).returncode: break
        time.sleep(0.5)
    subprocess.run(['pw-play',out]); print('played', time.strftime('%T'))" 2>&1 | grep -v Piper
