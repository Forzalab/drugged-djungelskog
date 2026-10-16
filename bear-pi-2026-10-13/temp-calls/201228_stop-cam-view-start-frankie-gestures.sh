# 2026-10-13T20:12:28.210939Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'scene_cam.py or\nscene_cam.py gemini\nscene_cam.py or2\n14751 /bin/bash ./bear_loop.sh\nfrankie.py --source 0'
cd ~/tony-tests && rm -f NO_BEAR && kill $(pgrep -f '^[^ ]*python -u [^ ]*cam_view[.]py$') && setsid nohup ./bear_loop.sh >/dev/null 2>&1 < /dev/null & sleep 25; pgrep -af '^/bin/bash .*bear_loop[.]sh$|^[^ ]*python -u [^ ]*(scene_cam|frankie|cam_view)' | sed 's|.*tony-tests/||'; grep -v qt.qpa ~/tony-tests/bear_loop.log | tail -3 | cut -c1-120
