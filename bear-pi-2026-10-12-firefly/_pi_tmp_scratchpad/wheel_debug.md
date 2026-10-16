# wheel_test vs step_pin (read-only analysis, 2026-10-13)

Binary check: ~/tony-tests/wheel_test (00:10) disassembles with pins 13/26 and 20/21 → matches ~/test2.cc.

## Timing (computed)
- wheel_test 1 140 fwd: fast=2000, slow=8000, ramp=35. Half period 8000→2000→8000 us,
  i.e. 62.5 → 250 → 62.5 full steps/s. 140 steps = 0.7 rev (200 st/rev), 0.99 s total. Pulse high 2–8 ms.
- wheel_test 1 280 fwd: ramp 70, same speeds, 1.4 rev, 1.97 s.
- step_pin 13 600 800: 50 steps at 3200 us half (156 st/s, 0.32 s), then hard jump to 800 us (625 st/s) for 550 steps
  (0.88 s). 600 steps = 3 rev in 1.2 s.
- No integer-division weirdness: ramp>0 for steps>=4, d never < fast, never 0. Pulse widths are ms, vs DRV8825 1.9 us min.
  delayMicroseconds on Pi5 wiringPi 3.x: nanosleep for >=100 us, accurate enough. Not the cause.
- wheel_test is SLOWER and GENTLER than step_pin, so "stall at speed" does not explain it.

## Only real difference: BCM26 driven
step_pin (no dir args) never touches 26; after the pin hunt resets it is "ip pd" (≈ LOW).
wheel_test drives 26 HIGH for fwd, LOW for back.
A real DRV8825 DIR level cannot stop stepping. Observations: 280 fwd = nothing; fwd+back = ONE CCW motion
→ 26 HIGH kills motion, 26 LOW lets it move. Blue wire behaves like EN (active-high disable), not DIR
(off-by-one on the header/driver row, or photo misread). Also wheel_map.cc comment claims "STEP 26 -> 1st driver,
no DIR wires" — conflicting wiring belief; recheck.
"Quick jerk" = the whole back run: 0.7 rev in ~1 s.

## Decisive test
~/tony-tests/step_pin 13 1500 800 26 0   (~2.6 s, 7.5 rev; predicted: moves)
then same with 26 1                       (predicted: no motion / motor goes limp = EN)
Logged DIR TEST A/B (02:56:58 LOW, 02:57:09 HIGH) already did this — their visual results decide it.

## Checkpoints (confirm/kill #1)
- Confirmed if DIR TEST A (26 LOW) moved and B (26 HIGH) did not.
- Refuted if B moved, or if HARDWARE_LOG.md:32 "wheel_test 1 700 fwd" (~02:00, same binary, 26 HIGH) visibly turned the wheel.
## #2 fallback: low-speed full-step resonance
wheel_test crawls 62→150 sps at each end (~0.18 s) — typical NEMA17 full-step resonance band; can lose sync and
never catch 250 sps. step_pin jumps 156→625. Weaker fit (usually audible buzz, not silence).
Fallback no-hypothesis command: ~/tony-tests/step_pin 13 1700 800  (~3.0 s, 8.5 rev)
