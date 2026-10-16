# Relay pulse sequence test (bear "Try Me")

## Context
The relay chain works end-to-end: Pi GPIO17 → relay module (5V0 VCC, SIG in GPIO17 row) → bear Try Me. 300 ms and 700 ms pulses clicked the relay but the bear did not dance; a **1500 ms** pulse (01:10:49) made it dance. We now need a sequential test to find which pulse lengths and pulse patterns reliably trigger the dance, then commit the finding.

## Approach
Write one small script, `~/tony-tests/pulse_seq.sh`. It reuses the existing pieces and adds no new hardware code:
- `~/tony-bear/pi/dance [ms]`: one relay pulse on BCM17 only (HIGH then LOW, pin back to input). Already built.
- `~/tony-tests/say.py`: spoken cue through McKay's Piper voice. It waits for playback; McKay's files are only read.

Each test: big on-screen banner + spoken cue ("Test 3 of 10. One second.") → 1 s pause → pulse(s) → log line → **25 s gap** (Try Me lockout ~22 s). Relay only, no wheels, no camera, no Gemini.

Sequence, about 5 minutes total:
| # | Pattern | Purpose |
|---|---------|---------|
| 1 | 1 × 1500 ms | confirm today's working pulse |
| 2 | 1 × 1000 ms | find the minimum |
| 3 | 1 × 1200 ms | |
| 4 | 1 × 2000 ms | upper margin |
| 5 | 1 × 3000 ms | long hold |
| 6 | 2 × 300 ms, 300 ms apart (double tap) | does a short double tap work? |
| 7 | 3 × 500 ms, 500 ms apart | burst |
| 8 | 1 × 1500 ms | repeatability 1 |
| 9 | 1 × 1500 ms | repeatability 2 |
| 10 | 1 × 1500 ms, only 10 s after #9 | confirm the lockout (expect NO dance) |

The script takes an optional list of `count×ms` args to override the sequence, e.g. `pulse_seq.sh 1x1500 1x1000`. A Ctrl-C trap sets pin 17 back to input/pull-down and `exit 130`, the same way `pin_hunt.sh` does it. All output is logged with timestamps to `~/tony-tests/pulse_seq.log`.

## How it runs
- Run with the UI: launch it in an `lxterminal` window on the Pi screen so Tony can read the banners while watching the bear. Also run it in the background here with a `Monitor` on the log, so I can announce each test in chat.
- Tony notes which test numbers danced. The voice says each number before its pulse.

## After the run
1. Write a results table: test # → pattern → danced yes/no, from Tony's notes.
2. Set the working default: if 1500 ms is reliable, the default pulse should be ≥1500 ms everywhere (`pi/dance.cc` default 300 → winning value; `bear_auto --pulse-ms` default; `dance_launch.py`/bridge). Those are Tony's repo files, so I send the change request to the Bear project deadline session rather than editing them on the Pi.
3. "COMMIT TO GIT": send `pulse_seq.sh` verbatim, the results table and the wiring fix (SIG → GPIO17 row right half, VCC → + rail fed from 5V0, bear wires COM+NO, bear must be switched ON) to the Bear project deadline session. It commits and pushes to Forzalab/evil-autonomous-bear-proj on branch `ccr-0e989f41-17205e`, as it did for PR #5. The Pi has no GitHub credentials, so I don't push from here.

## Verification
- `bash -n ~/tony-tests/pulse_seq.sh` before running.
- Dry check: `DRY=1` mode prints and speaks the sequence without touching GPIO.
- During the live run: `pinctrl get 17` reads `ip pd | lo` after the run and after any Ctrl-C.
- Results confirmed by Tony per test number. Log tail is attached to the report.
