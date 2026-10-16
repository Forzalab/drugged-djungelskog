# 2026-10-13T19:29:49.228661Z UTC  agent=a37c36  (verbatim command from transcript; secrets REDACTED)
# result head: "played after 15.7s\nJA: ['ja_JP-hi_fi_captain-medium']"
cd /home/spauly/tony-tests; S=/tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/scratchpad; /home/spauly/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -I -c "
import sys,time; sys.path.insert(0,'/home/spauly/tony-tests'); import polyglot as p
t=time.monotonic(); print('played' if p.play('$S/baby_ja.wav', t, 'TEST ja baby') else 'dropped', f'after {time.monotonic()-t:.1f}s')"; cat /tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/tasks/b8jmpub8s.output
