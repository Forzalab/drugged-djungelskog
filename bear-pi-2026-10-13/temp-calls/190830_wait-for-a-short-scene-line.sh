# 2026-10-13T19:08:30.960807Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: "12:08:34 [scene_cam] nothing to say (NONE)\n12:08:49 [scene_cam] nothing to say (NONE)\n12:09:05 [scene_cam] SAY (2.8s): Ugh, fine, I'm a taped-together bear staring at a"
L=~/tony-tests/scene_cam.log; S=$(($(wc -l < $L)+1)); until tail -n +$S $L | grep -q "SAY" || [ $SECONDS -gt 60 ]; do sleep 3; done; tail -n +$S $L | cut -c1-160
