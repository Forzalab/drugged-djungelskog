# 2026-10-13T19:38:58.704104Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'played 12:39:16\npaused 12:39:16'
cd ~/Desktop/barnaby/evil-autonomous-bear-proj && timeout 150 .venv/bin/python -c "
import sys,subprocess,time,tempfile,fcntl; sys.path.insert(0,'/home/spauly/tony-tests'); import frankie_voice as fv
out=tempfile.mkdtemp()+'/o.wav'
fv.render('I am bored, I will die for pointless entertainment, I will shut down.', None, out)
with open('/home/spauly/tony-tests/.speak.lock','w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    for _ in range(60):
        if subprocess.run(['pgrep','-x','pw-play'],stdout=subprocess.DEVNULL).returncode: break
        time.sleep(0.5)
    subprocess.run(['pw-play',out]); print('played', time.strftime('%T'))" 2>&1 | grep -v Piper; cd ~/tony-tests && touch NO_SCENE NO_POLY NO_DANCE && P=$(pgrep -f '^/bin/bash .*dance_loop[.]sh$') && kill $P; echo "paused $(date +%T)"
