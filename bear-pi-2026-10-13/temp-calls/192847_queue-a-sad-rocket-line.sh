# 2026-10-13T19:28:47.332895Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'played 12:29:03'
cd ~/Desktop/barnaby/evil-autonomous-bear-proj && timeout 120 .venv/bin/python -c "
import sys,subprocess,time,tempfile,fcntl; sys.path.insert(0,'/home/spauly/tony-tests'); import frankie_voice as fv
d=tempfile.mkdtemp(); raw=d+'/r.wav'; out=d+'/o.wav'
fv._synth(fv.BRITISH,'The rocket will hurt me... I will be sad.',raw)
# sad: slow, a little lower, wobbly (trembling voice), soft echo
fv._sox(raw,'-r','22050','-c','1',out,'tempo','0.72','pitch','-60','tremolo','5','30','echo','0.8','0.7','80','0.2','highpass','150','compand','0.005,0.08','6:-60,-30,-15','-4','-90','0.01','equalizer','2800','1.0q','+6','gain','-n','-1')
with open('/home/spauly/tony-tests/.speak.lock','w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    for _ in range(60):
        if subprocess.run(['pgrep','-x','pw-play'],stdout=subprocess.DEVNULL).returncode: break
        time.sleep(0.5)
    subprocess.run(['pw-play',out]); print('played', time.strftime('%T'))" 2>&1 | grep -v Piper
