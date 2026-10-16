# 2026-10-13T19:09:45.844961Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '12:10:03 [scene_cam] start\n12:10:04 [scene_cam] nothing to say (NONE)\n12:10:19 [scene_cam] nothing to say (NONE)\n12:10:34 [scene_cam] nothing to say (NONE)\n12:10:49 [scene_cam] nothing to say (NONE)\n12:11:04 [scene_cam] nothing to say (NONE)\n12:11:19 [scene_cam] nothing to say (NONE)\n12:11:34 [scene'
L=~/tony-tests/scene_cam.log; S=$(($(wc -l < $L)+1)); until tail -n +$S $L | grep -q "SAY" || [ $SECONDS -gt 110 ]; do sleep 3; done; tail -n +$S $L | cut -c1-160
