# SYSTEM-MODEL — Barnaby bear cart, internal physics/code model (as of Fri 2026-10-09 18:00 PT)

Tags: FACT (seen / told / in code), MEASURED (Tony measured), MODEL (agent calculation from stated inputs), GUESS (unmeasured estimate), UNVERIFIED, OPEN (Tony's to work out — do not resolve). Sources: brain motor-hardware §1–15, cart-sim README/PHOTOS/RESONANCE v1–v3.1, masses.json, modes.json, run_v3.log, main.cc, HAND-FACE.md, McKay's src/barnaby.

## (a) Mechanical stack and load path

```
                 head ~1 kg (jaw motor)                         z ≈ 1.84 m above floor (stack top)
                 torso + arms, fur over hollow grid frame       bear body ~6 kg GUESS, 1.20 ± 0.10 m tall (photo-scaled)
                 hip = dance mechanism (Try Me: shell sways on the post)
                 feet  --velcro strap-->  ball top              feet velcro: SEEN
      ~22 mm square steel POST (bear's original stand pole)    post: SEEN; runs down THROUGH the ball
                 | passes through SLOT in ball top: ~13 cm long, post + 1–4 mm wide, ~10 cm free along   SEEN/scaled
      hollow plastic BALL shell, 2 halves screwed at seam      0.47 ± 0.05 m dia, ~1.5 kg GUESS; cosmetic, not load-bearing
                 | ball bottom --velcro--> wooden cradle rails  sketch; patch sizes GUESS
      post welded into black tubular steel STAND FRAME         ~3.5 kg GUESS, base ~0.45 × 0.6 m GUESS
      frame sits ON deck, ~1 mm GAP, held by 3–4 ZIP TIES      FACT (Tony); ties ~4.8 mm / 50 lb (222 N) class SEEN
      ===== plywood + carpet DECK on steel dolly (GFS-1830 assumed, 30 × 18 in) =====   deck top ≈ 0.17 m
      [front: 2 swivel CASTERS]           [rear: 2 driven 6 cm WHEELTEC wheels, mirrored geared steppers]
      track ~0.40 m, wheelbase ~0.66 m (GUESS)                 also on deck: SOLIX, fog machine, Pi, drivers
      ------------------------------ carpet floor ------------------------------
```
Load path: bear weight → post → frame rails → deck (through the 1 mm gap once ties compress it) → casters + rear wheels. Ball carries no bear load (shell threaded on the post). Lateral restraint of the frame: ties in tension only + rail friction; rocking about a rail edge once lift-off accel is exceeded.

## (b) Masses and geometry

| item | low / mid / high (kg) | tag |
|---|---|---|
| dolly (GFS-1830 assumed) | 8.8 / 9.25 / 9.7 | GUESS (web) |
| wood deck + carpet | 1.5 / 3.0 / 4.5 | GUESS |
| motors + wheels + mounts | 1.4 / 1.5 / 1.8 | GUESS (2 × 0.46 kg motors) |
| ball shell | 1.0 / 1.5 / 2.5 | GUESS (hollow, SEEN) |
| bear body (hollow frame + fur) | 5.0 / 6.0 / 7.5 | GUESS (listing 20 lb incl. stand) |
| stand frame incl. post | 2.5 / 3.5 / 5.0 | GUESS |
| fog machine | 1.4 / 2.5 / 4.5 | GUESS (model unknown) |
| Anker SOLIX | 4.1 / 10.9 / 12.9 | GUESS (C300 / C800+ / C1000; F-series would add +18) |
| Pi + wiring | 0.15 / 0.3 / 0.6 | GUESS |
| buffer X | 5 / 5 / 5 | Tony's parameter |
| **whole cart** | **30.9 / 43.5 / 54.0** | MODEL sum |
| stack above deck (bear + post + shell + frame) | ~11 | MODEL |

| geometry | value | tag |
|---|---|---|
| deck height | 0.17 m (0.155–0.19) | GUESS |
| ball dia | 0.47 ± 0.05 m | photo-scaled (sugar-box ruler UNVERIFIED) |
| bear feet-to-head | 1.20 ± 0.10 m | photo-scaled |
| stack top above floor | ~1.84 m | MODEL |
| stack CoM above deck | 0.66 m (v3) | MODEL |
| whole-cart CoM above floor | ~0.37 m | MODEL |
| post section | 22 mm sq, ~1.2 mm wall, EI ≈ 1.4 kN·m², yield moment ~164 N·m | GUESS |
| frame rocking half-widths | 0.22 m transverse, 0.30 m longitudinal | GUESS |
| rear-wheel load share | 0.25 / 0.40 / 0.50 | GUESS — MEASURE |
| bear lateral CoM offset (raised arm) | 2–4 cm | INFERRED from pose |

## (c) Drivetrain kinematics (FACT from main.cc + motor label; derived = MODEL)

Chain: STEP pulse → 1.8° motor step (200/rev, full step; MS pins unconnected = full step, GUESS) → ÷5.18 planetary (nominal 5:1; 5.18 from vendor listing, UNVERIFIED) → wheel 60 mm → distance = π·d / (200 × 5.18).
- Per step at output: 0.3475°; wheel travel 0.182 mm/step (Tony: ~0.018 cm/step — his derivation).
- main.cc timing: 2000 µs high + 2000 µs low → 4 ms/step → 250 full steps/s → motor 1.25 rev/s (75 RPM) → wheel 0.241 rev/s = 14.5 RPM → cruise 4.55 cm/s.
- Per segment: 200 steps = 1 motor rev = 0.193 wheel rev = 3.64 cm (Tony: 3.6–3.8 cm). Segment lasts 0.80 s.
- Cycle: 0.8 s fwd + 1 s pause + 0.8 s rev + 1 s pause = 3.6 s → fundamental 0.278 Hz; reversal rate 0.556 Hz.
- Mirrored motors: DIR1 = !DIR2 always → both wheels same travel direction (inferred from mount + teammate report; mapping UNVERIFIED).
- Step pulse: 250 Hz square wave on STEP1 and STEP2 simultaneously (same loop iteration).

## (d) Dynamics (MODEL unless noted)

Motor-side (GUESS inputs: current limit 1.25 A, holding 0.36 N·m at motor shaft, rotor J 43 g·cm², zero-torque rate 1500 st/s, µ 0.6, crr 0.05):
- Instant start to 250 st/s needs the rotor+load to accelerate within ~2 steps → required torque ≫ available → STALL / missed steps at start (margin 0.12–0.83 across masses). Cruise torque fine (margin ~2.4). Commanded jerk 11.4 m/s²; motor can really deliver ~0.6–0.8 m/s² (torque-limited).
- Result for main.cc profile: 0.00–0.08 cm travel of 3.64 cm cmd at mid/high mass (stall); low mass 0.01 fwd / 3.4 rev. Matches teammate "small wiggle" qualitatively. OBSERVATION (Test B) beats this.
- 0.3 s trapezoid ramp: 0.46 fwd / 3.52 rev cm at mid mass. 125 st/s instant: 0.00 / 0.63.
- Load split / transfer: N_rear = m(g·f_rear + a·h/L). ΔN ≈ 15–20 N at 0.6–0.8 m/s² = ±8–12 % of the ~176 N static rear load → traction 115–118 N when accelerating rearward-loaded vs 94–97 N the other way → asymmetric slip → net creep per cycle. Rear-share sweep (ramp profile, fwd cm): 0.04 / 0.46 / 0.92 / 1.18 / 1.63 at f_rear 0.3–0.7.
- Caster swivel: trailing caster needs ~π·e/2 = 5–8 cm of travel (trail e 2.5–5 cm GUESS) to flip 180°; segments 0.1–3.5 cm → flip never completes, casters sit sideways and scrub (~40 N per caster, up to 1.8 m/s² lateral if both scrub same side; 0.48 m/s² in the ramp run). Kinematic swivel mode 0.14–0.24 Hz; shimmy not expected at 4.5 cm/s.
- Tip / lift-off thresholds per fixity case (a_tip = g·b/h):
  | case | a_tip (m/s²) | margin a main.cc / b 0.3 s ramp / c 125 st/s | lateral (b) |
  |---|---|---|---|
  | fixed (post/frame bolted to deck) | 5.38 (whole-cart transverse governs) | 6.1 / 2.8 / 11.8 | 4.2 |
  | pinned with gap (v2) | 1.23 | 1.24 / 0.57 TIPS / 2.4 | 0.85 TIPS |
  | velcro only (v2) | 1.79 | 1.71 / 0.79 TIPS / 3.3 | 1.17 |
  | **frame zip-tied + 1 mm gap (v3, current)** | **3.28 transverse (lift-off onset), 4.5 longitudinal** | **3.8 / 1.8 / 7.4** (low mass: 1.8 / 3.0 / 1.9; low-mass lateral b 1.35) | 5.3 |
  v3 reading: no toppling in any profile; the ramp profile sits at 1.8 against rocking onset → ramp ≥ 0.6–1 s keeps the frame seated. Tie force: 0 N at real jerk, 17 N/tie at whole-cart tip accel, break needs ~30 m/s². Weak links = tie slack/creep + 1 mm gap (free rocking, deck hammering each start/stop).
  Zip ties work in tension only → on a forward lurch, the ties on the side the frame lifts from take load (OPEN Cluck Q4 — let Tony say which).
- Single-pulse energy: one 4.55 cm/s velocity jump gives the stack ~0.008 J vs ~1.2 J to tip → one pulse cannot overturn it; resonance build-up and caster kicks are what matter.
- Resonant build-up at sway mode from the un-ramped 3.6 s comb (0.1 m/s² per harmonic, Q 10–17): 1.0–1.7 m/s² at bear CoM after 10–17 cycles; displacement 0.3–0.5 cm (zip-tied), 1–2 cm (pinned), 7–11 cm (velcro only). 1 s ramp cuts harmonics 5–55×; random dwell destroys coherence.

Modes (Hz, low / mid / high; ζ):
| mode | f | ζ |
|---|---|---|
| bear on frame sway, zip-tied (PRIMARY) | 1.8 / 2.8 / 3.6 (zero stiffness inside gap) | 0.04 |
| bear on post sway, fixed base | 3.1 / 3.4 / 4.1 | 0.03 |
| bear on post, pinned with gap | 1.0 / 1.5 / 2.1 | 0.05 |
| stack rocking, velcro only | 0.3 / 0.6 / 1.1 (unstable low) | 0.08 |
| frame rocking on ties | 2.3 / 6.5 / 11 (slack → 0) | 0.06 |
| shell dance slip on post (excitation) | 0.4 / 0.75 / 1.5 | 0.1 |
| torso on dance pivot | 0.5 / 1.2 / 2.5 | 0.05 |
| arms / head on neck | 1.5–7 / 2.5–8 | 0.06 |
| post-in-slot rattle (impact) | 6 / 10 / 25 | 0.1 |
| cart horizontal / pitch-roll / bounce | 3.7–11 / 4.5–12.6 / 6.4–14 | 0.08–0.1 |
| caster swivel rattle | 8 / 15 / 30 | 0.08 |
| shell ovalling / seam | 15 / 30 / 60 | 0.05 |
| drivetrain loaded (rotor + cart on magnetic spring) | 13.5 / 16.9 / 23.2 | 0.03 |
| stepper rotor mid-band | 180 / 236 / 303 | 0.02 |
Forbidden bands (Hz): **0.3–6** (sway, rocking, torso, arms; no un-ramped periodic start/stop), **6–30** (slot rattle, cart, mesh, drivetrain ring; rise times < 80 ms), **150–330** (rotor mid-band; 250 st/s is INSIDE; drums the shell). Excitations: E1 250 Hz step train; E3 0.278 Hz comb (flat to > 10 Hz without ramp); E5 2 backlash impacts per cycle; E8 caster flip; E9 load transfer; E10 dance 0.4–1.5 Hz (20 s, MEASURED cycle).
Worst modes in run_v3: a → shell ovalling @60 Hz 9.0 m/s² + rotor 180 Hz; b → rotor 236 Hz 8.3 m/s²; c → shell @30 Hz 5.5 m/s². Fatigue ranking: hub set screws > mount bolts/breadboard jumpers > ties/velcro > armature bolts > caster bolts.

Dance zig-zag chain (v3.1, from Tony's lean sketch): post 3° (stationary), ball −22°, legs +30°, torso −31° → alternating signs, two nodes = shape of a beam 3rd bending mode (hinges: ball bottom velcro, feet/slot, hip). 3-link model (0.47/0.50/0.70 m; 1.5/1.0/4.5 kg): CoM shift 0.071 m vs 0.187 m rigid for same top travel → **~60 % cancellation** (Tony read this off his own sketch: the zig-zag "mass-center line" is far more upright than the rigid-lean line). Reaction into post→frame→ties: 2–14 N·m at 0.4–0.75 Hz vs 24 N·m lift-off → no lift-off; extreme 1.5 Hz + sketch angles: 43 N·m → lift-off, 22 N per tie (10 % rating). Dance harmonics (2×, 3×) land in the 1.8–3.6 Hz frame sway band → never drive during the dance. Real loads: hip hinge, slot travel 5–18 cm per sway, bottom velcro in peel.
Direction convention (Tony's): lean signed relative to the post (left/right).

Recommended profile (modes.json): 1/16 microstep; S-curve (sin²) ramp ≥ 1 s; max segment accel ≤ 0.41 m/s² (1/3 of worst-case fixity) — ≤ 1 m/s² acceptable for the zip-tied case; cruise ≤ 250 full st/s equiv; dwell uniform random 2–4 s; segments ≥ 6–8 cm or rigid front wheels; full stop before reverse; no drive during Try Me.

## (e) Electrical / control

| pin (BCM) | role | main.cc use |
|---|---|---|
| GPIO13 | STEP1 → driver 1 → wheel ? | pulsed with STEP2 |
| GPIO20 | STEP2 → driver 2 → wheel ? | pulsed with STEP1 |
| GPIO26 | DIR1 | HIGH "CW", LOW "CCW" |
| GPIO21 | DIR2 | always opposite of DIR1 |
Which STEP pin → which physical wheel: UNVERIFIED (trace the wires).
- Drivers: 2 × purple modules with heatsinks; code says A4988, photo looks DRV8825-class; chip UNIDENTIFIED. Current limit: Vref unmeasured (A4988 ≈ Vref/0.8 with 0.1 Ω sense; DRV8825 = 2·Vref; clones vary). MS1–3 unconnected → full step (GUESS). ENABLE not driven (default enabled → holding current whenever powered; motors hot at idle). Rated motor 1.68 A/phase; 12 V supply above VMOT min ~8 V. Electrolytics on rails. Breadboard jumpers (intermittent STEP risk).
- Power: Anker SOLIX (model UNKNOWN, 12 V/10 A/120 W car socket on C-series) → car plug → red/black → Wago → rails. Not metered. Pi power path: UNKNOWN.
- Try Me: 2 bare wires = momentary button; code-fire needs relay/optocoupler/transistor across the pair (Kerney). One pulse = one 20 s cycle; mid-cycle tap ignored; cooldown ≥ 22 s.
- Failure modes: (1) Ctrl+C / crash leaves STEP/DIR pins at their last state — no signal handler, no cleanup; a STEP left HIGH is harmless to motion but DIR/STEP state persists into the next program; drivers stay enabled, holding current flows. (2) a.out is 32-bit armhf — likely will not run on 64-bit Pi OS; rebuild. (3) wiringPi on Pi 5: UNKNOWN (upstream wiringPi 3.x claims Pi 5 support; the apt package may be absent) — fallback libgpiod/lgpio/pigpio. (4) No ENABLE line → cannot de-energize motors from code; only the power switch. (5) No E-stop wired (whiteboard lists it). (6) Unplugging a motor bundle under power kills a driver. (7) 250 st/s in rotor mid-band → missed steps = position not knowable open-loop. (8) Hub set screws loosen under 250 Hz ripple.

## (f) Software model

Current main.cc (Tay, FACT): wiringPiSetupGpio; 4 outputs; infinite loop {DIR1=1,DIR2=0; 200 × (STEP2,STEP1 high; 2 ms; low; 2 ms); delay 1000; DIR1=0,DIR2=1; 200 steps; delay 1000}. No args, no ramp, no microstep config, no exit handler, starts moving immediately on launch; needs sudo. printf per segment.

Tony's API draft (OPEN — his to work out; listed, not resolved):
- `Promise move(direction_enum, milliseconds, lambda_after, trigger_id)` — queued, mutex, one motion at a time.
- `Promise dismiss(trigger_id, lambda_after)` — drop queued moves of that trigger_id.
- Promises auto-reject with a reason.
- trigger_id = per human; identify once at entry, cheap tracking after; per-visitor state (LLM/scene output) travels with the track; tracker PUSHES events (enter, leave, gesture+id) to the decider — observer pattern.
- OPEN design attacks (do not resolve): does dismiss abort the running segment (abrupt stop = jerk → resonance/lift-off)?; reject-reason enum (dismissed / busy / unsafe-during-Try-Me / estop); milliseconds vs steps as the unit; Promise + lambda_after redundancy; missing ramp / random-dwell parameters (the free fix lives in the profile, not the caller); C++ ↔ Python bridge (subprocess to a C++ binary vs Python GPIO); who owns per-visitor state (tracker vs decider); event list + payload = the interface to agree with McKay; hand↔face ownership; masks / turned faces; one-person YAGNI fallback (trigger_id = 0, new id after scene empty ~3 s).

Pipeline (target): camera → vision (McKay: YuNet face, FER, MediaPipe palm + hand via cv2.dnn; largest face / best hand only) → [NEW] person detector + ByteTrack/SORT tracker → trigger_id; wrist-keypoint precedence for hand ownership (RTMPose-t only on ambiguous boxes) → [NEW] decider input events → McKay's decider / scene / reactions → [NEW] motion module (cart API) + Try Me pulse.
Hook point in McKay's app (READ-ONLY, FACT): `src/barnaby/app.py` main loop: `observation = vision.infer(small)` → `StableLabel` filters (gesture, expression) → on label change `on_perception(PerceptionEvent(gesture, expression, hand_confidence, face_confidence, inference_ms))` (`src/barnaby/reactions.py`, frozen dataclass; currently `print(json.dumps(...))`). Gesture labels: open_palm, peace, pointing, thumbs_up, fist, unknown, none. There is no trigger_id, no per-person anything, no hook for motion.
Where a new module sits: a separate file/package (e.g. `src/barnaby_ext/` or a sibling process) that either (i) consumes the JSON lines `on_perception` prints on stdout (zero edits to McKay's code), or (ii) is registered as an observer by a thin wrapper that imports McKay's modules and runs its own loop. Motion side: a separate process (C++ binary or Python) owning the GPIO, with the queue/mutex, ramp profile, dwell randomizer, "no drive during dance" interlock and exit cleanup. The bridge choice is OPEN.

## (g) Capability envelope (what the bear can physically express today)

- Try Me dance: one-shot, 20 s, fixed choreography (shell sway on the post, jaw), not interruptible, ≥ 22 s cooldown. 1 bit.
- Cart: forward or back, ±3.64 cm per 200-step segment at 4.55 cm/s (MODEL from main.cc; real travel with instant start may be near zero — MODEL stall, UNTESTED). Speed = STEP_DELAY_US; distance = step count; direction = DIR pins. No ramp today.
- Vocabulary = combinations in time of {dance one-shot} × {cart dir, steps, rate, dwell} — not designed yet; dance and cart motion must not overlap.
- Independent wheel stepping: STEP1 and STEP2 are separate pins driving separate drivers/wheels (Tony's insight). UNVERIFIED mapping. Open question for Tony: what does single-wheel stepping do?
- Not available: turning as implemented code, sound/LED moods (UNKNOWN other outputs), position feedback (open loop; missed steps unknowable), E-stop (not wired).

## (h) Top unknowns, ranked by impact → cheapest resolution

1. Does the cart move at all under main.cc with the real load (stall vs wiggle)? → Test B, bear OFF, then empty cart on carpet, tape measure. 10 min.
2. Rear-wheel load fraction (sets slip; 0.25 vs 0.5 is the difference between 0 and 1.6 cm forward travel) → bathroom scale under each rear wheel. 5 min.
3. Frame fixity in practice: tie tension, 1 mm gap, whether the frame rocks when pushed at the bear's chest → push test by hand + phone accelerometer (sway freq + damping). 5 min. Then $5 fix (ties + EVA strip).
4. STEP pin → wheel mapping and single-wheel behaviour (Tony's open question) → trace the two STEP wires; one-pin test with the bear OFF the cart. 10 min.
5. Driver chip + Vref (sets torque, heat, missed steps) → read chip marking, measure Vref with multimeter. 5 min. Ask Tay.
6. wiringPi / build on the Pi (Pi 5 support, 32-bit a.out) → `g++ main.cc -lwiringPi` on the Pi; if it fails, switch library (Tay's call). 10 min.
7. Gear ratio 5:1 vs 5.18 and exact wheel dia (±4 % on all distances) → count output turns per 1000 steps; calipers on the wheel. 5 min.
8. Total mass and SOLIX / fog models → weigh or read labels. 5 min.
9. Dance sway rate / amplitude of the shell (0.4–1.5 Hz assumed; decides whether its harmonics pump the frame) → phone accelerometer on the chest during one 20 s cycle. 1 min.
10. Slot clearance / wing-nut play / shell wall (impact and crack risk) → rock the post by hand, look through the slot, knock on the shell. 3 min.
11. Pi 5 fps for detector + tracker (+ pose) (decides the trigger_id design) → time NanoDet/YOLOX-nano + ByteTrack on the Pi before committing. 30 min.
12. Sugar-box dimensions (pins the photo scale: ball dia, bear height) → tape measure. 1 min.
