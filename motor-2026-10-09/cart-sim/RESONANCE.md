# RESONANCE.md — earthquake-engineer pass on the Barnaby cart (agent A)

Numbers come from `modes_calc.py` → `modes.json` (re-run after editing masses.json or any ASSUMED value).
Masses: `masses.json` (agent B): whole cart 32 / 44.5 / 56 kg (low/mid/high), bear 9.07 kg, ball 1–6 kg.

Labels: **FACT** = measured or documented. **ASSUMED** = my engineering estimate, replace when measured.

## 0. Picture of the structure

```
                 head (~1 kg)            z = 2.6 m above floor
                 torso 4-5 kg  <- Try Me dance: "torso moves side-to-side on moving ball" (box text, FACT)
                 armature (steel tube, ASSUMED 16-25 mm)
   bear feet on ball top        z = 0.82 m
                 EPS ball 60-70 cm, 1-6 kg
   ball on deck                 z = 0.17 m   <- fixation UNKNOWN: resting / strapped / bolted
   plywood + carpet on steel dolly 30x18 in, 2 rear driven 6 cm wheels + front swivel casters
   carpet floor
```
Stack (bear + ball) CoM = **1.17 m above the deck** (mid), mass 12.1 kg, I about base edge 19.5 kg·m².
Whole cart CoM = 0.52 m above floor.

## 1. Excitations the drive injects (FACT for the code, ASSUMED where marked)

| # | source | frequency | strength | note |
|---|---|---|---|---|
| E1 | full-step pulse train (main.cc: 2 ms + 2 ms) | **250 Hz** + 500, 750 … | 1.8° rotor / 0.18 mm wheel per step | torque ripple through gearbox; buzz; set-screw loosening |
| E2 | stepper rotor mid-band resonance | 180 / 236 / 303 Hz | — | **250 steps/s sits inside the rotor's own resonance** → missed steps, chatter when wheel slips or backlash opens (explains "small wiggle" / stall as well as torque) |
| E3 | segment pattern 0.8 s on / 1 s off / 0.8 s reverse / 1 s off | fundamental **0.278 Hz**, harmonics every 0.278 Hz | each odd-ish harmonic up to 0.10 m/s² (impulse train → flat comb) | with NO ramp the comb is flat to >10 Hz; harmonics 3,5,7,11,13 (0.83–3.6 Hz) fall exactly in the bear sway band |
| E4 | start/stop jerk | pulse 4 ms commanded, ~20–40 ms real | commanded 11.4 m/s²; **real 0.6–0.8 m/s²** (torque-limited, 44.5 kg) | motor cannot deliver the commanded jerk; the stall/slip is what limits it |
| E5 | reversal backlash impacts (gearbox + clamp hub) | 2 per 3.6 s cycle (0.56 Hz) | broadband | hammering on set screws |
| E6 | planetary gear mesh (ASSUMED ~46 ring teeth) | ~11 Hz (8–14) at 0.241 rev/s output; planet pass ~0.7 Hz | small | lands in cart bounce band |
| E7 | carpet stick-slip of the tyres | 2–30 Hz broadband | load-share dependent | |
| E8 | **caster flip at reversal** (Tony) | each reversal | lateral scrub ≈ 39 N per caster; up to 1.8 m/s² lateral kick if 2 casters scrub | a trailing caster needs ≈ π·e/2 = 5–8 cm of travel to swing 180° (trail e = 3–5 cm ASSUMED); a segment moves 0.1–3.4 cm → **the flip never completes, casters sit sideways and scrub** |
| E9 | **longitudinal load transfer** (Tony) | with each jerk | ΔN = m·a·h/L = 24–32 N at a = 0.6–0.8 m/s² (L = 0.6 m ASSUMED) = ±14–18 % of the 175 N rear load | rear wheels gain load when pushing the cart rearward-first, lose it when braking a forward run → traction 119 N vs 91 N → asymmetric slip → net creep per cycle; at the stack tip accel (1.7 m/s²) ΔN = 65 N = 37 % |
| E10 | Try Me dance torso sway | 20 s cycle (FACT, measured); sway rate ASSUMED 0.4–1.5 Hz | moves 4–5 kg torso | sits inside the sway band by design (manufacturer designed it for a floor, not a 17 cm-high cart) |

Harmonic amplitudes of E3 (acceleration, worst phase): `a_n = (2Δv/T)·|1 − e^{−iω0.8} − e^{−iω1.8} + e^{−iω2.6}|`, Δv = 0.0455 m/s, T = 3.6 s.
With a linear ramp of duration τ the comb is multiplied by `|sinc(π f τ)|`: τ = 1 s cuts the 0.83 Hz harmonic 5×, the 1.9 Hz one 35×, 3 Hz one 55×.

## 2. Natural frequencies (first principles, low / mid / high in Hz)

| mode | low | mid | high | ζ | formula / assumptions |
|---|---|---|---|---|---|
| M1 bear sway (armature cantilever, inverted pendulum) | 0.7 | 2.0 | 4.7 | 3 % | `f = (1/2π)√(3EI/(m L³) − g/L)`; steel tube 16–25 mm OD, 1–1.2 mm wall, L 0.9–1.3 m, tip mass 4–6 kg → bare tube 2.6–6.3 Hz; ×0.75 for joint/bolt compliance; low floored at 0.7 Hz by the torso-pivot backlash. ASSUMED armature |
| M2 stack rocking on its fixation | 0.8 | 2.1 | 5.9 | 5 % | rigid bear+ball on fixation springs: `k_θ = 2 k r² − m g h_cm`, k = 5 kN/m (soft strap) … 150 kN/m (bolts/cradle), r = 0.25–0.30 m; `I = m_bear h² + m_ball·1.4R²`. **Resting ball: k_θ < 0 → no mode, statically unstable** |
| M3 EPS ball body flexure (if bear bolted through foam) | 3.9 | 5.2 | 6.5 | 5 % | sphere as short beam, E = 3–8 MPa, `k_θ = EI/L`, I at 60 % radius |
| M4 cart vertical bounce | 6.4 | 9.2 | 13.7 | 8 % | 6 contacts, caster PU + carpet/pad in series 15–40 kN/m each, m = 32–56 kg |
| M5 cart pitch/roll on casters (incl. load-transfer pitch) | 4.4 | 7.4 | 12.3 | 8 % | same springs, rotational; static pitch from ΔN = 1.6 mrad → 4 mm at the bear's head before amplification |
| M6 cart horizontal on tyre/carpet shear | 3.7 | 6.4 | 10.8 | 10 % | 5–25 kN/m per contact; stick-slip, nonlinear |
| M7 drivetrain, loaded (rotor + cart on the stepper's magnetic spring) | 13.5 | 17 | 22.6 | 3 % | `k_m = T_h·N_r = 0.19 N·m × 50 = 9.5 N·m/rad`, `J = J_rotor + (J_w + m r²/2)/(G² η)`; rings after every start/stop |
| M8 stepper rotor alone (mid-band) | 180 | 236 | 303 | 2 % | `f = (1/2π)√(k_m/J_rotor)`, J = 43 g·cm² (GUESS) — **250 steps/s is inside** |
| M9 arm cantilever | 2 | 5.5 | 10 | 6 % | 6 mm steel rod 0.5 m, 0.25 kg eff. ASSUMED |
| M10 head on neck | 3 | 5 | 8 | 6 % | 1 kg head, joint 0.4–2.5 kN/m ASSUMED |
| M11 torso on dance pivot (gear backlash) | 0.5 | 1.2 | 2.5 | 5 % | 4 kg at 0.4 m above pivot; rattles when unpowered ASSUMED |
| M12 caster swivel, kinematic trail mode | 0.14 | 0.18 | 0.24 | ~50 % | `f = V/(2π e)`, V = 0.0455 m/s, e = 3–5 cm; swivel friction makes it near-overdamped. **Caster flutter/shimmy needs V ≈ 0.5–2 m/s → not expected at 4.5 cm/s** |
| M13 caster swivel rattle (bearing/axle play) | 8 | 15 | 30 | 8 % | lateral tyre stiffness 10–40 kN/m, ~0.3 kg fork+wheel; excited at reversals and by E1 |

## 3. Overlap table (X = excitation band contains the mode band)

| | E3 comb 0.28–10 Hz (no ramp) | E4/E5 start impulses (broadband) | E6 mesh 8–14 Hz | E7 stick-slip 2–30 Hz | E1 250 Hz | E8 caster scrub (lateral, per reversal) | E10 dance 0.4–1.5 Hz |
|---|---|---|---|---|---|---|---|
| M1 sway 0.7–4.7 | **X** (harmonics 3–17) | X | | X | | **X** (lateral) | **X** |
| M2 stack rocking 0.8–5.9 | **X** | X | | X | | **X** | X |
| M11 torso pivot 0.5–2.5 | **X** | X | | | | X | **X** |
| M4/M5/M6 cart 3.7–13.7 | X (weak, n ≥ 13) | X | **X** | X | | X | |
| M7 drivetrain 13–23 | | **X** (rings every start) | | X | | | |
| M8 rotor 180–303 | | | | | **X** | | |
| M13 caster rattle 8–30 | | X | X | X | | X | |

## 4. Dynamic amplification

Steady-state resonant gain `Q = 1/(2ζ)` = 25 (2 %) … 10 (5 %), built up over ~Q cycles (10–25 cycles = 5–12 s at 2 Hz).
E3 harmonic at the sway mode: base accel 0.10 m/s² → relative accel at the bear CoM **1.0–2.5 m/s²**, relative displacement **0.6–1.6 cm at the CoM, ~1.5–3 cm at the head**.
Not catastrophic alone, but it is the SAME amplitude class as the tipping threshold below, and it is lateral/longitudinal sway on a 1.2 m-tall stack that the manufacturer designed for a static floor.
A 1 s ramp cuts those harmonics 5–55× → response falls below 0.5 mm. Randomising the dwell (2–4 s) destroys coherence → gain ≈ 1–3 instead of Q.

Cart pitch (M5, ζ 8 %, Q ≈ 6): static 4 mm at the head from ΔN, transient up to ~2 cm at the head if the pulse rise time is comparable to 1/(2·7 Hz) ≈ 70 ms — which is exactly the torque-limited start. A ramp ≥ 0.3 s removes it.

## 5. Tipping / rolling checks (rigid-body, quasi-static `a_tip = g·b/h`)

| body | h_cm | b (half base) | a_tip | vs realistic jerk 0.6–0.8 m/s² |
|---|---|---|---|---|
| stack, **ball resting** on deck | 1.17 m | ~0.02 m (EPS Hertz contact patch) | **0.17 m/s²** | FAILS by 4× — a free ball also rolls: a solid sphere on an accelerating plate lags by 5/7 of the plate travel → 2.5 cm per segment with a 9 kg inverted pendulum on top → topples |
| stack, strapped / in a ring, b = 0.20 m | 1.17 | 0.20 | **1.68 m/s²** | margin 2–2.8× only; commanded 11.4 m/s² would exceed it 7× if the motor could deliver it (it cannot — the stall is protecting the bear) |
| stack, bolted plate b = 0.30 m | 1.17 | 0.30 | 2.51 m/s² | margin 3–4× |
| whole cart, longitudinal | 0.52 | 0.38 | 7.2 m/s² | safe |
| whole cart, transverse | 0.52 | 0.23 | 4.3 m/s² | safe, but the caster lateral kick (1.8 m/s²) is 40 % of it with the stack's own rocking on top |

Single-pulse energy check (Housner): KE given to the stack by one 4.55 cm/s velocity jump = ½(m h Δv)²/I = 0.011 J, versus the potential hump to the tipping point `m g b²/(2h)` = 2.0 J (strapped), 0.02 J (resting). One pulse cannot overturn a strapped stack; it is marginal for a resting ball; **resonant accumulation (section 4) and caster kicks are what matter.**

## 6. Fatigue / loosening (ranked)

1. **Clamp-hub set screws on the gearbox D-shaft** — 250 Hz torque ripple + 2 backlash reversals per cycle (≈2000/h) + stall chatter. Classic failure in a day. Thread-locker (blue), flat/dimple on the shaft, check after 15 min of running.
2. **Motor mount bolts / driver board on breadboard** — same ripple; Wago levers are fine, breadboard jumpers are not (intermittent STEP = random chatter).
3. **Ball fixation (straps/zip ties)** — zip ties creep under 2 Hz cyclic load at ~50 N; EPS under a strap crushes locally → strap goes slack → b drops toward the resting case. Use a cradle ring or a plywood saddle, not ties.
4. **Bear armature bolts at the feet/ball interface** — low cycle count (~2000 reversals/h) but moment arm 1.45 m × 9 kg; inspect.
5. Caster swivel bolts — sideways scrub every reversal.

## 7. Forbidden bands and the recommended profile

Forbidden (Hz), also in modes.json:
- **0.5–6**: bear sway, torso pivot, stack rocking. No periodic start/stop whose fundamental OR low harmonics land here with un-ramped steps → effectively: never start/stop without a ramp, never repeat the same period.
- **6–15**: cart bounce/pitch + gear mesh. Pulse rise times of 30–80 ms excite it; ramp ≥ 0.3 s.
- **15–40**: loaded drivetrain mode; avoid full-step rates 15–40 steps/s and start-stop at that cadence.
- **150–330**: stepper mid-band; **the current 250 full steps/s is in it** — microstep (1/8 or 1/16: MS pins high) or move to < 100 or > 400 full steps/s.

Recommended motion profile (feeds agent C):
- Microstepping 1/16 (same speed = 4000 µsteps/s; ripple moves to 4 kHz, torque ripple ÷16).
- **S-curve ramp ≥ 1 s** up and down (acceleration ≤ 0.5 m/s², i.e. < 1/3 of the strapped tipping accel, and well below the caster scrub kick). Zero-start full-speed commands are forbidden.
- Peak accel budget: 0.5 m/s² (strapped), 0.8 m/s² (bolted), 0 (resting — fix the ball first).
- Dwell ≥ 2 s, **randomised 2–4 s**, never a fixed cadence; vary segment lengths too. Run at least 6–8 cm per segment so casters can complete the flip (or replace front swivel casters by rigid wheels/skids, which also removes E8 and M12/13).
- Do not drive during the 20 s Try Me dance (E10 already sits in the sway band; stacking lateral kicks on top is the worst case). Trigger the dance only when the cart has been still ≥ 2 s.
- Prefer direction changes with a full stop + dwell, never a hard reverse.

## 8. What to measure on the real bear (cheapest first)

1. **Push-and-release + phone accelerometer** (Phyphox / Physics Toolbox, 100 Hz sampling): tape the phone to the bear's chest, push the head 2 cm sideways and release; read the frequency from the FFT or count zero crossings in 5 s. Gives M1/M2 and the damping from the decay (ζ = ln(x_n/x_{n+1})/(2π)). Repeat phone on the deck for M4/M5 (tap the deck). 5 minutes, pins the two most important numbers.
2. **Is the ball fixed?** Push the ball sideways at the deck with ~50 N: does it roll/slide? If yes → resting case → stop until fixed. Measure the actual base half-width b (strap ring / saddle / bolt pattern).
3. **Bathroom scale under each rear wheel** → rear load fraction (slip, load transfer); plus total mass.
4. Phone on the deck while main.cc runs: spectrum shows 250 Hz buzz, the ~17 Hz ring after each start, whether the sway band gets energy (compare ramp vs no ramp).
5. Count caster flips: run 3 cycles and watch whether the front casters complete their swing or sit sideways.
6. Vref and chip marking on the drivers (sets T_h, k_m, hence M7/M8).

## 9. Risk ranking

1. Ball not positively fixed to the cart (UNKNOWN) → any drive topples the stack (a_tip 0.17 m/s²). Verify before anything else.
2. Un-ramped periodic start/stop (every 3.6 s) → flat harmonic comb through the 0.7–5 Hz sway/rocking band; Q = 10–25 → 1–2.5 m/s² at the bear CoM, same order as the strapped tipping accel (1.7 m/s²).
3. Caster scrub at reversals (segments too short for the 180° flip) → 1–2 m/s² lateral kicks on a 1.2 m-high stack + traction loss; plus ±15–18 % rear-load transfer making forward/reverse slip asymmetric (cart creeps).
4. 250 full steps/s inside the stepper mid-band (180–300 Hz) → chatter/missed steps → broadband shaking, hub set screws loosen.
5. Try Me dance (sway band by design) concurrent with cart motion.

---

# v2 (photo-based) — 2026-10-09 bear-mount photos change the load path

Inputs: `PHOTOS.md` (observations, scale check, questions), `masses.json` v2, `modes_calc.py` v2 -> `modes.json`; `cart_sim.py` re-run -> `run_v2_photo.log`.
v1 files kept as `modes_v1.json`, `masses_v1.json`, `RESONANCE_v1.md`.

## What changed (SEEN / INFERRED)

- **Geometry** (scale check with the sugar box + 3 in Post-its, PHOTOS.md §1): ball **0.47 +- 0.05 m** (was 0.65), bear **1.20 +- 0.10 m** feet-to-head (was 1.78; the listing's 70 in includes the stand), stack top ~1.84 m above floor (was 2.6), stack CoM **0.80 m above deck** (was 1.17).
- **Load path** (INFERRED from SEEN slot + post + sketch): bear (hollow frame, ~6 kg) hangs on a **~22 mm square steel post** (its original telescoping stand pole, wing-nut lock at the ball top) that runs down **through** the ball. The ball is a **hollow shell**, two halves screwed at a seam, threaded onto the post through a **slot** (post + 1-4 mm across, ~10 cm free along). Velcro at the feet (SEEN) and at the ball bottom (sketch). The post bottom's fixity is **UNKNOWN** ("gap" in the sketch) -> three cases below.
- **Masses**: ball 1.5 kg shell (was 3 kg solid EPS); bear split into body 6 / post 1.5 / base plate 0-2.5 kg. Whole cart 43 kg mid (was 44.5), CoM 0.37-0.46 m.
- **New nonlinear risk**: post rattling in the slot (gap closure -> impact on a thin shell wall), 6-25 Hz, excited by every start/stop; the hollow shell drums at the 250 Hz step buzz and its seam screws are a fatigue point.

## Modes (Hz, low / mid / high)

| mode | v1 | v2 |
|---|---|---|
| bear sway, post bottom FIXED | 0.7 / 2.0 / 4.7 (armature guess) | **3.3 / 3.5 / 4.3** (22 mm tube, EI 1.4 kN m2, x0.5-1 joint) |
| bear sway, post bottom PINNED with gap | - | **1.0 / 1.5 / 2.1**, zero stiffness inside the gap, then impact |
| stack rocking, VELCRO only | 0.8 / 2.1 / 5.9 (strapped/bolted) | **<0.3 (unstable) / 0.6 / 1.2** — the soft-velcro case has k_th < 0: only velcro peel holds it |
| post in slot rattle (impact) | - | 6 / 10 / 25 |
| shell ovalling / seam | - | 15 / 30 / 60 (ASSUMED wall) |
| arms (hollow, light) | 2 / 5.5 / 10 | 1.5 / 3.5 / 7 |
| cart / drivetrain / rotor | unchanged within 5 % | 6.5-14 / 14-24 / 180-303 |

Resonant build-up at the sway mode from the un-ramped 3.6 s comb (0.10 m/s2 per harmonic, Q 10-17): 1.0-1.7 m/s2 relative at the bear CoM in every case; displacement 0.2-0.3 cm (fixed), 1-2 cm (pinned), **7-11 cm (velcro only, i.e. it walks the velcro off)**.

## Tip thresholds and margins per fixity case (mid mass 43 kg; cart_sim margins scale with a_tip)

| post-bottom case | a_tip m/s2 (v1 equivalent) | governing | margin a: main.cc | b: 0.3 s ramp | c: 125 st/s | lateral (b) |
|---|---|---|---|---|---|---|
| **fixed** (bolted to deck / base plate screwed down) | **5.3** (v1 bolted 2.5) | whole-cart transverse tip; post yields only at 24 m/s2 | 6.1 | **2.8** | 11.8 | 4.2 |
| **pinned with gap** (captive, rotates through play, shell + velcro take the moment after impact) | **1.07** (v1 strapped 1.68) | velcro/cradle tip 2.15 / impact factor 2; shell wall crush at the slot | 1.24 | **0.57 TIPS** | 2.4 | 0.85 TIPS |
| **velcro only** (post in nothing; stack held by bottom velcro on a 0.12 m-radius cradle contact) | **1.48** (v1 resting 0.17) | rigid stack about the cradle edge, no peel credit (velcro fatigues in peel at 0.5 Hz reversals) | 1.71 | **0.79 TIPS** | 3.3 | 1.17 |

(cart_sim run used the velcro-only values; the other rows are the same run scaled by a_tip. Low-mass cart: profile b margin 0.78-1.1 lateral even in the velcro case.)
Read: the shorter, lighter stack is **easier** to keep upright than v1 thought (velcro-only 1.5 vs resting 0.17), but the realistic structure is a 9 kg inverted pendulum on a **single 22 mm telescoping tube with an unknown foot**, and the ramped profile that actually moves the cart still tips the pinned/velcro cases. Single pulse cannot overturn it (0.008 J vs 0.8 J); resonance and caster kicks can.

## Forbidden bands (Hz) — v2

- **0.3-6**: bear-on-post sway (all fixities), velcro rocking, torso pivot, arms. Un-ramped periodic start/stop forbidden; ramp >= 1 s; dwell random 2-4 s.
- **6-30**: post-in-slot impact, cart bounce/pitch, gear mesh, drivetrain ring. Pulse rise times < 80 ms (every instant start) hammer the slot edge; ramp >= 0.3 s.
- **150-330**: stepper mid-band, 250 full steps/s is inside; it also drums the shell. Microstep 1/16.

## Top risks v2 (ranked)

1. **Post bottom fixity unknown.** If it is "gap"/velcro, the bear is a free-standing inverted pendulum on velcro peel: ramped driving tips it (margin 0.6-0.8) and resonance walks the velcro off. **Fix: screw the pole's base plate (or a new one) to the deck -> fixed case, margin 2.8+.** This is the single highest-value build action.
2. **Slot clearance / wing-nut play** -> impact loads on a hollow shell wall at every start/stop; shell cracks at the slot, seam screws loosen, post chatters at 6-25 Hz. Shim the slot (hardwood/foam blocks each side), re-tighten the wing nut with a lock washer, or better: make the post the only load path (risk 1) and give the slot 5 mm clearance all round so the shell never touches it.
3. **Velcro in peel** at the feet and ball bottom under 2 reversals per cycle -> creeps off within tens of cycles; only shear-loaded velcro is reliable.
4. Un-ramped 3.6 s cadence through the 0.3-6 Hz band (unchanged from v1); 1.0-1.7 m/s2 at the bear CoM after 10-17 cycles.
5. Caster scrub lateral kick (0.7 m/s2 with the ramp) = 65 % of the pinned-case lateral tip threshold.
6. 250 full steps/s in the rotor mid-band; shell drumming; hub set screws (unchanged).

Recommended profile unchanged (1/16 microstep, S-curve ramp >= 1 s, accel <= 0.35 m/s2 = 1/3 of the worst case, random 2-4 s dwell, no driving during the dance) — **but do not run the cart with the bear on until question 1 in PHOTOS.md §7 is answered and the post bottom is screwed down.**

---

# v3 — frame zip-tied to the deck (Tony's answers, 17:2x PT)

Files: `masses.json`, `modes.json` (v3), `modes_calc.py` (v3), `run_v3.log` (cart_sim re-run). Backups of the previous pass: `*_v2photo.*`. Answers in `PHOTOS.md` §8.

## Structure as now understood

Bear (hollow frame, 6 kg) on its own ~22 mm steel post, which is welded into the animatronic's tubular steel **stand frame** (~3.5 kg, base ~0.45 x 0.6 m). The frame sits **on top of the wooden deck with ~1 mm gap, held only by 3-4 zip ties (4.8 mm, 50 lb / 222 N class)**. The hollow plastic ball (1.5 kg) is threaded on the post through the slot and velcro'd to the feet. The Try Me dance moves the fur shell (and the ball with it) **on the fixed post** -> internal excitation + slot hammering.
Stack above deck (bear + post + shell + frame base) 11 kg, CoM 0.66 m; whole cart 43.5 kg, CoM 0.37 m above floor.

## Tip check: frame rocking about its rail vs zip ties (mid mass)

| | transverse (b = 0.22 m) | longitudinal (b = 0.30 m) |
|---|---|---|
| lift-off / rocking onset a = g b / h_cm | **3.3 m/s2** | 4.5 m/s2 |
| tie force per tie at the real jerk (0.9 m/s2) | 0 N (no lift-off) | 0 |
| tie force per tie at resonant 1.7 m/s2 | 0 N | 0 |
| tie force per tie at the whole-cart tip accel (5.3 m/s2) | 17 N (2 ties per rail) | 5 N |
| accel to BREAK the ties (222 N each) | 30 m/s2 | 41 m/s2 |
| low-mass case (1 tie per rail) | lift-off 3.5, break 22 m/s2 | |

**Zip ties are not the strength weak link** (< 10 % of rating at anything the drive can do; the whole cart tips first at 5.3 m/s2). The weak links are (i) **slack / preload loss / creep**: nylon ties around a round tube on wood lose tension within days and under the 250 Hz buzz, after which the frame rocks freely through the 1 mm gap and **hammers the deck** at every start/stop (impact, loosening, noise), and (ii) the 1 mm gap itself. Lift-off at 3.3 m/s2 is now the "tip" number used by cart_sim (rocking onset, not toppling).

Dance (internal): 3 kg at 0.75 Hz, +-5 cm -> 3.3 N at the shoulders, 4 N m on the frame vs 24 N m gravity restoring -> no lift-off from the dance alone (even the 1.5 Hz / 8 cm extreme gives 34 N m, just above lift-off); but it drives the post against the slot edges twice per sway (1-3 Hz impacts) and sits in the sway band.

## Modes v3 (Hz, low / mid / high)

| mode | v2 | v3 |
|---|---|---|
| bear on post+frame sway, zip-tied (PRIMARY) | fixed 3.3 / 3.5 / 4.3 | **1.8 / 2.8 / 3.6** (frame flex x0.4-0.8 in series with tie rocking); zero stiffness inside the 1 mm gap |
| frame rocking on ties (rigid stack) | - | 2.3 / 6.5 / 11 (k_tie 5-100 kN/m; slack ties -> 0 = free rocking) |
| shell dance slip on post (excitation, not a mode) | - | 0.4 / 0.75 / 1.5 |
| post in slot rattle / shell ovalling / cart / drivetrain / rotor | unchanged | 6-25 / 15-60 / 6-14 / 13-23 / 180-303 |

## Tip (lift-off) margins, cart_sim run_v3.log (a_tip 3.28 m/s2; v2 velcro-case values in brackets)

| profile | mid mass fore-aft | mid lateral | low mass fore-aft / lateral | worst mode (mid) |
|---|---|---|---|---|
| a main.cc 250/s instant (stalls, 0.0/0.08 cm) | **3.8** (1.7) | >100 | 1.8 / >100 | shell ovalling @60 Hz, 9.0 m/s2; rotor mid-band 180 Hz |
| b 0.3 s ramp (moves 0.5/3.5 cm) | **1.8** (0.8) | 5.3 | 3.0 / **1.35** | rotor mid-band @236 Hz, 8.3 m/s2 |
| c 125/s instant | **7.4** (3.3) | >100 | 1.9 / 2.4 | shell ovalling @30 Hz, 5.5 m/s2 |

Every profile still puts energy in the forbidden bands (0.3-6: reversal harmonics; 6-30: swivel pulse, slot rattle, drivetrain ring; 150-330: rotor). Profile b remains the only one that moves the cart and is now at margin 1.8 against **lift-off** (not toppling): the frame will start rocking on its ties at roughly half the ramp acceleration that cart_sim b uses, i.e. ramp >= 0.6-1 s keeps it seated.

## Top 3 fixes, ranked by cost

1. **Free (code):** S-curve ramp >= 1 s (accel <= 1.0 m/s2 = 1/3 of lift-off), 1/16 microstep, random 2-4 s dwell, full stop before reversing, no driving during the dance. Keeps the frame seated and off the slot edges.
2. **~$5, 20 min:** re-tension or replace the ties with 7.6 mm / 120 lb ties pulled with a tie gun, 2 per rail + 1 per crossbar end (6 total), with a rubber/EVA strip under the rails to kill the 1 mm gap and give the ties preload that survives creep; thread-lock the wheel hub set screws at the same time. Hollow-shell: shim the slot with foam blocks each side of the post so the dance and starts do not hammer the shell.
3. **~$15, 1 h:** replace the ties with 4 pipe clamps / U-bolts (or saddle clamps) screwed through the plywood deck -> true fixed case (margin 2.8-6 against whole-cart tip, no gap, no creep); then the remaining risks are the stepper mid-band (microstep) and the shell/seam screws.

## v3.1 — the Try Me "lean" as a 3-link zig-zag around the fixed post (Tony's sketch abf31c19)

Segment angles measured from the sketch (displayed 956 x 2000 px; "going up" convention, + = to the right):
| segment (colour) | px bottom -> top | angle from vertical | note |
|---|---|---|---|
| post (white) | (520,1700) -> (440,210) | 3 deg | stationary, "slight wiggle" |
| ball (red) | (490,1410) -> (415,1225) | **-22 deg** | ball top swings left of the post |
| legs (yellow) | (405,1240) -> (615,870) | **+30 deg** | hip swings right (drawn twice = the zig) |
| torso + head (cyan) | (605,850) -> (303,340) | **-31 deg** | head/shoulders swing left |
Alternating signs; the chain crosses the post twice (y ~ 1150 and ~ 570 px) = **two nodes**: this is the highest mode of a 3-hinge chain, i.e. the shape of a beam's **3rd bending mode**, not a rigid 1st-mode lean. (Hinges: ball bottom on velcro/cradle, feet/ball-top via the feet velcro and the slot, hip = the dance mechanism.) The ~10 cm free length of the slot is probably exactly the ball-top travel the dance needs, so the slot direction = the sway direction.

Chain model (links 0.47 / 0.50 / 0.70 m, masses 1.5 / 1.0 / 4.5 kg, numbers in modes.json `fixity_cases.frame_ziptied_gap.dance_zigzag_chain`):
| | sketch angles (-22/+30/-31) | plausible, top travel 8 cm (-6/+8/-9) |
|---|---|---|
| head/top displacement | 0.29 m | 0.08 m |
| CoM horizontal shift, zig-zag | **0.071 m** | 0.020 m |
| CoM shift of a rigid lean with the same top displacement | 0.187 m (11 deg) | 0.048 m (2.9 deg) |
| cancellation by counter-rotation | **62 %** | 58 % |
| base shear / moment on post->frame at 0.4 Hz | 3 N / 7.6 N m | 1 N / 2.2 N m |
| at 0.75 Hz (likely) | 11 N / 14 N m | 3 N / 4.3 N m |
| at 1.5 Hz (extreme) | 44 N / **43 N m -> lift-off** (vs 24 N m), 22 N per tie (10 % of rating) | 12 N / 13 N m, no lift-off |
| cart acceleration from the dance | 0.07-0.25 m/s2 (1.0 at 1.5 Hz) | 0.02-0.07 m/s2 |

Reading: the zig-zag is a self-balancing motion — the counter-rotating links cancel ~60 % of the CoM shift, so the dance puts only 2-14 N m into the post/frame/ties at realistic rate and amplitude, well under the 24 N m lift-off moment and < 10 % of a zip tie's rating even in the extreme case. What it does load is the **hinges and the slot**: the hip mechanism carries the torso inertia, the ball top drags 5-18 cm along the slot every sway, and the ball bottom rocks on its velcro (ball angle 6-22 deg). The 0.4-1.5 Hz dance sits inside the primary sway band (1.8-3.6 Hz zip-tied; 1.0-2.1 Hz if ties are slack), so the harmonics (2x, 3x) can still pump the frame rocking — one more reason not to drive the cart during the dance. Zip-tie check unchanged: ties are not the weak link; slack + 1 mm gap are.
