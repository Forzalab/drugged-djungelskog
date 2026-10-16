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

## Wheel test 2026-10-13 (subagent)
- 09:18:01–09:19:31, run from ~/tony-tests, about 3 s gap before each command. Full per-command log: ~/tony-tests/wheel_test_2026-10-13.log
- `uptime -s` stayed 2026-10-13 08:08:51 throughout, so no reboot. `get_throttled` was 0x0 before and after every command.
- 1a `step_pin 13 600 800 26 1`: exit 0, 600/600 pulses
- 1b `step_pin 13 600 800 26 1` (repeat, Vref latch check): exit 0, 600/600 pulses
- 2 `step_pin 16 600 800 21 1`: exit 0, 600/600 pulses
- 3a/3b/3c `run_both 5 800 fwd`: exit 0 ×3, 2759 / 2748 / 2760 steps in 5.0 s
- 4a/4b/4c `run_both 5 1200 fwd`: exit 0 ×3, 1833 / 1836 / 1833 steps in 5.0 s
- Software and power side were clean. NOT CONFIRMED VISUALLY: Tony still has to record which runs actually moved and in which direction (1a vs 1b for the latch; 3 vs 4 for the direction flip at start).

## 2026-10-13 09:39–09:45 — DANCE MOVED TO GPIO17 (locked) + live wheel run
- SIG is on GPIO17 (physical pin 11) since a rewire ~09:26 (Tony: keep it there). dance_sda.sh (pin 3) would no longer reach the relay.
- T1 09:39:50: GPIO17 driven HIGH and held → relay clicked, LED on, bear DANCED. So the relay is active-HIGH and the CLOSE edge triggers Try Me (matches the SDA1 plug-in "kickstart").
- T2 09:40:17 / :47 / 09:41:18: new ~/tony-tests/dance_gpio17.sh (relay held ON; OFF 0.3 s → ON) → 3/3 DANCED (Tony).
- bear_loop.sh now exports BEAR_DANCE_BIN=dance_gpio17.sh (backup: .bear_loop.sh.bak-sda). Loop restarted 09:42:11 with window.
- FULL CHAIN 09:43:04: hand → "[yell] Barnaby the bear is watching you." on SoundCore + bear DANCED (Tony). No bridge errors, throttled=0x0, no reboot since 08:08:51.
- Boot note: after a reboot GPIO17 idles LOW (relay open); the first hand just closes it (close edge = dance). SDA1 "dance at every boot" risk is gone.
- Wheels 09:44 (spoken labels A–E): A/B step_pin 13 ×2, C step_pin 16, D run_both 5 800 fwd → all exit 0, throttled 0x0, no reboot. Tony stopped E mid-run (reason not given); pins left idle. Visual result of A–D NOT reported.

## 2026-10-13 09:47–09:58 — WHEELS PARKED until after STEM day (decision: Tony)
- Rerun with wheels plugged in (09:47, A–E) and STEP hunts over BCM 13/16/21/26 (09:52) and 19/6/20/12 (09:57): every command exit 0, throttled 0x0, no reboot. NOTHING moved.
- Hand check: wheel 1 STIFF (driver powered + holding, so the step signal isn't reaching it); wheel 2 spins FREELY (driver not energized: OCP latch, or RST/SLP lost 5 V, or VMOT open).
- Photo 09:55: wheel 1 yellow (STEP) looked like it was on the GPIO19 row, not 13; pulsing 19 did nothing either → suspect the jumper isn't seated on the driver side or is a row off there.
- Latch can't be cleared in code: DRV8825 clears OCP only via RESET/SLEEP toggle or a VMOT power cycle, and RST+SLP are hard-wired to 5V0 (no GPIO). Nothing in the show code drives wheels (bear_loop/dance_launch/trigger: no wheel calls; boot.sh only with RUN_PIN_HUNT+RUN_WHEELS flags, both absent).
- DECISION (Tony, 09:58): skip wheels for STEM day; fix before Halloween. Suggest unplugging the drivers' 12 V for the show (wheel 1 draws holding current nonstop = heat + battery).
- After STEM, start here: (1) 12 V off 5 s → on; (2) meter VMOT on driver 2; RST/SLP of driver 2 at 5 V; (3) continuity Pi pin 33 (GPIO13) → driver 1 STEP; (4) re-run step_pin 13 / 16.

## 2026-10-13 10:11–10:14 — reboot + horror show live
- Pi rebooted ~10:11 (power again, throttled 0x0 after). boot.sh recovered everything by itself: speaker a2dp, bear_loop running with window, claude rc.
- ~/tony-tests/horror (horror.py): one-command 65 s show, bear_voices CLEAR voices, creepy_fx sounds, 2 dances via dance_gpio17.sh (25 s lockout respected), no wheels. LIVE run 10:12:49–10:13:54: all steps ran, dance #1 at +17 s and #2 at +42 s fired, cleanup left 17 HIGH, no reboot. Tony visual/audio feedback not reported.

## 2026-10-13 10:20–10:45 — FRANKIE replaces the old bridge (new spec from Tony)
- bear_loop.sh now runs ~/tony-tests/frankie.py (backup .bear_loop.sh.bak-1021). McKay's files untouched (runtime patch of barnaby.scene.PROMPT, app.on_perception / on_scene_description / describe_scene).
- Boot line "Frankie bear activated.", then passive detection. Gestures have priority: middle_finger → angry line + dance; peace → "sexy back" line + dance (song if ~/tony-tests/sexyback.wav|mp3 exists); open_palm → cut speech + 30 s quiet (dance can't be stopped: Try Me). Gemini flash-lite every 20 s: Jigsaw-style, very sarcastic, self-aware, college roast (PG-13, no body/race/gender/age/disability).
- Voice (frankie_voice.py): British en_GB-alan + Russian ru_RU-dmitri (in ~/tony-tests/voices). First chunk always angry (British on top, low Russian under), later chunks random angry/Russian/baby with random growls; final mechanical chain, +1 dB clip. Volume 150 % set by frankie.py at start (FRANKIE_VOL).
- Tested live with Tony: activated line, middle finger, open palm, peace, roast all OK (10:22). Dance via dance_gpio17.sh OK at 10:38:40.
- OpenRouter fallback (or_scene.py) being built by an agent; key in ~/tony-tests/.or_env (600, never printed).

## 2026-10-13 10:45–11:08 — Frankie show build (for the 12:00 STEM day)
- Files (all ~/tony-tests): frankie.py (main; run by bear_loop.sh), frankie_voice.py (angry voice: British Alan + low Russian Dmitri, light distortion), frankie_pipe.py (ON via touch PIPE_ON: 4 voting detection threads, AI queue with dedupe + ≤8 calls/min + Gemini/OpenRouter race, dance narration), detect_tuning.py (lower thresholds), or_scene.py (OpenRouter, key in .or_env 600), crowdwork.py (crowd-work prompt + lines), frankie_intro.wav (detuned jingle + 10-word lullaby), sexyback_10s.wav (peace sign song), prerender/ (cached lines).
- Behaviour: start = intro jingle → "Frankie bear activated." → Logan Guzman revenge line. middle finger = angry line + dance; peace = prerendered line + 10 s song + dance (other gestures ignored while it plays — that's why the song never played before 11:02); open palm = Star Wars/Force line + 30 s quiet; thumbs_up/fist = smug lines; roasts anchored on clothes/hairstyle/gesture, never race/body/gender/age/disability.
- Volume: 60 % until 11:45 (frankie.py + boot.sh), then 150 % on next Frankie start.
- Verified live with Tony: song played (11:04), dances, narration (OpenRouter 2.3 s), load ≤ 3.3, throttled 0x0.
- Rollback: rm ~/tony-tests/PIPE_ON (old single-thread path); backups .frankie.py.bak-* .frankie_pipe.py.bak-* .bear_loop.sh.bak-1021 (old dance_launch.py bridge).

## 2026-10-13 11:10–11:17 — Ultron scan, howl, sassy, growls, boot renewed
- frankie_pipe.py: idle Ultron scan every ~75 s (whole-scene object recognition → existential line, British slow slightly distorted voice, reverb wolf howl ~howl.wav in front). Expression + last-3-lines context in every AI prompt.
- crowdwork.py sassy diva-bear; frankie_voice.py random raspy growl ~1 in 3 lines (no sub-bass).
- boot.sh renewed (backup .boot.sh.bak-1116): no old Barnaby greeting; stale NO_BEAR cleared at boot (use NO_BEAR_BOOT to keep off); guardian re-starts bear_loop every 30 s. DRY run OK.
- Volume: background job raises to 150 % at 11:45.

## 2026-10-13 11:34–11:41 — reboot; guardian bug fixed
- Pi rebooted ~11:34 (power). Guardian never started bear_loop: its pgrep pattern matched its own command line. Frankie started by hand 11:40 (3 detection workers from the timing agent edit, compiles OK).
- Fix: boot.sh guardian check is now pgrep -f "^/bin/bash .*bear_loop[.]sh$" (only the real loop). Old guardian killed, fixed one running. Backup .boot.sh.bak-1138.
- Timing agent (3 s linger tuning) was stopped by the reboot; its frankie_pipe.py edits up to 11:25 are live (backup .frankie_pipe.py.bak-linger).
- Volume job re-created: 150 % at 11:45.
