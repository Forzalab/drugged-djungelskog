# 2026-10-13T19:30:17.983375Z UTC  agent=a37c36  (verbatim command from transcript; secrets REDACTED)
# result head: 'ar 4.2s render 7.7s\nar 3.9s render 2.4s'
cd /home/spauly/tony-tests; S=/tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/scratchpad; /home/spauly/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -I -c "
import sys,time; sys.path.insert(0,'/home/spauly/tony-tests'); import polyglot as p
for t in p.LINES['ar'][:2]:
    t0=time.time(); o=p.render('baby','ar',t,'$S/baby_ar.wav'); print('ar',f'{p.dur(o):.1f}s render {time.time()-t0:.1f}s')" 2>&1 | tail -3
