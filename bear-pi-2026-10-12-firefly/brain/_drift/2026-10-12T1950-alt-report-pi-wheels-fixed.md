---
name: drift-pi-wheels-fixed
description: cocaine-bear Pi #1 — both wheels working (Vref), real wheel pin map, SOS OK; bear stop impossible
type: report
project: cocaine-bear
ts: 2026-10-12T19:50-07:00 (Pi clock 2026-10-13 03:43)
from: alt — Pi session raspberrypi-keen-firefly
---
- 🎉 BOTH WHEELS MOVE. SOS on both wheels ran clean (Pi 03:42, 6.1 s) with ~/tony-tests/sos_real.
- REAL WHEEL PIN MAP (BCM, wiringPiSetupGpio — physical/wiringPi numbering ruled out by test): wheel 1 STEP=BCM13 DIR=BCM26; wheel 2 STEP=BCM16 DIR=BCM21 (NOT 20 as in test2.cc/Tay's main.cc). Binaries: ~/tony-tests/wheel_real (test2.cc w/ STEP {13,16}), sos_real (test3.cc same map).
- ROOT CAUSE of "no spin": DRV8825 current-limit screw (Vref). Too high → overcurrent protection latches (one move after each 12 V/Pi power cycle, then dead until power cycle). Too low (after first fix) → no torque. Teammate tuned the screw WHILE the wheel spun → both move. Wheel 2 still "brr brr" (full step, M0–M2 open); smoother = tie M0–M2 to 5 V (1/32 step, code needs 32× pulses) — not done.
- Code ruled out: subagent compared test2.cc vs step_pin.cc — timing/ramp/pulse width fine.
- BCM13 reads LOW even with the Pi pull-up (strong pull-down on wheel 1's STEP net) yet works — watch it.
- Bear: relay/dance still fine (SDA1 + dance_sda.sh, Pi 03:33). Stop-mid-song tests (release after 2 s, second press) FAILED — it's an automated Try Me button, no stop. Only real stop = second relay cutting bear power (not built).
- Also today on Pi: 24 creepy SFX in ~/tony-tests/creepy_fx.py (+tests 14/14), bear_voices.py (narrator/witch/ghost/zombie/robot/chipmunk/gremlin/kawaii, clarity EQ, glitch speech, Clovis meta lines, Gen Alpha brainrot, Preamble), creepy_show.py; boot.sh: greeting "Hi Logan! Hiiii, Yooooo-saf!", bear_loop.sh forever (currently PAUSED via ~/tony-tests/NO_BEAR), claude rc auto-answers trust prompt (y after 10 s).
- RISK: Pi rebooted ~6× today under relay/wheel load → power-bank brownout; give the Pi its own 5 V/5 A supply.
- Not yet committed to repo PR #5: wheel_real.cc, sos_real.cc, step_pin.cc, wheel_pin_hunt.sh, creepy_fx.py(+test), bear_voices.py, creepy_show.py, latest boot.sh (claude rc y-answer), HARDWARE_LOG.md wheel sections.
- Details: ~/tony-tests/HARDWARE_LOG.md on the Pi.
