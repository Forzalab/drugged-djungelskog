# 2026-10-13T20:04:51.587662Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '0 light headlines'
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1303 && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:50]; s=s.replace(a,b)
rep('''def log(msg):''','''# Tony 13:02: random live news + brainrot, stand-up crowd work. Light Google News sections only, grim words filtered.
NEWS_FEEDS = [f"https://news.google.com/rss/headlines/section/topic/{t}?hl=en-US&gl=US&ceid=US:en"
              for t in ("TECHNOLOGY", "SCIENCE", "ENTERTAINMENT", "SPORTS")]
GRIM = re.compile(r"dies|died|dead|death|kill|shoot|shot|murder|war|attack|crash|assault|abuse|suicide|victim|"
                  r"injur|bomb|terror|missile|hostage|fatal|funeral|cancer|trump|biden|harris|election|senat|"
                  r"congress|israel|gaza|ukraine|russia|immigra|ice |police|arrest|charged|lawsuit|sued", re.I)
_news, _news_at = [], 0.0
BRAINROT = ("skibidi", "rizz", "aura points", "sigma", "Ohio", "fanum tax", "no cap", "delulu", "mewing", "six seven",
            "it's giving", "main character energy", "NPC", "brain rot", "bussin", "lowkey", "touch grass")


def news():
    """A random light headline (refreshed every 30 min); '' if offline."""
    global _news, _news_at
    if time.time() - _news_at > 1800 or not _news:
        got = []
        for url in NEWS_FEEDS:
            try:
                xml = subprocess.run(["curl", "-s", "-m", "8", url], capture_output=True, text=True, timeout=12).stdout
                for t in re.findall(r"<title>([^<]*)</title>", xml)[1:]:
                    t = re.sub(r"\\s+-\\s+[^-]+$", "", t.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"'))
                    if t and not GRIM.search(t) and "Google News" not in t:
                        got.append(t)
            except Exception:
                pass
        if got:
            _news = got
        _news_at = time.time()
    return random.choice(_news) if _news else ""


def log(msg):''')
rep('''            prompt = PROMPT + " This time focus on: " + random.choice(ANGLES) + "."''','''            prompt = PROMPT + " This time focus on: " + random.choice(ANGLES) + "."
            headline = news() if random.random() < 0.5 else ""
            if headline:
                prompt += (f" Also riff on this real headline from today like a stand-up comic: \\"{headline}\\"."
                           " Keep it light.")
            prompt += (" Entertain the people in front of you: stand-up crowd work, and use 1-2 Gen-Z brainrot words"
                       f" naturally (like {', '.join(random.sample(BRAINROT, 3))}).")''')
# old static news block off: live feed replaces it
s=s.replace(''' About one line in three, work in TODAY'S NEWS''',''' (old static news, unused) TODAY'S NEWS''')
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py && ~/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -c "
import sys; sys.argv=['x','or']; sys.path.insert(0,'/home/spauly/tony-tests')
import importlib.util as u; sp=u.spec_from_file_location('sc','/home/spauly/tony-tests/scene_cam.py'); m=u.module_from_spec(sp); sp.loader.exec_module(m)
m.news(); print(len(m._news), 'light headlines'); [print(' -', h) for h in m._news[:6]]" 2>&1 | grep -v Piper
