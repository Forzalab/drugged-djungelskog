# 2026-10-13T20:05:05.160763Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '0\n213 light headlines\n - Apple releases HomeView smart home hub with screen as showcase for Siri AI\n - Hands-on with the Apple Home Collection\n - Pokémon × Beats Pill Wireless Bluetooth® Speaker Coming Soon\n - NVIDIA Unveils "Preset C "DLSS Frame Generation with up to 35% Faster Generation\n - Apple '
cd ~/tony-tests && sed -i 's|\["curl", "-s", "-m", "8", url\]|["curl", "-sL", "-m", "8", url]|' scene_cam.py && python3 - <<'EOF'
import re
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
i=s.index('    # Tony 12:57: report today'); j=s.index('violence."', i)+len('violence."')
s=s[:i]+'    # 13:03: static news removed; live headlines are added per request (news())'+s[j:]
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py && grep -c "Netflix" scene_cam.py; ~/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -c "
import sys; sys.argv=['x','or']; sys.path.insert(0,'/home/spauly/tony-tests')
import importlib.util as u; sp=u.spec_from_file_location('sc','/home/spauly/tony-tests/scene_cam.py'); m=u.module_from_spec(sp); sp.loader.exec_module(m)
m.news(); print(len(m._news), 'light headlines'); [print(' -', h) for h in m._news[:8]]" 2>&1 | grep -v Piper
