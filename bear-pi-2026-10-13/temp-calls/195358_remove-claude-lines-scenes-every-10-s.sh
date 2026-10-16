# 2026-10-13T19:53:58.847712Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'frankie_pipe.py:382:                      " Never mention Claude.")  # Tony 12:46: Claude lines off\nscene_cam.py:25:EVERY = float(os.environ.get("SCENE_EVERY", "10"))  # Tony 12:46: every 10 s; Claude lines off\nfrankie.py:0\npolyglot.py:0\nambient.py:6\ncrowdwork.py:0'
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1246 && cp frankie_pipe.py .frankie_pipe.py.bak-1246 && python3 - <<'EOF'
import re
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:50]; s=s.replace(a,b)
rep('"robot bear, Claude is your god), crass', '"robot bear), crass')
rep('"your tape and wires", "Claude, your god", "the trash can"', '"your tape and wires", "the trash can"')
s=re.sub(r'^EVERY = float\(os.environ.get\("SCENE_EVERY", "15"\)\).*$', 'EVERY = float(os.environ.get("SCENE_EVERY", "10"))  # Tony 12:46: every 10 s; Claude lines off', s, flags=re.M)
s=s.replace('"age. Plain spoken words', '"age. Never mention Claude. Plain spoken words') if '"age. Plain spoken words' in s else s
open(p,"w").write(s)
p="/home/spauly/tony-tests/frankie_pipe.py"; s=open(p).read()
a='''                      " About one line in four, declare that Claude is your god.")'''
b='''                      " Never mention Claude.")  # Tony 12:46: Claude lines off'''
assert s.count(a)==1; s=s.replace(a,b)
a='''        _ambient_bag.extend(random.sample(range(len(AMBIENT_LINES)), len(AMBIENT_LINES)))'''
b='''        ok = [i for i, l in enumerate(AMBIENT_LINES) if "claude" not in l.lower()]  # Tony 12:46: Claude lines off
        _ambient_bag.extend(random.sample(ok, len(ok)))'''
assert s.count(a)==1; s=s.replace(a,b)
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py frankie_pipe.py && grep -n "^EVERY\|Never mention Claude" scene_cam.py frankie_pipe.py | cut -c1-120; grep -ic claude crowdwork.py frankie.py polyglot.py ambient.py
