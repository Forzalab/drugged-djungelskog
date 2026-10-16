# 2026-10-13T19:54:19.639485Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '12:54:43 [scene_or] start (or, every 10 s, ≤20 words)\n12:54:46 [scene_or] SAY (3.0s): These nerds hold useless plastic junk near white tents, parading past my taped-up paws like total morons.\n12:54:43 [scene_gemini] start (gemini, every 10 s, ≤20 words)\n12:54:49 [scene_gemini] SAY (5.7s): Bozhe moi,'
cd ~/tony-tests && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''    " never about bodies, race, gender, age or disability."
)'''
b='''    " never about bodies, race, gender, age or disability. Never mention Claude."
)'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
python3 -m py_compile scene_cam.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*(scene_cam|frankie)') && L1=$(wc -l < scene_cam_or.log) && L2=$(wc -l < scene_cam_gemini.log) && until [ "$(tail -n +$((L1+1)) scene_cam_or.log | grep -c SAY)" -ge 1 ] && [ "$(tail -n +$((L2+1)) scene_cam_gemini.log | grep -c SAY)" -ge 1 ] || [ $SECONDS -gt 90 ]; do sleep 3; done; tail -n +$((L1+1)) scene_cam_or.log | cut -c1-150; tail -n +$((L2+1)) scene_cam_gemini.log | cut -c1-150; pgrep -af '^[^ ]*python -u [^ ]*(scene_cam|frankie)' | sed 's|.*tony-tests/||'
