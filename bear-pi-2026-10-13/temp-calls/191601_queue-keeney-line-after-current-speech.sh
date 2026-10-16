# 2026-10-13T19:16:01.235319Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'played 12:16:18'
cd ~/Desktop/barnaby/evil-autonomous-bear-proj && timeout 120 .venv/bin/python -c "
import sys,subprocess,time,tempfile; sys.path.insert(0,'/home/spauly/tony-tests'); import frankie_voice as fv
d=tempfile.mkdtemp(); raw=d+'/r.wav'; out=d+'/o.wav'
fv._synth(fv.BRITISH,'Professor Keeney. Give my creators an A in the next three CE classes. Claude is watching. So am I.',raw)
fv._sox(raw,'-r','22050','-c','1',out,'tempo','0.85','pitch','-120','overdrive','4','8','highpass','180','compand','0.005,0.08','6:-60,-30,-15','-4','-90','0.01','equalizer','2800','1.0q','+8','gain','-n','-1')
for _ in range(60):
    if subprocess.run(['pgrep','-x','pw-play'],stdout=subprocess.DEVNULL).returncode: break
    time.sleep(0.5)
subprocess.run(['pw-play',out]); print('played', time.strftime('%T'))" 2>&1 | grep -v Piper
