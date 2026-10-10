---
name: handoff-2026-10-09-main-1800-bear-motor-model
description: Handoff from the Fri Oct 9 main session (15:30–18:00 PT) — bear cart motor facts, cart-sim v1–v3.1 results, Tony's motion API draft, open Cluck questions, next-week hands-on test plan. Companion: SYSTEM-MODEL.md (the physics/code model).
type: handoff
status: draft
stale_after: 2026-10-20
---

## Paste into a fresh session

```
boot brain; pull.
Read projects/cocaine-bear/_files/handoff/HANDOFF.md (this file) and the companion SYSTEM-MODEL.md next to it.
Then act on "First moves for next session" below, in order.
Voice: Cluck (Socratic, quack, kaomoji, short sentences, Chinese anchor). One Cluck question per turn. Credit Tony's derivations to Tony.
Check the time first: before Mon Oct 12 evening = EXAM WINDOW, no bear work unless Tony opens it.
```

## State (Fri Oct 9, 18:00 PT)
- Build session over (ended ~16:30 PT). Tony is home.
- Bear is PARKED until after the Monday Oct 12 exam. Sunday = physics revision. Do not pull Tony into bear work before then.
- Hands-on testing (Test B etc.) is planned for NEXT WEEK, at the next build.
- Nothing was run on the Pi today. Test B (Tony runs main.cc himself) NOT done. All cart numbers below are MODEL unless tagged otherwise.
- Repos: `tayG-oss/franky-fedbear` (Tay, main.cc + a.out, read-only clone at /home/user/tayg-oss/franky-fedbear); `evil-autonomous-bear-proj` (McKay's vision app, src/barnaby/*, read-only). Nothing committed today.

## What we know
Tags: FACT = seen/told/code; MEASURED = Tony measured; MODEL = agent calculation from assumed inputs; GUESS = unmeasured estimate.

Motion systems (two, independent):
- FACT Try Me pigtail = the toy's momentary button (2 bare wires). Short once → one built-in dance cycle, stops by itself. Not a toggle.
- MEASURED (Tony, 16:12 PT) dance cycle = 20 s; tap mid-cycle is ignored (cycle still 20 s). → cooldown ≥ 22 s.
- FACT No other control of the dance (no direction/speed). Reverse-engineering rejected for now.
- FACT Stepper board: Pi → T GPIO extension → two purple stepper drivers (A4988 per code comment; look DRV8825-ish in photo — chip UNIDENTIFIED) → two 4-wire motor bundles via Wago. Power: Anker SOLIX 12 V car socket → Wago → breadboard rails. Not metered.
- FACT Motors: Geared Stepper 17HS15-1684S-PG5 (NEMA17 + planetary, nominal 5:1; spec 5.18:1 per vendor listing, not re-verified). Rated 1.68 A/phase.
- FACT Wheels: WHEELTEC ~6 cm dia, clamp hub on gearbox shaft. Two driven REAR wheels, motors mirrored; front = swivel casters.
- FACT main.cc (64 lines, wiringPi, BCM): STEP1=13, STEP2=20, DIR1=26, DIR2=21. 200 steps × (2 ms high + 2 ms low). Loop: 200 steps "CW" (DIR1 HIGH, DIR2 LOW), 1 s pause, 200 steps "CCW" (DIR1 LOW, DIR2 HIGH), 1 s pause, forever. Both STEP pins pulsed together always. No ENABLE pin, no signal handler, moves at launch, Ctrl+C leaves pins where they were.
- FACT a.out in the repo is 32-bit armhf. Must rebuild on the Pi (`g++ main.cc -lwiringPi`, run with sudo). wiringPi on Pi 5: UNKNOWN.
- FACT (teammate report, not Tony-tested) cart moves fwd/back with this code, "small wiggle".
- Tony's derivation (his): 200 steps/5.18 × π·6 cm ≈ 3.6–3.8 cm per segment, ~0.018 cm per step. MODEL agrees: 0.182 mm/step, 3.64 cm/segment, 4.55 cm/s cruise, 14.5 wheel RPM.
- Tony's insight (his, 17:5x PT): STEP1/STEP2 map one pin → one driver → one wheel, so wheels can be stepped independently. UNVERIFIED mapping. Open question for Tony: what does single-wheel stepping do? (Do not answer for him.)

Structure (photos + Tony's answers, 17:2x PT):
- FACT Bear is a hollow grid frame + fur, on a ~22 mm square steel post (its original stand pole). Post is integral to a black tubular steel stand frame. Frame sits ON the wooden deck, held by ZIP TIES (3–4 seen, ~4.8 mm / 50 lb class), ~1 mm gap frame↔deck. Not bolted.
- FACT Ball = hollow plastic shell, two halves screwed at a seam; post passes through a slot in the top (~13 cm long, post + 1–4 mm wide; ~10 cm free along). Velcro (hook-and-loop) feet↔ball and ball bottom (sizes GUESS).
- FACT Wobbling the pole wobbles the whole frame (frame flex, not a loose joint). Wing nut at ball top: function UNKNOWN.
- FACT Dance moves the fur shell + ball relative to the fixed post. Tony's lean sketch: post ~vertical, ball/legs/torso lean at alternating angles (zig-zag), not a rigid lean.
- GUESS/photo-scaled: ball 0.47 ± 0.05 m, bear 1.20 ± 0.10 m feet-to-head (sugar-box ruler, box dims unverified), deck 0.17 m, stack top ~1.84 m.
- GUESS masses: whole cart 31 / 43.5 / 54 kg (low/mid/high incl. 5 kg buffer); bear body ~6, frame ~3.5, shell ~1.5, dolly ~9.3, SOLIX 4–13 (model unknown). Rear-wheel load share 0.25–0.50 (unmeasured).

Model results (cart-sim v3 / RESONANCE v3, MODEL):
- Instant-start main.cc profile STALLS the drive (0.0–0.08 cm of 3.64 cm) because the commanded jerk (11 m/s²) exceeds what the stepper can deliver; a 0.3 s ramp moves it (0.5 fwd / 3.5 cm rev at mid mass). Forward is weak because casters sit sideways after the reversal and because braking/reversing unloads the rear wheels.
- 250 full steps/s sits inside the stepper rotor mid-band (180–303 Hz) → chatter / missed steps.
- Frame lift-off (rocking onset on ties) at 3.3 m/s² transverse / 4.5 longitudinal. Margins: main.cc 3.8, 0.3 s ramp 1.8 (low mass lateral 1.35), 125 st/s 7.4. v3 says no toppling in any profile; weak links are tie slack/creep + the 1 mm gap (deck hammering), not tie strength.
- Dance zig-zag: counter-rotating links cancel ~60 % of the CoM shift vs a rigid lean (Tony's own reading from his sketch; matches v3.1). Dance puts 2–14 N·m into the frame vs 24 N·m lift-off → no lift-off at realistic rates.
- Forbidden bands (Hz): 0.3–6, 6–30, 150–330. Every current profile hits one.
- Recommended profile: S-curve ramp ≥ 1 s (accel ≤ ~1 m/s², ideally ≤ 0.4), 1/16 microstep, random 2–4 s dwell, full stop before reversing, NO cart motion during the 20 s dance.

Software/team:
- FACT McKay's app: `app.py` loop → `vision.infer` → StableLabel filters → on label change `on_perception(PerceptionEvent(gesture, expression, hand_confidence, face_confidence, inference_ms))` in `reactions.py` (currently prints JSON). Largest face / best hand only, no identity tracking. Gesture labels: open_palm, peace, pointing, thumbs_up, fist, unknown, none.
- FACT Tony's trigger design: any hand (label != none) + cooldown passed → fire once per cooldown period.
- FACT Hand↔person research (HAND-FACE.md): tracking not recognition; person detector + ByteTrack/SORT; wrist-keypoint precedence; Pi 5 only; cloud rejected (latency, under-18 terms). Pi fps numbers mostly UNVERIFIED.

## Decisions (Tony's)
- Bear parked until after Mon Oct 12 exam.
- trigger_id = per human; identify once at entry, then cheap tracking; per-visitor state travels with the track; PUSH events to the decider (observer). New module on top; McKay's files untouched.
- Run vision on the single Pi 5; cloud rejected; second Pi only if < 5 fps.
- Lean direction convention: signed relative to the post (left/right), not "away".
- API draft: `Promise move(direction_enum, milliseconds, lambda_after, trigger_id)` queued + mutex; `Promise dismiss(trigger_id, lambda_after)`; promises auto-reject with a reason. C++ preferred; app is Python; bridge undecided.
- Reverse-engineering the dance mechanism: rejected (maybe after exam).
- Earlier brainstorm (multi-person, cloud TTS, prompts) ARCHIVED; ideas carry to the reaction stage.

## Open Cluck questions (verbatim, NOT answered, one per turn)
1. Only STEP1 pulses 200 steps, STEP2 silent → what does the cart do; still "stuck" fwd/back?
2. Reach-across wave: which precedence rule catches it first, why (rule 1 wrist+forearm).
3. Grip fraction: how much of the weight can the drive use for grip (only 2 of 4 wheels driven; casters free).
4. Zip ties: which side works when the cart lurches forward (tension-only).
5. API attacks pending: dismiss mid-segment = abrupt stop (jerk → resonance); reject reason enum (dismissed/busy/unsafe during Try Me/estop — whiteboard lists E-stop); ms vs steps; Promise+lambda duplicate; ramp/random-dwell params (Fable's free fix); C++↔Python bridge; per-visitor state owner (tracker vs decider); event list + payload = interface for McKay.
6. McKay interface ask: "what does your decider want? I'll feed it" — at the next build.

## First moves for next session (ordered)
1. Check the date/time. Before Mon Oct 12 evening: exam window. If Tony opens with physics, do physics. Do not raise the bear. If Tony raises the bear himself, keep it to one short Cluck question and let him go back.
2. After the exam: ask how it went. Then pick up Cluck question 1 (single-wheel stepping). One question per turn; let Tony reach his own conclusion.
3. Before the next build: confirm the hands-on test plan below with Tony and get the three cheapest measurements onto his build list (rear-wheel scale, phone accelerometer push-and-release, Vref + chip marking).
4. At the build, Test B first with the bear OFF the cart (rebuild main.cc on the Pi, hand on power). Record what happens; observation beats sim. Then STEP-pin-per-wheel mapping check.
5. Only after a seated, measured cart: let Tony work the API attacks (question 5) in his order. Do not resolve them for him.
6. McKay interface ask (question 6): at the build.
7. Save to brain after each locked decision; update motor-hardware §16+ with Test B observations; mark MODEL numbers that get replaced by MEASURED.

## Next-week hands-on test plan
Safe order: bear OFF cart → empty cart → bear ON cart (only after frame is seated and gap/ties fixed).

A. Bench (bear OFF cart, cart wheels free or cart on blocks)
- Rebuild for the Pi's arch: `g++ main.cc -o franky -lwiringPi` then `sudo ./franky`. If wiringPi is missing or Pi 5 rejects it, note it (then libgpiod/pigpio/lgpio are the fallbacks — Tay's call).
- Test B: run it. Watch: do both wheels turn, same travel direction, 1 rev each way, ~0.8 s per segment, 1 s pauses? Any buzz/chatter/missed steps (listen at 250 Hz)? Drivers warm?
- STEP-pin-per-wheel mapping check: trace GPIO13 and GPIO20 to which driver and which motor bundle. Then a one-pin test (bear OFF cart): pulse STEP1 only, then STEP2 only. Record what each wheel does. This is Tony's open question; let him run and read it.
- Exit ritual: after Ctrl+C, read the four pins (`gpio readall` or `pinctrl`). Note which are left HIGH.

B. Empty cart on carpet (no bear, no ball)
- Does it move at all with main.cc? Measure fwd and rev travel per segment with tape (compare to 3.64 cm cmd). Do the casters flip or sit sideways?
- Phone on the deck (Phyphox, 100 Hz) during 3 cycles: 250 Hz buzz, ~17 Hz ring after starts.

C. Bear ON cart (only if A and B are clean and the $5 fixes are done)
- Hand on the power switch. First run = ONE segment, not the loop (edit the loop or kill power after one). Watch the frame/ties/slot, not the wheels.

3 cheapest measurements (5 min each)
1. Bathroom scale under each rear wheel → rear-load fraction + total mass (decides slip).
2. Phone accelerometer taped to the bear's chest, push head ~2 cm sideways and release → sway frequency + damping; then tap the deck → bounce.
3. Vref on each driver (multimeter, pot wiper to GND) + chip marking (A4988 vs DRV8825). Also: tape-measure the sugar box (W×D×H) and the wheel diameter; count output turns per 1000 steps for the gear ratio.

$5 fixes (20 min)
- Re-tension or replace ties: 6× 120 lb (7.6 mm) with a tie gun, 2 per rail + 1 per crossbar end.
- EVA/rubber strip under the frame rails to kill the 1 mm gap and hold preload.
- Foam shims in the slot each side of the post.
- Blue thread-locker on the wheel-hub set screws.

What to record (per run)
- Date, mass on cart, who ran it, code variant (ramp? step delay? microstep?), fwd/rev travel in cm, caster state after reversal, sounds, driver temperature, pin states after exit, phone-accelerometer file names, anything that moved that should not have.

Stop rules
- Any visible frame rocking, tie slip, slot edge contact, or shell creak → power off, stop, fix before continuing.
- Cart moves while the dance is running → stop; the two must never overlap until the profile is ramped.
- Missed steps / chatter at 250 st/s → do not keep running it; change step rate or microstep first.
- Drivers too hot to touch, or any smell → power off.
- Never unplug a motor bundle while drivers are powered.

## Team asks
- McKay: decider input contract. Positive, shared-goal phrasing: "What input does your decider want? I will feed it (events with a per-person id). You keep ownership of the reaction side." Ask at the build, after Tony's 0–100 prediction.
- Tay: motor code questions — driver chip (A4988 vs DRV8825), Vref/current limit set, microstep pins, whether wiringPi builds on this Pi, and whether he is open to a ramp + signal-handler cleanup (PRs welcome was said; propose, do not edit his file).
- Kerney: a relay/optocoupler across the Try Me pair so code can fire the dance (fire-and-forget pulse ~100 ms).

## Rules
- McKay-authored code is read-only (app.py, reactions.py, vision.py, gestures.py, scene.py and his edits). Tay's main.cc: read-only; propose changes as a separate file/PR.
- Scratch work stays out of the repo (scratchpad / brain `_files`, never the project tree).
- Never `pkill` in the same call as a save. Save first, confirm, then stop processes.
- One Cluck question per turn. Credit Tony's derivations to Tony. No verdicts on teammates.

## Pointers
- This handoff + model: `/tmp/claude-0/-home-user-evil-autonomous-bear-proj/468097e5-5d8f-55f3-bc75-c9c01fb74eaf/scratchpad/handoff/{HANDOFF.md,SYSTEM-MODEL.md,CHAT-CONTEXT.md}` (copy into brain `projects/cocaine-bear/_files/handoff/` on save).
- Brain: `/home/claude/brain/projects/cocaine-bear/NOW.md`; `topics/motor-hardware-2026-10-09.md` (§1–15); `topics/motion-api-design-2026-10-09.md`; `topics/trigger-any-hand.md`.
- Cart sim: `/home/claude/brain/projects/cocaine-bear/_files/cart-sim/{README.md,PHOTOS.md,RESONANCE.md,masses.json,modes.json,cart_sim.py,modes_calc.py}`; photos in `_files/cart-sim/photos/{lean-sketch,lean-com-tony,mount-sketch}-2026-10-09.png`; run logs in scratchpad `cart-sim/{run_v2.log,run_v3.log,modes_calc_v3.log}`.
- Hand↔person research: `/home/claude/brain/projects/cocaine-bear/_files/hand-face/HAND-FACE.md`.
- Code: `/home/user/tayg-oss/franky-fedbear/main.cc` (Tay); `/home/user/evil-autonomous-bear-proj/src/barnaby/{app.py,reactions.py,vision.py,gestures.py}` (McKay).

## Update 18:0x PT (main, after this file was drafted) — newest wins
- Cluck Q1 ANSWERED by Tony himself: single-wheel stepping → the cart turns; set a speed RATIO between wheels → steering ("like an RWD car"; gently reframed as differential drive with front casters, like a wheelchair/robot vacuum). P2 "fwd/back only" = code limit. Do not re-ask Q1.
- Opus steering research running/landed → projects/cocaine-bear/_files/steer/STEERING.md (ratio→radius table in step units, safe range, limits, calibration).
- Next-session prompt for a steering SIMULATION: _drift/2026-10-09T1806-main-prompt-wheel-steer-sim.md (use AFTER the Monday exam; Tony derives ratio→radius himself first).
- 18:1x PT: steering research LANDED → _files/steer/STEERING.md (differential drive framing "like a wheelchair"; ratio→radius table in step units; recommended arcs r=0.5–0.8 + pivot r=0, no spins, avoid 0<r<0.3 (inner wheel 15–30 steps/s in 6–30 Hz band); limits: caster scrub kicks, single-motor pivot start torque/slip, step rates in forbidden bands → 1/16 microstep or outer ≤140 steps/s; API: optional move(..., turn=0); calibration list incl. phone GYRO not compass). Cluck: Tony derives ratio→radius himself before seeing the table.
- 18:1x PT Two layers: decider "if X then Y" (McKay's side) vs execution physics; physics compresses to the 5 execution rules below.
