# 2026-10-13T19:29:32.294979Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'played 12:29:53'
cd ~/Desktop/barnaby/evil-autonomous-bear-proj && timeout 120 .venv/bin/python -c "
import sys,subprocess,time,tempfile,fcntl; sys.path.insert(0,'/home/spauly/tony-tests'); import frankie_voice as fv
out=tempfile.mkdtemp()+'/o.wav'
fv.render('Drag me to the robot dog. Let me devour it.', None, out)
with open('/home/spauly/tony-tests/.speak.lock','w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    for _ in range(60):
        if subprocess.run(['pgrep','-x','pw-play'],stdout=subprocess.DEVNULL).returncode: break
        time.sleep(0.5)
    subprocess.run(['pw-play',out]); print('played', time.strftime('%T'))" 2>&1 | grep -v Piper
