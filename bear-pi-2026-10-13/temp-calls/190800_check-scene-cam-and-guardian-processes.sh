# 2026-10-13T19:08:00.483591Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '12:08:01\n   5228       02:29 /bin/bash /home/spauly/tony-tests/guardian.sh\n   5455       00:00 /bin/bash -c source /home/spauly/.claude/shell-snapshots/snapshot-bash-179191655\n   5458       00:00 /bin/bash -c source /home/spauly/.claude/shell-snapshots/snapshot-bash-179191655\n12:07:18 [scene_cam] er'
date +%T; ps -eo pid,etime,args | grep -E "[s]cene_cam|[g]uardian" | cut -c1-100; tail -2 ~/tony-tests/scene_cam.log | cut -c1-120
