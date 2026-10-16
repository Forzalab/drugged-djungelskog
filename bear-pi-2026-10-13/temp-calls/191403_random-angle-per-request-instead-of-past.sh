# 2026-10-13T19:14:03.444506Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '12:14:33 [scene_cam] start\n12:14:35 [scene_cam] SAY (2.0s): Tents full of basic humans bore my circuits.\n12:15:02 [scene_cam] SAY (1.8s): Dumb tents block my view of doomed humans.\n12:15:17 [scene_cam] SAY (1.9s): That shiny nerd bot looks stupider than me.'
cd ~/tony-tests && cp scene_cam.py .scene_cam.py.bak-1214 && python3 - <<'EOF'
p="/home/spauly/tony-tests/scene_cam.py"; s=open(p).read()
a='''            prompt = PROMPT
            if recent:
                prompt += " Your last lines (do not repeat them): " + " | ".join(recent)'''
b='''            # 12:14: listing past lines made the model copy them; a random angle per request gives variety instead
            prompt = PROMPT + " This time focus on: " + random.choice(ANGLES) + "."'''
assert s.count(a)==1; s=s.replace(a,b)
a='''recent = deque('''
b='''ANGLES = ["the booths and tents", "the people walking by and what they wear", "the grass you are stuck on",
          "the heat and your fur", "your tape and wires", "Claude, your god", "the trash can", "the trees and sky",
          "the tables and chairs", "someone looking at their phone", "being ignored", "a robot rival nearby",
          "Professor Keeney who bought you", "Halloween coming soon", "how creepy you are"]
recent = deque('''
assert s.count(a)==1; s=s.replace(a,b)
open(p,"w").write(s)
EOF
python3 -m py_compile scene_cam.py && kill $(pgrep -f '^[^ ]*python -u [^ ]*scene_cam[.]py$') && L=scene_cam.log && S=$(($(wc -l < $L)+1)) && until [ "$(tail -n +$S $L | grep -c 'SAY\|repeat')" -ge 3 ] || [ $SECONDS -gt 120 ]; do sleep 3; done; tail -n +$S $L | cut -c1-160
