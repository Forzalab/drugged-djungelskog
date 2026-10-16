# 2026-10-13T19:39:28.815116Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '2026 /bin/bash ./bear_loop.sh\n7065 .venv/bin/python -u /home/spauly/tony-tests/frankie.py --source 0'
until [ $SECONDS -gt 12 ]; do sleep 3; done; pgrep -af '^/bin/bash .*(dance_loop|bear_loop)[.]sh$|^[^ ]*python -u [^ ]*(scene_cam|frankie|polyglot)' | cut -c1-90
