## 2026-10-13 01:24:44 — HARDWARE ERROR: bear trigger circuit short / not insulated
- Symptom: relay on BCM17 clicks every time, but the bear dances only sometimes. Same pulse gives different results (1.5 s worked at 01:10:49, failed at 01:13).
- Cause (found by Tony): the relay output → bear "Try Me" wiring is not insulated properly / shorts. It only works when the bare parts happen to touch the right way.
- Effect: all pulse-length results before the fix are UNRELIABLE. Run 1: 1 / 1.2 / 1.5 / 2 s failed, 3 s and 2×0.3 s danced. Run 2 (01:20–01:23): results not recorded.
- Fix in progress: Tony is insulating the wiring with electrical tape.
- Pi side verified OK: GPIO17 drives HIGH (level 1, ~3.3 V measured), relay VCC on the + rail fed from 5V0, SIG in the GPIO17 row, bear wires on COM + NO, bear power ON.
- After the fix: rerun ~/tony-tests/pulse_seq.sh (default sequence) to find the real minimum pulse.

## 2026-10-13 01:27–01:29 — post-tape rerun: relay clicks, NO dance at any width
| width | try 1 |
|---|---|
| 0.3 s | click, no dance |
| 1.5 s | click, no dance |
| 3.0 s | click, no dance |
- No width reached 3/3. After taping, the relay output no longer triggers the bear: the trigger circuit is likely open (a taped joint broken or insulated where it must touch) or not on COM + NO.
- Next: short the two bear wires together by hand (bear ON) to test the bear side; meter-check COM–NO continuity while the Pi holds pin 17 high.

## 2026-10-13 01:48 — SIG moved from GPIO17 to SDA1 (BCM2, physical pin 3)
- Observation (Tony): physically plugging SIG into SDA1, or into any pin/rail with voltage, makes the bear dance right away ("kickstart").
- Why: SDA1 has a permanent 1.8 kΩ pull-up to 3.3 V on the Pi board, so it idles HIGH. SIG on SDA1 = relay ON at rest. The plug-in moment = relay closes = bear triggers.
- Scripted GPIO17 pulses (0.3–3 s): relay clicks, no dance (post-tape runs). Hand plug-in to voltage: dance. Open question: steady close vs. pulse.
- Pi rebooted twice during pulse runs (01:17, 01:47; power bank shut off). Possible brownout or power-bank cutoff; watch power.
- Test on SDA1 is inverted: drive BCM2 LOW = relay OFF, release to input (pull-up) = relay ON (like a plug-in).
- RESULT 01:50–01:51 (SIG on SDA1): Tony reports "works!": the bear danced on the SDA tests (relay OFF 5 s → back ON and held ON).
- Takeaway: the bear triggers when the relay closes AND STAYS closed. Short closes (0.3–3 s on GPIO17, post-tape) did not trigger it. Untested with the bear ON and working wiring: a long hold (≥5–10 s) on GPIO17. The 10 s holds at 01:07 had the bear switched OFF.
- RESULT 01:52–01:53 (SIG on SDA1): relay OFF only 0.3 s → back ON and held: 3/3 DANCED ("all works").
- CONCLUSION: the trigger that works is "relay normally CLOSED (held), brief OPEN of 0.3 s, then CLOSED again". Short ON pulses from a normally-OPEN relay (0.3–3 s) did not work after taping.

## 2026-10-13 01:57–02:05 — full chain, wheels, reboots
- Full chain (camera + Gemini flash-lite + dance bridge via dance_sda.sh, no wheels, 120 s): 4 dances fired with pretext yells, 12 Gemini lines spoken, 21 hand events, no errors. Some Gemini lines were too dark for kids (McKay's prompt in scene.py).
- dance_launch.py now caps Gemini at GEMINI_MAX=5 calls per run, then answers "Quack quack!".
- Wheels: wheel_test 1 and 2, 700 steps fwd each, 5.0 s each, exit 0, pins idle afterwards.
- Pi rebooted a THIRD time (02:02, during the gremlin show). All 3 reboots happened while relay/wheels were in use → likely power-bank brownout/cutoff. Use a steadier 5 V/5 A supply.
- Boot is now silent (no voice cues) and starts `claude rc` when online.

## 2026-10-13 02:50–03:13 — WHEEL 1: driver latches off (overcurrent protection)
- Wiring confirmed by photos + tests: wheel 1 driver (DRV8825) STEP ← BCM13 (yellow), DIR ← BCM26 (blue), RST+SLP → 5V0, EN open. BCM numbering (wiringPiSetupGpio) is the right convention (physical/wiringPi candidates moved nothing).
- Pattern: right after a power cycle (Pi reboot or 12 V unplug/replug), ONE step burst moves the wheel (`step_pin 13 600 800`, at 03:10:03 and 03:13:07). After that, NOTHING moves: wheel_test at any speed, bursts with DIR high/low, even the identical burst at 03:11:45.
- Code ruled out: timing/ramp/pulse width analysis shows wheel_test and step_pin are both fine.
- Diagnosis: DRV8825 overcurrent protection (OCP) trips and stays latched until power is cycled. Likely causes: current limit (Vref) set too high, a motor-coil wire one row off / shorted, or wrong coil pairing.
- BCM13 also reads held LOW with the Pi's pull-up (strong pull-down on the STEP net); keep an eye on it.
- Fix: lower Vref to ~0.4–0.5 V, verify coil pairs (2–10 Ω within a pair, open between pairs) on A1/A2 and B1/B2, nothing one row off; then retest with two bursts in a row.
- 03:25 WHEEL 2 found: STEP = BCM16 (burst moved it, but wobbly), DIR = BCM21 (likely). Not BCM20. After test 1 the driver latched again (jolt + faint whine, then nothing) = overcurrent trip. Wobble suggests wheel 2's motor coils are mispaired on A1/A2/B1/B2. Built ~/tony-tests/wheel_real (STEP {13,16}, DIR {26,21}).
- Vref lowered to 0.4 V on both drivers: wheel 1 then moved on 2 bursts in a row (slight stall at the hard speed jump).
- 03:35 STOP TEST 1 (dance, then relay OFF after 2 s for 5 s): bear did NOT stop. Next: second press during song.
- 03:37 STOP TEST 2 (dance, second press after 2 s): bear did NOT stop (kept dancing). Next: long release then press (test 3), then triple tap (test 4); fallback = second relay that cuts bear power.
- 03:36 WHEEL 2 after teammate rescrewed + lowered Vref further + "coils fine": wheel_real 2 280 fwd → nothing; step burst BCM16 → nothing. Earlier (03:24:59, higher Vref) the same burst moved it (wobbly). Suspect Vref now too low, or a wire moved during rescrew.
- Bear stop tests dropped: per Tony it is just an automated Try Me button (no stop). Vref raised on both wheels ~03:38.

## 2026-10-13 03:39–03:55 — BOTH WHEELS WORKING, then 2 open issues
- 03:39 wheel 2 burst on BCM16 after Vref raise: moves, but "brr brr" (full-step, discrete). 03:40 10.9 s run OK.
- FIX that made both wheels move: teammate tuned the Vref screw WHILE the wheel was spinning.
- 03:42 sos_real (STEP {13,16}, DIR {26,21}): SOS on both wheels, 6.1 s, clean.
- 03:46 / 03:48 / 03:50: run_both 40 800 fwd → 40.0 s each, ~23,250 steps on both wheels, exit 0, no Pi reboot.
- OPEN (handoff ~/tony-tests/HANDOFF.md): (1) a wheel sometimes turns the WRONG way on the first command of a run (intermittent); (2) wheel 1 stopped working again after later tuning — suspect Vref (latch if too high, no torque if too low).
