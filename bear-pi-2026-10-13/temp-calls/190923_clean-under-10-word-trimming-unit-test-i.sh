# 2026-10-13T19:09:23.398741Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: "''\n'Tents.'\n''\n'Booths everywhere, and nobody brought me honey.'"
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1209 && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''                first = text.replace("*", "").strip().split(". ")[0]  # Tony 12:06: under 10 words
                text = " ".join(first.split()[:9]).rstrip(",;:") + ("" if first.rstrip().endswith((".", "!", "?")) else ".")'''
b='''                text = short(text)  # Tony 12:06: under 10 words, never cut mid-phrase'''
assert s.count(a)==1; s=s.replace(a,b)
a='''def log(msg):'''
b='''def short(text, limit=10):
    """First sentence if < limit words; else its first clause; else '' (skip rather than cut mid-phrase)."""
    import re
    first = re.split(r"(?<=[.!?])\\s+", text.replace("*", "").strip())[0].strip()
    if len(first.split()) < limit:
        return first
    for clause in re.split(r"(?<=[,;:])\\s+", first):
        clause = clause.strip().rstrip(",;:")
        if 3 <= len(clause.split()) < limit:
            return clause + "."
    return ""


def log(msg):'''
assert s.count(a)==1; s=s.replace(a,b)
a='''                recent.append(text)
                log(f"SAY'''
b='''                if not text:
                    log("skipped: reply too long to cut cleanly")
                    raise StopIteration
                recent.append(text)
                log(f"SAY'''
assert s.count(a)==1; s=s.replace(a,b)
s=s.replace('''        except Exception as e:
            log(f"error: {e!r}")''','''        except StopIteration:
            pass
        except Exception as e:
            log(f"error: {e!r}")''')
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py && ~/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -c "
import sys; sys.path.insert(0,'/home/spauly/tony-tests'); sys.argv=['x']
import importlib.util as u; sp=u.spec_from_file_location('sc','/home/spauly/tony-tests/scene_cam.py'); m=u.module_from_spec(sp); sp.loader.exec_module(m)
for t in ['Ugh, fine, I\'m a taped-together bear staring at a sea of grass and tents.','Tents. Grass. Doom.','Darling, these students loiter like ghosts with nothing better to do all day long','Booths everywhere, and nobody brought me honey.']: print(repr(m.short(t)))" 2>&1 | grep -v Piper
