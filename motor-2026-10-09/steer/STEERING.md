# STEERING.md — turning the bear cart by wheel-speed ratio (2026-10-10)

Tags: **FACT** = sourced (URL) or read from project files; **DERIVED** = computed from FACT/GUESS inputs here; **GUESS** = assumption, measure it.
Project inputs come from `brain/projects/cocaine-bear/topics/motor-hardware-2026-10-09.md`, `cart-sim/masses.json`, `cart-sim/RESONANCE.md` v3/v3.1, `franky-fedbear/main.cc`.

## 0. Inputs used

| quantity | value | tag |
|---|---|---|
| wheel dia | 6 cm (WHEELTEC) | FACT (photo label, not measured) |
| gearbox | 5.18:1 planetary (17HS15-1684S-PG5) | FACT (listing, agent-cited; confirm by counting) |
| steps/wheel rev | 200 × 5.18 = 1036 full steps | DERIVED |
| travel per full step | π·6 cm / 1036 = **0.0182 cm** | DERIVED |
| max commanded speed | 250 full steps/s (main.cc 2 ms + 2 ms) → **4.55 cm/s** | DERIVED |
| track T (rear wheel centre-to-centre) | **0.40 m** | GUESS (masses.json) |
| wheelbase L (rear axle → front caster pivots) | **0.66 m** | GUESS (masses.json) |
| front caster lateral offset | ±0.20 m | GUESS (18 in dolly) |
| caster trail e | 3–5 cm; 180° flip needs 5–8 cm travel | GUESS (RESONANCE.md E8) |
| frame lift-off (zip-tied case v3) | 3.3 m/s² transverse, 4.5 longitudinal | DERIVED in RESONANCE v3 |
| v2 velcro case tip | ~1.5 m/s² | DERIVED in RESONANCE v2 |
| forbidden bands | 0.3–6, 6–30, 150–330 Hz | DERIVED in RESONANCE v2/v3 |
| STEP1=GPIO13, STEP2=GPIO20, DIR1=26, DIR2=21; DIR always opposite (mirrored mounts) | | FACT (main.cc) |
| STEP1↔left / STEP2↔right mapping | unverified | GUESS |

## 1. Framing: this is differential drive, not car steering

- **Car (Ackermann) steering**: wheels are *angled* by a steering mechanism; the driven rear wheels of an RWD car only push, and the differential lets them turn at whatever speeds the geometry imposes. The turn is decided by the steering angle, not by wheel speeds. ([robotix tutorial](https://2020.robotix.in/tutorial/mechanical/drivemechtut))
- **Our cart**: no steering mechanism. Two independently driven wheels on one axle + free swivel casters = **differential drive** (power wheelchair, robot vacuum, most AMRs). It "changes its direction by varying the relative rate of rotation of its wheels and hence does not require an additional steering motion"; casters are there to keep it from tipping. ([robotix tutorial](https://2020.robotix.in/tutorial/mechanical/drivemechtut))
- Not skid-steer either (skid-steer drags fixed wheels sideways; our casters swivel instead). ([robotix tutorial](https://2020.robotix.in/tutorial/mechanical/drivemechtut))
- **Why Tony's ratio idea works anyway**: in differential drive the ratio of the two wheel speeds *is* the steering input. Both wheels rotate about one point on the rear-axle line (the instantaneous centre of curvature, ICC); fixing the ratio fixes where that point is, i.e. the turn radius. ([Columbia ICC notes](https://www.cs.columbia.edu/~allen/F15/NOTES/icckinematics.pdf)). Wording fix: say "like a wheelchair", not "like an RWD car". In a car the speed difference is a *result* of steering; here it is the *cause*.
- Stepper bonus: steps are counted, so the ratio is exact (open loop), as long as no step is lost and no wheel slips.

## 2. Kinematics

Wheels at ±T/2 from the axle midpoint, speeds vL, vR. Both turn about the ICC at the same yaw rate ω:
vR = ω(R + T/2), vL = ω(R − T/2) → **ω = (vR − vL)/T**, **R = (T/2)·(vR + vL)/(vR − vL)**, measured from the axle midpoint. ([York lab](https://www.eecs.yorku.ca/course_archive/2019-20/W/1011/labs/7/differential-drive-robot.html), [Columbia](https://www.cs.columbia.edu/~allen/F15/NOTES/icckinematics.pdf)) FACT

With **ratio r = v_inner / v_outer** (outer wheel at the commanded speed):
- R = (T/2)·(1 + r)/(1 − r)
- r = 1 → straight (R = ∞); r = 0 → **pivot about the stopped inner wheel** (R = T/2); r = −1 → **spin in place** (R = 0, about the axle midpoint); −1 < r < 0 → ICC between the wheels.
- Heading change Δθ = (s_outer − s_inner)/T = N_outer·0.0182 cm·(1 − r)/T (rad).
- Inverse: r = (2R − T)/(2R + T); outer steps for heading θ: N = θ·T/(0.0182 cm·(1 − r)).

### Worked table (T = 0.40 m GUESS, L = 0.66 m GUESS; all DERIVED)

Outer wheel at 250 full steps/s (4.55 cm/s). "Caster angle" = how far each front caster must swivel from straight to roll along its circle (inner / outer caster).

| r | R (axle mid) | Δθ per 200 outer steps | Δθ per 1000 | yaw rate | centripetal a at axle mid | caster swivel in / out | outer steps for 90° | time for 90° | inner wheel rate |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ∞ | 0° | 0° | 0 | 0 | 0 / 0 | — | — | 250 /s |
| 0.9 | 3.80 m | 0.52° | 2.6° | 0.7°/s | 0.0005 m/s² | 10° / 9° | 34 500 | 138 s | 225 /s |
| 0.75 | 1.40 m | 1.30° | 6.5° | 1.6°/s | 0.0011 | 29° / 22° | 13 800 | 55 s | 188 /s |
| 0.5 | 0.60 m | 2.61° | 13.0° | 3.3°/s | 0.0019 | 59° / 40° | 6 900 | 28 s | 125 /s |
| 0.25 | 0.33 m | 3.91° | 19.5° | 4.9°/s | 0.0024 | 79° / 51° | 4 600 | 18 s | 62 /s |
| 0 | 0.20 m (pivot on inner wheel) | 5.21° | 26.1° | 6.5°/s | 0.0026 | 90° / 59° | 3 450 | 14 s | 0 (holding) |
| −0.5 | 0.067 m | 7.82° | 39.1° | 9.8°/s | 0.0019 | 101° / 68° | 2 300 | 9 s | 125 /s reversed |
| −1 | 0 (spin) | 10.4° | 52.1° | 13.0°/s | 0 | 107° / 73° | 1 730 each | 7 s | 250 /s reversed |

Reading: the current main.cc segment (200 steps) turns at most 5° at r = 0. A 90° turn is 3–14 s of driving at the current speed; at a sane ≤150 st/s (see §4) it is 1.7× longer. Turning is slow, which helps.

## 3. What other scales use, and why

| class | typical turning | limits / why | source |
|---|---|---|---|
| Robot vacuum / iRobot Create 2 | drive command: v −500…500 mm/s, radius −2000…2000 mm, special values ±1 = **spin in place**; also direct per-wheel speeds | tiny, low, wide-base: CoM very low → tip not an issue; spin in place is the main manoeuvre because the footprint is round (spinning doesn't sweep extra area) | [npm create2 docs](https://www.npmjs.com/package/create2), [pycreate2](https://pypi.org/project/pycreate2/) |
| Hobby diff-drive (Jetbot-class) | turns in place; wheel ω = (v ± ω_body·L/2)/r with a max wheel speed cap | wheel speed saturation, not tip | [Isaac Sim diff controller](https://docs.isaacsim.omniverse.nvidia.com/5.0.0/robot_simulation/mobile_robot_controllers.html) |
| Power wheelchair | turning radius: mid-wheel drive ~20–26 in, front-wheel 25–28 in, **rear-wheel drive (our layout) 30–33 in** (widest) | RWD + front casters: the long front overhang (casters, footrests) sweeps a big circle; mid-wheel puts the ICC under the user | [MDA Quest](https://www.mda.org/quest/article/front-middle-or-rear-finding-power-chair-drive-system-thats-right-you), [Pride](https://experience.pridemobility.com/electric-wheelchairs/faqs-for-electric-wheelchairs/whats-the-difference-between-front-wheel-drive-rear-wheel-drive-and-mid-wheel-drive-on-my-power-wheelchair) |
| Building code reference | 60 in (1525 mm) turning circle minimum; users often need more because chairs "do not make a perfect circle" | footprint + caster behaviour, not tip | [US Access Board ch.3](https://www.access-board.gov/ada/guides/chapter-3-clear-floor-or-ground-space-and-turning-space) |
| Mobility scooter (tiller-steered, NOT diff drive) | turning radius 42 in (3-wheel) / 54 in (4-wheel) example | Ackermann-like steering → much larger radius than diff drive; included as the contrast case | [Pride 3 vs 4 wheel](https://experience.pridemobility.com/mobility-scooters-topics/faqs-for-mobility-scooters/3-wheel-vs-4-wheel-scooter) |
| Warehouse AMR (MiR250, differential steering) | 2.0 m/s max; needs 1.5 m aisle for a U-turn, 1.55 m corridor for 90° | footprint + safety-scanner fields | [MiR250 spec](https://www.hartfiel.com/wp-content/uploads/2024/04/MiR250-Specs.pdf) |
| AMR / industrial vehicle control practice | cap **lateral accel a = v·ω**; at a given speed a tighter turn → more ω → more lateral accel → tip-over / load slide-off; limit ω or enlarge radius when load CoG is high | tip-over and payload slide | [ORCA diff-drive params](https://orca-robotics.sourceforge.net/head/orca/classorca_1_1VehicleControlVelocityDifferentialDescription.html), [USPTO 9358975](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9358975), [golf AMR patent](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12679481) |
| Swivel casters in general | low swivel friction → easy turning but shimmy at ~5–6 mph; damping adds the drive torque needed to turn; trailing casters scrub when turning >90° | caster behaviour dominates low-speed turning feel | [US4969232](https://patents.google.com/patent/US4969232), [US10259263](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10259263) |

Pattern: **at speed, tip-over (lateral accel v·ω) sets the turn limit; at walking speed and below, footprint and caster behaviour set it.** We are 40× below walking speed.

## 4. What is best for OUR cart

### 4.1 Centripetal acceleration is a non-issue
Worst steady case (r = 0, outer 4.55 cm/s): 0.0026 m/s² at the axle; at the bear post (~0.33 m from the axle, GUESS) during a spin: ω²·d = 0.227²·0.33 = **0.017 m/s²**. DERIVED. Against 3.3 m/s² (v3 lift-off) → margin ~1000×; against 1.5 m/s² (v2 velcro) → ~90×. Tip-over sets no turn limit here. The **start/stop ramps** (same as driving straight) and the **caster kicks** set it.

### 4.2 What actually limits turning (ranked)
1. **Caster swivel scrub.** Starting a turn from straight needs the front casters to swing 10–107° (table). Until they finish, they get dragged sideways: RESONANCE E8 estimates ~39 N per caster and **0.7–1.8 m/s² lateral kicks** (DERIVED there), i.e. 20–55% of the 3.3 lift-off and up to 120% of the v2 1.5 case. That is 100–1000× the centripetal term. Swing travel scales with angle: ~2.5–4 cm for 90°, 5–8 cm for 180° (DERIVED from E8 GUESS trail). Small swivel angles (r ≥ 0.5) and long segments let the casters settle once and then roll. **Spins (r < 0) are the worst case**: both casters must swing past sideways (73° and 107°), right at the front of a 0.66 m lever, and the inner caster ends up pointing partly backwards. Pivot (r = 0) needs 90°/59°.
2. **Start torque / slip with uneven load.** The sim already shows forward starts at the stall edge (margin 0.12–0.83, v1; profile b moves only 0.55 cm forward). Turning adds caster swivel torque and tyre twist on carpet, all carried by ONE wheel in a pivot (r = 0) or by the outer wheel in an arc. A single NEMA17 on carpet pushing ~40 kg sideways via the casters is the most likely step-loss case (DERIVED/GUESS). A stalled outer wheel during a pivot = no motion + buzzing; a stalled wheel in an arc = wrong heading. In arcs with r ≥ 0.5 both wheels push → share the load.
3. **Stepper step rates vs forbidden bands.** 250 full st/s is inside the 150–330 Hz rotor mid-band (FACT from RESONANCE). With a ratio, the inner wheel runs r × outer: at outer 250, r = 0.06–0.12 puts the inner wheel at 15–30 st/s = inside the 6–30 Hz drivetrain/slot-rattle band; at outer 125, r = 0.05–0.24 does. Full-step pulses at those rates hammer the gearbox. **Fix = 1/16 microstep** (torque ripple moves to 16× the rate and shrinks ÷16, per RESONANCE). Without microstep: keep outer ≤ 140 st/s (below 150 Hz band) and pick r so the inner rate is ≥ 40 st/s or exactly 0 (r = 0 or r ≥ ~0.3 at outer 140).
4. **Yaw resonance.** Yaw rates are ≤ 0.23 rad/s and steady; what excites the 0.3–6 Hz stack band is how fast yaw *changes*. If both wheels ramp together with a constant ratio, yaw rate ramps with the same S-curve as speed → same spectrum as a straight move, already handled by the ≥ 1 s ramp. Changing the ratio mid-move (or starting one wheel before the other) gives a yaw step → forbidden-band content. A spin also puts the bear's post near the ICC so its sway sees mostly rotation, not translation (GUESS, mild).
5. **Carpet.** Pile drag on the casters and a twisting tyre in a pivot raise the needed torque and make the real heading smaller than computed (GUESS: expect 5–20% under-turn until calibrated).

### 4.3 Recommendation
- **Default turning: arcs with r = 0.5 to 0.8** (R ≈ 0.6–1.8 m, 3–13° per 1000 outer steps). Why: both wheels drive (shared torque, no wheel at rest), caster swing ≤ 60°/40° and settles once, inner step rate stays ≥ 60–125 st/s (out of the 6–30 Hz band at either outer rate), smooth for a show.
- **Tight reorientation: pivot r = 0 only, never spin (r < 0) unless tests prove it works.** Pivot keeps both wheels' DIR unchanged (no gearbox backlash flip on one side, no change to the mirrored-DIR logic), the stopped wheel just holds. Spin needs one DIR flip (backlash impact), the largest caster swing (107°), and depends on the unverified STEP/DIR mapping.
- **Avoid 0 < r < 0.3**: inner wheel at 0–75 st/s falls through the low forbidden bands in full step, and it is neither a clean pivot nor a shared-load arc.
- **Profile:**
  1. Set DIR for both, then **ramp both wheels together with the ratio held constant** (same S-curve, ≥ 1 s, peak accel ≤ 1 m/s² per RESONANCE v3). Never ramp one wheel first.
  2. Outer peak ≤ 140 full st/s (≈ 2.5 cm/s) in full step, or keep 250 only with 1/16 microstep.
  3. **Long segments**: ≥ 6–8 cm outer travel (≥ 350–450 steps) per arc so the casters finish swinging and roll freely.
  4. **Full stop + 2–4 s random dwell before changing ratio sign, side, or direction.** Changing turn side flips both casters → scrub kick.
  5. Optional "caster pre-set": a short straight creep (≥ 3 cm) after any reversal before starting an arc, so the casters trail before they're asked to swing again.
  6. No driving during the 20 s Try Me dance (unchanged rule).

## 5. Implementation notes (prose)

- **One timer, two step trains (DDA/Bresenham).** Run a single loop at the outer (dominant) wheel's step rate. Each tick: step the outer wheel; add |r|·(denominator) to an integer accumulator for the inner wheel; when it overflows the denominator, step the inner wheel too and subtract. Express r as a fraction p/q (e.g. 3/4) so integer counters never drift: after any N outer steps the inner has exactly floor(N·p/q) steps. This is what Grbl does for multi-axis moves (Bresenham with fast integer counters and no DDA round-off; non-dominant axes get slightly uneven pulse spacing at low rates, which is fine here). ([Grbl stepper comments, PSI mirror](https://gitea.psi.ch/motion/ecmc_plugin_grbl/commit/7a85ab896d1640138f9612b6635299075e6f64d2))
- Ramp by changing the tick period only, not r: the S-curve applies to the shared tick → both wheels ramp together and the ratio is held automatically (§4.2 item 4).
- r = 0: just never pulse the inner STEP (driver still powered → holding torque). r < 0: flip that wheel's DIR **before** the ramp starts, never mid-move.
- **Timing source on the Pi.** main.cc uses `delayMicroseconds` in user space; fine for 250 st/s, but Linux scheduling adds jitter, worse on a single core or under load. ([AdvPiStepper requirements](https://advpistepper.readthedocs.io/en/latest/requirements.html)). For cleaner pulses: pigpio waveforms (DMA-timed GPIO edges, built from the same Bresenham schedule: each "pulse" = which GPIOs go high/low + delay) ([Pigpiox waveform docs](https://hexdocs.pm/pigpiox/Pigpiox.Waveform.html)); a Pi-based stepper controller using DMA/PWM reported up to 10 kHz with ~1 µs timing. ([ICALEPCS 2019](https://jacow.org/icalepcs2019/papers/WESH3002.pdf)). Both STEP pins in one waveform = one timebase = ratio exact. Note wiringPi on Pi 5 is still UNKNOWN (brain notes); pigpio does not support Pi 5 either (GUESS, check) → on a Pi 5 the simple `delayMicroseconds` loop with the DDA is the pragmatic path.
- **Fit to Tony's draft `move(direction, ms, lambda_after, trigger_id)`** — keep it, add **one optional trailing parameter `turn` (default 0 = straight)**:
  - `turn` is signed: sign = side (e.g. + = right, − = left), magnitude sets the ratio, **r = 1 − |turn|**. So turn 0 = straight, 0.25 → r 0.75, 0.5 → r 0.5, 1.0 → pivot (r = 0). Clamp |turn| ≤ 1 (no spins) for now; allow up to 2 (r = −1) later behind a flag if tests pass.
  - `ms` keeps its meaning: total move time for the outer wheel incl. ramps; the DDA makes both wheels start and stop together, so `lambda_after` fires once.
  - `direction` keeps fwd/back; reversing with a turn mirrors the arc (the cart backs along the same circle).
  - Why `turn` and not radius: a radius needs T (unknown until measured) and is infinite for straight; `turn` is dimensionless, 0 for every existing call, and the calibration table (§6) maps turn → measured degrees later. A radius/curvature helper can sit on top once T is known.

## 6. Calibration next week (bear OFF the cart first, then on)

1. **Mapping test**: pulse STEP1 only, then STEP2 only (bear off): which wheel turns, which DIR level = forward for each. Records left/right and confirms "DIR opposite = same direction". FACT needed before any turn code.
2. **Steps per wheel rev, each side**: chalk mark on the tyre, 1036 full steps (16 576 at 1/16 microstep), check exactly 1 rev → confirms 5.18:1.
3. **Wheel diameter each side**: roll 5 revs on the floor, tape the distance ÷ 5π; or tape around the tyre. A 1% L/R diameter difference = R ≈ 0.40/0.01 = **40 m drift curve** when "straight" (DERIVED). Trim with r slightly ≠ 1.
4. **Track width T**: tape centre-to-centre of the two tyre contact patches (or inside + outside edge ÷ 2). It scales every heading.
5. **Wheelbase L and caster trail e**: axle to caster swivel bolts; horizontal offset between swivel bolt and caster axle (e). Gives caster swing distances.
6. **Turn test** (each of r = 0.75, 0.5, 0 and later −1, each side, 2000 outer steps, slow ramp): tape a floor mark under the axle midpoint and a straight-edge along the cart side, measure heading change with a protractor/tape triangle, or with the **phone gyroscope** (phyphox-type app, integrate yaw) taped to the deck. Prefer gyro over compass: the steel dolly, motors and stepper magnets will bias a magnetometer (GUESS). Compare measured vs table → per-ratio correction factor ("effective T").
7. **Watch the casters** in each test: did they finish swinging, did the front skid sideways, did the outer wheel buzz/stall (lost steps)? Phone accelerometer on the deck for lateral kicks at turn start (compare with the 0.7–1.8 m/s² estimate).
8. Then repeat 6 with the bear on, 1/16 microstep if wired, and check frame/tie seating after each run.
