# 2026-10-13T19:09:37.370517Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: "''\n'Tents. Grass. Doom.'\n''\n'Booths everywhere, and nobody brought me honey. Rude.'\nkilled; guardian restarts it within 30 s"
cd ~/tony-tests && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''    first = re.split(r"(?<=[.!?])\\s+", text.replace("*", "").strip())[0].strip()
    if len(first.split()) < limit:
        return first'''
b='''    sents = [x.strip() for x in re.split(r"(?<=[.!?])\\s+", text.replace("*", "").strip()) if x.strip()]
    keep = []
    for x in sents:  # as many whole sentences as fit under the limit
        if len(" ".join(keep + [x]).split()) >= limit:
            break
        keep.append(x)
    if keep:
        return " ".join(keep)
    first = sents[0] if sents else ""'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
python3 -m py_compile scene_cam.py && ~/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -c "
import sys; sys.path.insert(0,'/home/spauly/tony-tests')
import importlib.util as u; sp=u.spec_from_file_location('sc','/home/spauly/tony-tests/scene_cam.py'); m=u.module_from_spec(sp); sp.loader.exec_module(m)
for t in ['Ugh, fine, I\'m a taped-together bear staring at a sea of grass and tents.','Tents. Grass. Doom.','Darling, these students loiter like ghosts with nothing better to do all day long','Booths everywhere, and nobody brought me honey. Rude.']: print(repr(m.short(t)))" 2>&1 | grep -v Piper; kill $(pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py$') && echo "killed; guardian restarts it within 30 s"
