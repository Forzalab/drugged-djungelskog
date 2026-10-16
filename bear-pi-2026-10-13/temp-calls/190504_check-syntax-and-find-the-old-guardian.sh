# 2026-10-13T19:05:04.859417Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: "syntax-ok\n2109 bash -c while true; do         if [ ! -e '/ho"
cd ~/tony-tests && chmod +x guardian.sh && bash -n guardian.sh && bash -n boot.sh && echo syntax-ok && pgrep -af '^bash -c while true' | cut -c1-50
