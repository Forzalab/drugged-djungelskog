---
name: motor-hardware-2026-10-09
description: Bear has TWO motion systems (Fri build 16:02 PT) — Try Me toggle pigtail (built-in dance) + franky-fedbear stepper board; facts, photos-read, open unknowns
type: fact
status: stable
stale_after: 2026-10-24
---
## 1. Try Me pigtail (toy's built-in dance) — Tony, corrected 16:08 PT
- 2 bare wires (red + black) = the toy's Try Me button, literally.
- Touch the ends together once → one dance cycle runs → stops BY ITSELF at the end of the cycle. Not a toggle. (16:02 "toggle" note was wrong.)
- So from code: fire-and-forget pulse (relay/optocoupler/transistor across the pair). A lost pulse = one missed dance, no state drift.
- Only one motion. No direction or speed control. Reverse-engineering: rejected by Tony (maybe after exam).
- MEASURED 16:12 PT (Tony): full cycle = 20 s. Tap mid-cycle → cycle unchanged (still 20 s total; read as ignored). → cooldown ≥ 22 s (cycle + 2 s, see trigger-any-hand.md).
- NO tongue test. The dance itself is the indicator.

## 2. franky-fedbear stepper board — github.com/tayG-oss/franky-fedbear @3f99a13 (Oct 3, only commit)
- main.cc (64 lines, wiringPi, BCM): STEP1=13 STEP2=20 DIR1=26 DIR2=21. 200 steps/rev, 2 ms high + 2 ms low = 0.8 s/rev. Loop forever: 1 rev CW, 1 s, 1 rev CCW, 1 s. DIR1/DIR2 always opposite. No ENABLE pin, no signal handler, starts moving at launch, Ctrl+C leaves pins as they were.
- a.out = 32-bit armhf binary → likely will not run on 64-bit Pi OS; rebuild on the Pi (g++ main.cc -lwiringPi; sudo). wiringPi on Pi 5 = UNKNOWN.
- Board (photos): Pi ribbon → T GPIO extension board → 2 purple stepper drivers with heatsinks (purple looks like DRV8825; code says A4988; same STEP/DIR pins, different current-limit formula) → two 4-wire motor bundles; 2 electrolytic caps on power rails.
- Motor power: Anker SOLIX via 12 V car-socket plug → red/black → Wago lever connectors → breadboard rails (photo 16:08). 12 V is above driver VMOT minimum (~8 V). Not metered.
- Steppers drive the wheeled carpet platform (cart) — 4-wire bundles run through Wago connectors to it (photo 16:08).
- Safety: never unplug a motor bundle while drivers are powered; shafts/wheels free; hand on power for first run.

## 3. Cart behavior — teammate report 16:2x PT (NOT tested by Tony)
- Steppers drive the cart's WHEELTEC wheels. Cart moves forward / backward depending on pin state (DIR). Matches main.cc: 1 rev one way, 1 s, 1 rev back.
- franky code = wheel motion only. No turning in current code (both STEP pulse together; DIR always opposite = mirrored mount → same travel direction, inferred).
- Test B (Tony running main.cc himself) NOT done.

## Open problems (raised by TONY at the build, Fri 16:2x; team went quiet = taken seriously)
- P1: Try Me cycle = 20 s, cannot stop or restart → each reaction locks the bear 20 s.
- P2: cart only goes forward/back.
- Note for later: two independent outputs exist (20 s dance + cart dir/steps/speed/timing). Vocabulary = combos in time. Not designed yet.

## Conflicts
- Earlier note "movement = Try Me dance only" vs a real stepper board exists. Two systems, or steppers are a future add. Ask the team.

## 4. Cart sim v0 (16:33 PT) — _files/cart-sim/cart_sim.py
- Mostly GUESS inputs (65 mm wheel, direct drive, 0.40 N·m NEMA17, bear 9.07 kg from listing S0-facts.md:601, cart 3 kg).
- Verdict STALL at instant start (margin 0.018); cruise fine (2.43). Start model = reach speed within 1–2 steps (pessimistic, crude).
- CONFLICTS with teammate report "cart moves fwd/back" → model or inputs wrong. Observation (Test B) beats sim. Do not trust v0.
- Sensitivity: gear ratio > wheel diameter > step timing > holding torque > Vref > bear mass > torque falloff > cart mass.

## 5. Real specs from photos (16:35 PT, Tony)
- Motor label: "Geared Stepper Motor 17HS15-1684S-PG5" = NEMA17 + planetary gearbox (nominal 5:1, exact ratio to confirm). Rated 1.68 A.
- Wheel: WHEELTEC, ~6 cm diameter, clamp hub on gearbox output shaft.
- Layout RESOLVED 16:41: TWO driven rear wheels (passenger + driver side photos), motors mounted mirrored → DIR1/DIR2 opposite = same travel direction (confirms main.cc inference). Front = casters.
- Load: metal dolly frame + wood + carpet; large gold ball (~60–70 cm) on cart; full-size Barnaby (70" tall) standing on the ball. Not weighed (Tony: research instead).
- Driver: purple module, unidentified (DRV8825 vs A4988 clone).
- Sim v1 rerun requested with these (gear ratio = #1 sensitivity in v0).

## 6. Cart sim v1 (16:4x PT) — real motor + 6 cm wheel + 2 driven wheels
- Specs (agent-cited, not re-verified): 17HS15-1684S-PG5 = 5.18:1, 90% eff, 2 N·m cont / 4 N·m peak output, 1.68 A, 1.65 Ω, 3.2 mH (tindie stepperonline listing). Dolly 20.4 lb (gorillamade GFS-1830, assumed). Ball mass GUESS. Mass 17.5 / 24.1 / 33.3 kg.
- Commanded: 14.5 wheel RPM, 4.55 cm/s, 3.64 cm per segment, 0.18 mm per motor step.
- Torque checks: STALL at instant start (margin 0.12–0.83). With slip model: travel 3.38 / 1.56 / 0.12 cm of 3.64 (low/mid/high). Matches teammate "small wiggle".
- Cheapest fix = code: acceleration ramp or slower step rate.
- Measure first: rear-wheel load, total mass, Vref + chip marking, exact wheel diameter, gear ratio (count output turns per 1000 steps).

## 7. Resonance study launched (16:52 PT, Tony's idea: "think like an earthquake engineer")
- Concern (Tony): periodic shaking near a natural frequency of the bear/ball/cart stack → amplification → break stuff / tip.
- 3 agents in scratchpad cart-sim/: A (Fable) modes + RESONANCE.md + modes.json; B mass budget (fog machine, Anker SOLIX, ball, bear, dolly, buffer X=5 kg) → masses.json; C sim v2 (FFT of drive, 1-DOF mode responses, tip check, profiles: main.cc vs ramp vs slower). Results → this file §8 when back.
- Open design Q (Tony): "how to code it in, there's no API" — Cluck in progress.

## 8. Mass budget (agent B, 16:5x PT) — cart-sim/masses.json
- Dolly 8.8–9.7 kg (gorillamade GFS-1830, 30x18 in); wood+carpet 1.5–4.5 (est); motors+wheels ~1.5; EPS ball 1–6 (est); Barnaby 9.07–11.3 (spirithalloween 266092); fog machine 1.4–4.5 (ADJ VF400 etc.); Anker SOLIX 4.1 (C300) / 10.9 (C800 Plus) / 12.9 (C1000), all with 12 V 120 W car socket (F2000 = 30.5 kg → +18); Pi ~0.3; buffer X=5.
- TOTAL 32.4 / 44.5 / 56.4 kg. Rear-wheel load share est 0.25/0.40/0.50.
- Geometry est: deck 0.17 m, ball 0.65 m, bear 1.78 m, bear feet at 0.82 m, stack top ~2.6 m; cart CoG 0.52–0.58 m; bear-on-ball CoG 1.33–1.41 m; track ~0.40 m, wheelbase ~0.66 m; bear (43 in wide) overhangs 18 in deck.
- Unknown: SOLIX model, fog model, ball solid/hollow, bear mass distribution, attachment of bear/ball, real track.

## 9. Sim v2 (agent C, 16:5x PT) — mid mass 44.5 kg, rear share 0.40, MODEL ONLY
| profile | travel fwd/rev | worst mode | fore-aft tip margin | lateral tip margin |
|---|---|---|---|---|
| a main.cc 250 st/s instant | 0.00 / 0.08 cm (stall) | rotor mid-band 180 Hz | 1.64 | 80 |
| b + 0.3 s ramp | 0.55 / 3.52 cm | rotor mid-band 236 Hz | 0.84 (TIPS) | 2.03 |
| c 125 st/s instant | 0.00 / 0.56 cm | drivetrain spring 23 Hz | 3.60 | 100 |
- Tip threshold 1.55 m/s² (strapped stack, modes.json). Only b really moves → only b excites 0.5–6 Hz stack modes.
- Every profile hits a forbidden band (rotor 150–330 Hz; drivetrain 15–40 Hz; reversal harmonics + caster swivel 0.5–6 Hz).
- Rear-share sweep (b): fwd 0.03/0.55/0.79/1.16/1.59 cm at 0.3–0.7; reverse ~3.5 cm. Fwd weak = casters start pointing wrong way, never finish 180° swivel (worst-case assumption).
- High mass 56 kg: all stall forward. Caster params are agent guesses.
- Lesson: the obvious fix (ramp) moves the cart AND may tip the bear. Needs real measurements before any motion test with the bear on.

## 10. Resonance analysis (agent A, Fable, 17:0x PT) — _files/cart-sim/RESONANCE.md + modes.json
- RISK 1: ball fixation UNKNOWN. Bear+ball CoM 1.17 m above deck, ~12 kg. Resting ball: tips/rolls at 0.17 m/s² vs jerk 0.6–0.8 → FAILS. Strapped: 1.68 m/s² (margin ~2.5×). Bolted: 2.5. Whole cart safe (4.3–7.2).
- RISK 2: fixed 3.6 s start/stop cadence = harmonic comb (0.278 Hz spacing) through bear sway (0.7/2.0/4.7 Hz, assumed armature) + stack rocking (0.8/2.1/5.9 Hz); Q 10–25 → 1.0–2.5 m/s² at bear CoM after 10–25 cycles ≈ strapped tip accel.
- RISK 3: casters need 5–8 cm to flip 180°; segments 0.1–3.4 cm → casters stay sideways, scrub (~39 N each, up to 1.8 m/s² lateral). Load transfer ±14–18% rear load → asymmetric traction (119 N fwd vs 91 N rev) → creep.
- Also: 250 full steps/s inside stepper mid-band (180–303 Hz) → chatter/missed steps; drivetrain 13–23 Hz rings each start; hub set screws = first fatigue failure.
- FORBIDDEN BANDS (Hz): 0.5–6, 6–15, 15–40, 150–330.
- RECOMMENDED: 1/16 microstep; S-curve ramp ≥1 s (accel ≤0.5 m/s²); random dwell 2–4 s (never fixed cadence); segments ≥6–8 cm or rigid front wheels; full stop before reversing; NO cart motion during the 20 s Try Me dance.
- CHEAPEST MEASUREMENTS: (1) push-and-release, phone accelerometer taped to bear chest → sway freq + damping; tap deck → bounce. (2) push ball sideways ~50 N: does it move? base half-width. (3) scale under each rear wheel → rear load fraction.

## 11. Bear mount photos (17:0x PT, Tony) — Fable re-analysis running
- SEEN: black square steel post from bear crotch down into a slot cut in the ball top, wing-nut clamp; ball = two halves joined at a seam with screws; black strap (velcro) foot↔ball. Tony sketch: post runs down through the ball ("stable" at top), velcro at feet AND at ball bottom, "gap" at the bottom.
- SEEN: sticky notes "WILL BITE" / "DO NOT MOVE" on bear; whiteboard list incl. "Roar", "Go faster!", "E-stop"; powdered sugar box (sugar spray plan).
- Implication (to verify): load path may be post → base, ball = cosmetic shell → tipping model changes. Agent writes PHOTOS.md + questions + modes v2 in _files/cart-sim/.

## 12. Photo-based model v2 (Fable, 17:2x PT) — _files/cart-sim/PHOTOS.md, RESONANCE.md v2
- SEEN: ~22 mm square steel post crotch → slot in ball top (clearance ~1–4 mm across, ~10 cm along); wing-nut bolt at ball top; ball = 2 screwed halves, hollow; velcro foot↔ball; cable down slot; arms asymmetric (2–4 cm CoM offset); wooden cradle rails under ball.
- SCALE (sugar box ~3.75 in wide, UNVERIFIED dims; cross-check Post-its): ball 0.47 ± 0.05 m (was 0.65); bear 1.20 ± 0.10 m feet-to-head (70 in listing likely incl. stand); stack top ~1.84 m; stack CoM 0.80 m above deck (was 1.17).
- INFERRED: post = original telescoping stand pole = structural spine; wing nut = height lock (backlash at max moment); ball = cosmetic hollow shell ~1.5 kg; bear ~6 kg hollow frame.
- TIP MARGINS (mid 43 kg; a main.cc / b 0.3 s ramp / c 125 st/s):
  - post FIXED to deck: 6.1 / 2.8 / 11.8 (lateral 4.2) — sway 3.3–4.3 Hz.
  - pinned WITH GAP: 1.24 / 0.57 TIPS / 2.4 (lateral 0.85 TIPS) — sway 1.0–2.1 Hz.
  - VELCRO only: 1.71 / 0.79 TIPS / 3.3 (lateral 1.17) — statically unstable w/o velcro, resonance 7–11 cm at CoM.
- New modes: shell ovalling 30–60 Hz; post-in-slot impact 6–25 Hz (DAF up to 6). Forbidden bands: 0.3–6, 6–30, 150–330 Hz.
- TOP ACTION: screw pole base plate to the deck + shim/clear the slot BEFORE any motion test with the bear on.
- QUESTIONS for next build (ranked): 1 post bottom → deck / base plate (screwed? velcro?) / nothing; 2 what/how big is the "gap"; 3 wing nut = telescope lock or shell clamp, any play; 4 slot clearance mm; 5 shell material/wall/weight; 6 velcro patch sizes + cradle contact; 7 sugar box W×D×H (tape); 8 does the dance move torso vs post; bear weight w/o pole.

## 13. Tony's answers to the build questions (17:2x PT)
1 Post = integral part of a black tubular steel frame (original stand); frame sits ON the deck, held by ZIP TIES (not bolted).
2 Gap ≈ 1 mm. 3 Wing nut: unknown. 4 Wobbling pole wobbles the whole structure (whole-frame wiggle, not a telescoping joint).
5 Ball = hollow plastic shell, only the pole passes through. 6 Hook-and-loop velcro, sizes guessed. 7 Sugar box: online estimate OK.
8 Post effectively fixed; bear shell + ball move relative to it (Try Me dance) → internal excitation.
- Fable rerun (v3, "frame zip-tied to deck" case) requested.
- 17:2x PT Tony lean sketch (_files/cart-sim/photos/lean-sketch-2026-10-09.png): during a dance lean the post stays vertical; torso / legs / ball lean at ALTERNATING angles (zig-zag ~+30° / −30° / +25°) = articulated multi-link chain around a fixed post, not a rigid lean. Sent to Fable for v3 (CoM shift vs rigid, reaction moment into post→frame→zip ties, higher-mode shape).

## 14. Model v3 — frame zip-tied to deck (Fable, 17:3x PT)
- Bear ~6 kg on post welded into ~3.5 kg tubular stand frame (base ~0.45×0.6 m) on deck, 1 mm gap, 3–4 × 4.8 mm / 50 lb (222 N) zip ties (gexpro TY5253M). Stack 11 kg, CoM 0.66 m above deck. Sway 1.8/2.8/3.6 Hz. Dance ≈ 3 kg @0.75 Hz ±5 cm → 4 N·m on frame vs 24 N·m gravity restoring + 2 slot impacts per sway.
- Tip (frame lift-off): 3.3 m/s² transverse / 4.5 longitudinal. Margins: a main.cc 3.8; b 0.3 s ramp 1.8 (lateral 5.3; low mass 1.35); c 125 st/s 7.4. → v3 says NO tipping in any profile (v2 velcro case was 1.7/0.8/3.3).
- Zip ties: 0 N at real jerk, 17 N at whole-cart tip accel vs 222 N rating; break needs ~30 m/s². Weak link = slack/creep + 1 mm gap → free rocking, deck hammering each start/stop + dance sway.
- Worst modes: shell ovalling 30–60 Hz (5–9 m/s²), rotor mid-band 180–236 Hz, slot rattle 6–25 Hz; all profiles still hit forbidden bands.
- FIXES by cost: (1) free/code: S-curve ramp ≥1 s (≤1 m/s²), 1/16 microstep, random 2–4 s dwell, stop before reverse, no drive during dance. (2) ~$5: 6× 120 lb ties with tie gun, EVA strip under rails (kill gap/creep), foam shims in slot, thread-lock hub set screws. (3) ~$15: pipe/saddle clamps through plywood → fixed case.
- Open: sugar box dims, frame length, tie count/tension, wing nut, dance rate/amplitude. Lean-sketch 3-link analysis requested as v3.1.

## 15. v3.1 dance zig-zag chain (Fable, 17:3x PT)
- Sketch angles (from vertical): post 3° (stationary), ball −22°, legs +30°, torso −31° → alternating; shape = beam 3rd bending mode (2 interior nodes), not a rigid lean.
- 3-link chain (0.47/0.50/0.70 m; 1.5/1.0/4.5 kg): CoM shift 0.071 m vs 0.187 m rigid for same top travel → ~60% cancellation (plausible 8 cm top travel: 0.020 vs 0.048 m).
- Reaction into post→frame→ties at 0.75 Hz: 4–14 N·m vs 24 N·m lift-off → no lift-off. Extreme 1.5 Hz + sketch angles: 43 N·m → lift-off, 22 N/tie (10% of rating).
- Dance 0.4–1.5 Hz sits just under the 1.8–3.6 Hz frame sway band (inside it if ties slack) → harmonics can pump rocking. Real loads: hip hinge, slot travel 5–18 cm per sway, bottom velcro. Ties still not the weak link; slack + 1 mm gap are.
- 17:3x PT Tony (own reasoning, photos/lean-com-tony-2026-10-09.png): direction must be signed RELATIVE TO THE POST (left/right), not "away" (loses direction — he corrected Cluck's convention). Drew rigid-lean line vs zig-zag "mass-center line": zig-zag line is far more upright → less lean load. Matches Fable v3.1 (~60% cancellation). Insight earned, not given.
- 17:5x PT Tony insight: STEP1/STEP2 map one-to-one to the two wheels (2 pins, 2 wheels, 2 drivers) → each wheel can be stepped independently. Current main.cc always pulses both together → straight fwd/back only. Implication (Cluck in progress, not told): independent step counts/rates → turning/pivot in code, no hardware change → P2 ("cart only fwd/back") may be a CODE limit. Verify mapping: trace GPIO13/GPIO20 wires to which driver → which motor bundle, or one-pin test with the bear OFF the cart.

## 16. Surfaces (Tony, 18:1x PT) — LOAD-BEARING FACT
- TEST = carpet (indoor). PROD = campus concrete ground (likely outdoor).
- Sims v1–v3.1 assumed carpet only → re-run for concrete before prod. Expected changes (to verify, not computed): higher rubber grip + lower rolling resistance (easier start, less slip); casters swivel easier; LESS damping → more rattle/impact into the 1 mm gap + shell; cracks/expansion joints = impact inputs; SLOPE (even 1–3%) → roll-away when idle + uneven drive load; outdoor WIND on a ~1.8 m bear = side load (tip!); heat/rain/battery.
- Measure at the prod spot: slope (phone level app), joint spacing/height, wind exposure.
- Weather (checked 18:1x PT Oct 9; assumes Clovis, CA): no real forecast exists 3 weeks out. Base rate Oct 28–Nov 3: highs ~72–74°F, lows ~47–49°F, rain on ~13–15% of days historically (weatheronthisday.com, 55 yr NOAA); October avg ~0.84 in. Strong El Niño 2026–27 → wet signal mainly from Dec (NIFC Oct 1 outlook). Wind data not found. Plan: ONE check of the 7-day forecast ~Oct 24–25; keep a tarp/cover as cheap rain backup (electronics on the cart).
