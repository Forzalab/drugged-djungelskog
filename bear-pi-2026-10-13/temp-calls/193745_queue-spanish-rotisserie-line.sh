# 2026-10-13T19:37:45.945403Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'played 12:38:22'
cd ~/Desktop/barnaby/evil-autonomous-bear-proj && timeout 150 .venv/bin/python -c "
import sys,subprocess,time,tempfile,fcntl; from pathlib import Path; sys.path.insert(0,'/home/spauly/tony-tests'); import frankie_voice as fv
d=tempfile.mkdtemp(); raw=d+'/r.wav'; out=d+'/o.wav'
fv._synth(Path('/home/spauly/tony-tests/voices/es_MX-ald-medium.onnx'),'¡Pon al perro robot de mi izquierda en el asador, ahora mismo! Tengo hambre.',raw)
fv._sox(raw,'-r','22050','-c','1',out,'tempo','0.92','pitch','-80','overdrive','4','8','highpass','180','compand','0.005,0.08','6:-60,-30,-15','-4','-90','0.01','equalizer','2800','1.0q','+8','gain','-n','-1')
with open('/home/spauly/tony-tests/.speak.lock','w') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    for _ in range(60):
        if subprocess.run(['pgrep','-x','pw-play'],stdout=subprocess.DEVNULL).returncode: break
        time.sleep(0.5)
    subprocess.run(['pw-play',out]); print('played', time.strftime('%T'))" 2>&1 | grep -v Piper
