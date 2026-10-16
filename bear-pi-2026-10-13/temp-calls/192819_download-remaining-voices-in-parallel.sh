# 2026-10-13T19:28:19.381177Z UTC  agent=a37c36  (verbatim command from transcript; secrets REDACTED)
# result head: 'Command running in background with ID: b8jmpub8s. Output is being written to: /tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/tasks/b8jmpub8s.output. You will be notified when it completes. To check interim output, use Read on that file path.\nSession cwd remains /home/spauly/tony-'
cd /home/spauly/tony-tests/voices; B=https://huggingface.co/rhasspy/piper-voices/resolve/main
dl(){ f=$(basename $1); curl -sfL -C - -o $f.$2.part $B/$1.$2 && mv $f.$2.part $f.$2 || echo FAIL $f.$2; }
mv ar_JO-kareem-medium.onnx ar_JO-kareem-medium.onnx.part
for p in ar/ar_JO/kareem/medium/ar_JO-kareem-medium zh/zh_CN/huayan/x_low/zh_CN-huayan-x_low de/de_DE/eva_k/x_low/de_DE-eva_k-x_low; do dl $p onnx & dl $p onnx.json & done
( curl -sfL -m 60 $B/voices.json | python3 -c "import json,sys;d=json.load(sys.stdin);print('JA:',[k for k in d if k.startswith('ja')])" ) &
wait; ls -la; dpkg -l | grep -i espeak | head
