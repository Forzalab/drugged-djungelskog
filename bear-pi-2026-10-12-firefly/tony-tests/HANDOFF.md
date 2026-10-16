# Bear Pi handoff — next session (written 2026-10-13 ~03:55 Pi clock)

Rule from the human at the bench: **ONE test, ONE change at a time.** Announce each test out loud
(`$PY ~/tony-tests/bear_voices.py say narrator "..."`). Keep messages short.
`PY=~/Desktop/barnaby/evil-autonomous-bear-proj/.venv/bin/python` (McKay's repo + venv = READ-ONLY).

## Open problems (focus)
1. **A wheel sometimes turns the WRONG direction on the first command** of a run (intermittent).
2. **Wheel 1 stopped working again** after the latest tuning. It ran 3 × 40 s cleanly at 03:46–03:50, then stopped.

## Known-good facts
- Pin map (BCM, `wiringPiSetupGpio`): **wheel 1 STEP=13 DIR=26**, **wheel 2 STEP=16 DIR=21** (NOT 20). Physical and wiringPi numbering were tested and ruled out.
- Drivers: DRV8825-style. EN open (enabled), M0–M2 open (full step), RST+SLP tied to 5V0. Motor power is 12 V (separate supply).
- Root cause of the earlier "no spin" was the **current-limit screw (Vref)**:
  - too high → overcurrent protection latches: ONE move after a 12 V power cycle, then dead until the next power cycle;
  - too low → no torque, no move or buzz only.
  - It worked after the teammate tuned it WHILE the wheel was spinning.
- Code is fine (a subagent compared test2.cc with step_pin.cc; timing, ramp and pulse width are OK). The slow `wheel_test` ramp (62–250 steps/s) stalls these motors. Use 800 µs half period.
- BCM13 reads LOW even with the Pi's pull-up (strong pull-down on wheel 1's STEP net), but it still drove the wheel. Keep in mind.
- Bear relay/dance: SIG on SDA1 (BCM2), `~/tony-tests/dance_sda.sh` → works. The bear can't be stopped mid-song.
- The Pi rebooted about 6× today under relay/wheel load (power bank). The Pi needs its own 5 V / 5 A supply.

## Commands (wheels in the air; Ctrl-C stops; pins go back to input)
```
cd ~/tony-tests
./run_both 5 800 fwd          # both wheels 5 s   (run_both.cc: 50-step soft start at 4×, then steady)
./wheel_real 1 700 fwd 800    # wheel 1 only ~5 s (test2.cc with real pins)
./wheel_real 2 700 fwd 800    # wheel 2 only
./step_pin 13 600 800         # raw burst, wheel 1 STEP only (DIR untouched)
./step_pin 16 600 800         # raw burst, wheel 2 STEP only
pinctrl get 13,16,21,26       # all should read "ip" when idle
```

## Next tests, in order (one change each)
### Wheel 1 not working
1. Switch 12 V off for 5 s, then on → `./step_pin 13 600 800` once.
   - Moves once, then dead on the next try → overcurrent latch again → Vref too HIGH, turn the screw slightly anticlockwise.
   - Never moves, maybe buzzes → Vref too LOW (or a wire moved). Measure Vref (screw→GND, 12 V on), aim ~0.5 V (wheel 2's working value is a good reference: measure it first).
2. If Vref is OK and still nothing → check the yellow STEP wire is in the GPIO13 row (right side, 4th pin) and on the driver's STEP pin, and the motor plug.

### Wrong direction on the first command
Likely causes, most probable first:
- **Missed steps at start-up → the rotor "snaps" backward**: at full step a weak or resonant start can jump a step backward before locking in. Test: `./run_both 5 1200 fwd` (slower) 3× vs `./run_both 5 800 fwd` 3×, note direction each time. If the slower runs never flip, raise the soft-start (more ramp steps) in run_both.cc.
- **Coil pairing / loose coil wire**: a mispaired or intermittently open coil makes direction random and motion wobbly. Meter: each pair 2–10 Ω, open between pairs; wiggle the plug during a run.
- **DIR line**: DIR is set ~1 ms before the first step (fine for the DRV8825). If the flip only happens on the FIRST run after the Pi boots, suspect DIR floating at power-on; test by running twice in a row.
- **Mirrored motors**: run_both/wheel_real set wheel 2's DIR = opposite of wheel 1 so both travel the same way. Make sure "wrong direction" means the same wheel flipping between runs, not wheel 2 always opposite (that would just mean flipping `(fwd ^ (i == 1))`).
- Optional smoother motion: M0/M1/M2 → 5 V = 1/32 microstep. Much smoother start, fewer missed steps. The code then needs 32× the pulses (use half period ~50–100 µs or scale the step counts).

## Files (~/tony-tests)
run_both(.cc), wheel_real(.cc), sos_real(.cc), step_pin(.cc), wheel_pin_hunt.sh, dance_sda.sh, dance_launch.py, bear_loop.sh (PAUSED: NO_BEAR flag set),
boot.sh (cron @reboot: speaker a2dp+max vol, greeting, wifi SC_GUEST by name, bear_loop unless NO_BEAR, claude rc with "y" to its trust prompt),
creepy_fx.py (+test, 24 SFX), bear_voices.py, creepy_show.py, gremlin_show.py, HARDWARE_LOG.md (full history), wheel_pin_hunt.log, pulse_seq.log.
Not yet committed to repo PR #5: wheel_real.cc, sos_real.cc, run_both.cc, step_pin.cc, wheel_pin_hunt.sh, creepy_fx.py(+test), bear_voices.py, creepy_show.py, latest boot.sh, HARDWARE_LOG.md wheel part.
