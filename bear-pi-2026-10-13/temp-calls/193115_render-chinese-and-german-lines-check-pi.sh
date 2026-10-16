# 2026-10-13T19:31:15.553930Z UTC  agent=a37c36  (verbatim command from transcript; secrets REDACTED)
# result head: 'Missing phoneme from id map: ̧\nMissing phoneme from id map: ̧\nzh 2.8s render 5.4s 我是一只机器熊，我也怕鬼！\nzh 3.5s render 0.7s 万圣节快乐！糖果在哪里？\nzh 3.4s render 0.6s 我不是真的熊，我是饿了的机器人。\nzh 2.6s render 0.4s 小心！熊熊在看着你。\nzh 2.9s render 0.4s 我的电池快没电了，给我巧克力！\nzh 2.7s render 0.4s 不给糖就捣蛋，熊熊说的！\nde 3.6s render 4.1s Ich bin ein Ro'
cd /home/spauly/tony-tests; S=/tmp/claude-1000/-home-spauly/74003cd9-c50a-51a5-9802-e3e4aeab6b8f/scratchpad; /home/spauly/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python -I -c "
import sys,time,random; sys.path.insert(0,'/home/spauly/tony-tests'); import polyglot as p
for l in ['zh','de']:
  for t in p.LINES[l]:
    t0=time.time(); o=p.render('baby',l,t,f'$S/baby_{l}.wav'); print(l,f'{p.dur(o):.1f}s render {time.time()-t0:.1f}s',t)
print({l:(p.model(l).stem if p.model(l) else None) for l in p.V})
for i in range(5): print(p.pick()[:3])" 2>&1 | tail -20
