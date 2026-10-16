# 2026-10-13T19:29:25.436715Z UTC  agent=a37c36  (verbatim command from transcript; secrets REDACTED)
# result head: 'dijkstra en 12.3s render 8.2s\nbaby en 3.6s render 1.1s\nbaby ru 2.6s render 7.2s\nbaby ja 3.3s render 1.0s\n-rw-rw-r--  1 spauly spauly 61894656 Oct 13 12:29 ar_JO-kareem-medium.onnx.part\n-rw-rw-r--  1 spauly spauly 13221888 Oct 13 12:29 de_DE-eva_k-x_low.onnx.part\n-rw-rw-r--  1 spauly spauly  6631424 '
cd /home/spauly/tony-tests; S=/tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/scratchpad; /home/spauly/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -I - <<EOF
import sys; sys.path.insert(0,'/home/spauly/tony-tests'); import polyglot as p, time
S='$S'
for kind,lang,t in [("dijkstra","en",p.DIJKSTRA[3]),("baby","en",p.LINES["en"][0]),("baby","ru",p.LINES["ru"][0]),("baby","ja",p.LINES["ja"][1][0])]:
    t0=time.time(); o=p.render(kind,lang,t,f"{S}/{kind}_{lang}.wav"); print(kind,lang,f"{p.dur(o):.1f}s render {time.time()-t0:.1f}s")
EOF
ls -la voices | grep part
