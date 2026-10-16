# 2026-10-13T20:07:03.504872Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'restarting detectors via guardian'
cd ~/tony-tests && cat > news_manual.txt <<'EOF'
# Hand-picked light news for the bear (crawled with TinyFish, 2026-10-13 13:08). One headline per line; edit freely.
A SpaceX launch this morning made a glowing jellyfish-shaped cloud over Tampa Bay and New Jersey
Scientists found a bacteria immune system that works completely backward
A woman says weird things keep happening after visiting Annabelle the haunted doll in Salem, and it went viral on TikTok
Apple announced a 149 dollar HomePod mini 2 with Siri AI and something called Sound Glow
Target dropped a 20 dollar KPop Demon Hunters tech collection with speakers and headphones
Youth football coaches in Arkansas got banned for fighting in the post-game handshake line
A tech school in West Virginia is holding a Tech or Treat Halloween event
Foldable iPhone sales are reportedly going to be riddled with problems
Xbox is officially embracing AI-powered game ports
Pokemon and Beats are releasing a Pokemon Bluetooth speaker
Ohio State crushed Maryland 45 to 16 this weekend
The internet is full of two-person Halloween costume lists, over a hundred ideas
EOF
python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''    global _news, _news_at
    if time.time() - _news_at > 1800 or not _news:'''
b='''    global _news, _news_at
    manual = HERE / "news_manual.txt"  # 13:08: hand-crawled headlines win (Tony: feed in manually)
    if manual.is_file():
        lines = [l.strip() for l in manual.read_text().splitlines() if l.strip() and not l.startswith("#")]
        if lines:
            return random.choice(lines)
    if time.time() - _news_at > 1800 or not _news:'''
assert s.count(a)==1; open(p,"w").write(s.replace(a,b))
EOF
python3 -m py_compile scene_cam.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py') && echo "restarting detectors via guardian"
