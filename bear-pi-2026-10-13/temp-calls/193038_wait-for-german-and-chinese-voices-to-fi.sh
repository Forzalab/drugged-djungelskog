# 2026-10-13T19:30:38.588040Z UTC  agent=a37c36  (verbatim command from transcript; secrets REDACTED)
# result head: '-rw-rw-r-- 1 spauly spauly 20628813 Oct 13 12:30 de_DE-eva_k-x_low.onnx\n-rw-rw-r-- 1 spauly spauly     4158 Oct 13 12:28 de_DE-eva_k-x_low.onnx.json\n-rw-rw-r-- 1 spauly spauly 20628813 Oct 13 12:31 zh_CN-huayan-x_low.onnx\n-rw-rw-r-- 1 spauly spauly     4164 Oct 13 12:28 zh_CN-huayan-x_low.onnx.json'
cd /home/spauly/tony-tests/voices; until [ -f de_DE-eva_k-x_low.onnx ] && [ -f zh_CN-huayan-x_low.onnx ]; do sleep 3; done; ls -la de_DE* zh_CN*
