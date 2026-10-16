# 2026-10-13T19:03:26.085424Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'syntax-ok\n    # Guardian: every 30 s make sure bear_loop.sh runs (it restarts frankie.py itself). Honors a NO_BEAR made after boot.\n    (setsid nohup bash -c "while true; do\n        if [ ! -e \'$T/NO_BEAR\' ] && ! pgrep -f \'^/bin/bash .*bear_loop[.]sh$\' >/dev/null; then\n            echo \\"\\$(date \'+%F'
cd ~/tony-tests && cp boot.sh .boot.sh.bak-1206 && python3 - <<'EOF'
p="/home/spauly/tony-tests/boot.sh"; s=open(p).read()
a='''            setsid nohup '$T/bear_loop.sh' >/dev/null 2>&1 &
        fi
'''
b='''            setsid nohup '$T/bear_loop.sh' >/dev/null 2>&1 &
        fi
        if [ ! -e '$T/NO_SCENE' ] && ! pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py\\$' >/dev/null; then
            echo \\"\\$(date '+%F %T') guardian: starting scene_cam\\" >> '$T/boot.log'
            setsid nohup '$PY' -u '$T/scene_cam.py' >/dev/null 2>&1 &
        fi
'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
bash -n boot.sh && echo syntax-ok && sed -n '/Guardian:/,/Frankie guardian started/p' boot.sh && pgrep -af '^[^ ]*python -u [^ ]*scene_cam[.]py$' | cut -c1-80
