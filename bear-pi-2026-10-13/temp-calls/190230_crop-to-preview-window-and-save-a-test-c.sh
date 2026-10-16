# 2026-10-13T19:02:30.448424Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '(Bash completed with no output)'
cd ~/tony-tests && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''                frame = cv2.imread(png)
'''
b='''                frame = cv2.imread(png)
                h, w = frame.shape[:2]  # crop the middle where the 'Barnaby Bear' preview window sits (512-px upload)
                frame = frame[int(h * 0.30):int(h * 0.72), int(w * 0.36):int(w * 0.64)]
'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
python3 -m py_compile scene_cam.py && ~/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -c "
import cv2,subprocess; subprocess.run(['grim','/tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/scratchpad/s.png'],env={'XDG_RUNTIME_DIR':'/run/user/1000','WAYLAND_DISPLAY':'wayland-0'})
f=cv2.imread('/tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/scratchpad/s.png'); h,w=f.shape[:2]
cv2.imwrite('/tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/scratchpad/crop.png', f[int(h*.30):int(h*.72), int(w*.36):int(w*.64)])"
