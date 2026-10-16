# Manifest — Pi files rebuilt from session_017hJKaECmNA3qBC9xUQA9R3 (raspberrypi-keen-firefly)

Source: all 1,791 user/assistant events (33 pages, 2026-10-12 22:34 → 2026-10-13 03:02 UTC). Paths are relative to the Pi home `/home/spauly/` unless they are under `_*`.
Byte sizes of all 10 tony-tests files the Pi listed with `wc -c` at 02:59:50 match the rebuilt files exactly. Files the session sent verbatim to the "Bear project deadline" session also match the rebuilt files.

| path | status (why) | last event (UTC) |
|---|---|---|
| tony-tests/HANDOFF.md | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-13T02:58:58.263253Z |
| tony-tests/HARDWARE_LOG.md | FULL (Read snapshot 03:02:01 (6032 B) + final `cat >>` append at 03:02:08 (that command never returned a result: session ended; append very likely ran but unconfirmed)) | 2026-10-13T03:02:08Z |
| tony-tests/bear_loop.sh | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-13T01:07:38.042918Z |
| tony-tests/bear_voices.py | FULL (final `cat` on Pi at end of session) | 2026-10-13T03:00:38Z |
| tony-tests/boot.sh | FULL (final `cat` on Pi (matches last edit chain)) | 2026-10-13T03:01:33Z |
| tony-tests/creepy_fx.py | FULL (Read snapshot 01:28:30 + replayed 2 python patches (01:29:36, 01:30:11); size 26653 B matches Pi wc -c at 02:59:50) | 2026-10-13T01:30:11Z |
| tony-tests/creepy_show.py | FULL (final `cat` on Pi at end of session) | 2026-10-13T03:00:38Z |
| tony-tests/dance_launch.py | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-13T00:57:41.529754Z |
| tony-tests/dance_sda.sh | FULL (`cat` on Pi; never changed after 00:56 heredoc) | 2026-10-13T02:35:16Z |
| tony-tests/gremlin_show.py | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-13T01:04:15.601066Z |
| tony-tests/pin_hunt.sh | FULL (heredoc; identical to Read at 23:43) | 2026-10-12T23:12:26Z |
| tony-tests/pulse_seq.sh | FULL (`cat` on Pi after last sed edit (00:20)) | 2026-10-13T01:05:25Z |
| tony-tests/run_both.cc | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-13T02:45:15.147678Z |
| tony-tests/say.py | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-12T23:42:24.909812Z |
| tony-tests/sos_real.cc | FULL (final `cat` on Pi at end of session) | 2026-10-13T02:59:54Z |
| tony-tests/step_pin.cc | FULL (final `cat` on Pi at end of session) | 2026-10-13T02:59:54Z |
| tony-tests/test_creepy_fx.py | FULL (final `cat` on Pi at end of session) | 2026-10-13T03:00:38Z |
| tony-tests/wheel_pin_hunt.sh | FULL (final `cat` on Pi at end of session) | 2026-10-13T02:59:54Z |
| tony-tests/wheel_real.cc | FULL (final `cat` on Pi at end of session) | 2026-10-13T02:59:54Z |
| tony-tests/wheel_test19.cc | FULL (sed of ~/test2.cc; `cat` on Pi 02:09:47) | 2026-10-13T01:51:14Z |
| .claude/plans/do-some-sewuential-tests-abundant-fern.md | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-13T00:11:49.036222Z |
| .claude/projects/-home-spauly/memory/MEMORY.md | PARTIAL (3 index lines appended by echo >>; pre-existing content unknown (cat printed nothing → likely none)) | 2026-10-12T23:20:06Z |
| .claude/projects/-home-spauly/memory/bear-pi-boot-runner.md | PARTIAL (Write+Edits+sed/cat>>/echo>> replayed; Pi line count at 01:06 was 19 vs 16 rebuilt → ~3 unknown lines missing) | 2026-10-13T02:44:50Z |
| .claude/projects/-home-spauly/memory/bear-run-with-ui.md | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-12T22:57:45.978754Z |
| .claude/projects/-home-spauly/memory/bear-test-limits.md | FULL (Write tool input + Edit tool calls applied in order) | 2026-10-12T23:02:39.917734Z |
| _deleted_on_pi/tony-tests/wheel_map.cc | FULL (sed of ~/test2.cc (wrong map); `cat` 02:09:52; DELETED on Pi at 02:26:21 (rm -f wheel_map wheel_map.cc)) | 2026-10-13T02:05:11Z |
| _pi_tmp_scratchpad/tune.py | FULL (Pi /tmp scratchpad (subagent "Play cheerful random melody"): heredoc + 2 successful python patches replayed (01:42:40 patch was blocked, not run)) | 2026-10-13T01:43:03Z |
| _pi_tmp_scratchpad/wheel_debug.md | FULL (Pi /tmp scratchpad (subagent analysis): heredoc + append) | 2026-10-13T02:12:25Z |
| _reference_not_written/test2.cc | FULL (NOT written by session (pre-existing ~/test2.cc); `cat -n` 02:07:33; base of wheel_test19/wheel_map/wheel_real) | 2026-10-13T02:07:33Z |
| brain/_drift/2026-10-12T1950-alt-report-pi-wheels-fixed.md | FULL (heredoc; committed in brain repo 2a5ce81) | 2026-10-13T02:44:33Z |
| brain/_drift/2026-10-12T2000-alt-handoff-pi-wheels.md | FULL (HANDOFF.md + sed 1i frontmatter; committed in brain repo 0073672) | 2026-10-13T02:59:01Z |

## Not rebuildable / intentionally skipped
- Binaries built on the Pi: tony-tests/wheel_test (from ~/test2.cc), wheel_test19, wheel_real, sos_real (from ~/test3.cc; source sos_real.cc is saved), step_pin, run_both, relay17 (from ~/test.cc), wheel_map (deleted). Rebuild with `g++ -O2 X.cc -o X -lwiringPi`.
- Generated data: tony-tests/fx_cache/*.wav + manifest.json (run `creepy_fx.py render`), logs (boot.log, pulse_seq.log, wheel_pin_hunt.log, bear_loop.log, gremlin_show.log, claude-rc.log), flags (RUN_PIN_HUNT, NO_BEAR, .last_pulse), backup .boot.sh.bak.
- ~/test3.cc and ~/test.cc (pre-existing, not written; contents never fully printed). ~/test2.cc is saved under `_reference_not_written/` because it is the base of wheel_test19/wheel_real.
- Pi /tmp scratchpad throwaway probes (cam_proof.py, scene_proof*.py, models_check.py, t.py, new.py, image crops): one-off checks, not kept. tune.py and wheel_debug.md are saved.
- No secrets were found in any rebuilt file; nothing needed REDACTED.

## Branches touched
| repo | branch | last hash | push OK? |
|---|---|---|---|
| GitLab Forzalab-bravo/brain (`~/brain` on the Pi) | default branch, via `save.sh alt` | 0073672 (handoff); before it 2a5ce81 (wheels report) | Probably. save.sh printed "== SAVED" with exit 0 both times (the first try at 02:44:29 failed on BRAIN_DIR, and the retry worked). The push output itself was cut off by `tail`. |
| GitHub Forzalab/evil-autonomous-bear-proj (`~/tony-bear` clone) | ccr-0e989f41-17205e (PR #5) | The Pi only ran `git pull` and a `git push --dry-run`; it has no GitHub credentials | The Pi made no commits or pushes. Commits were made **by the cloud session "Bear project deadline" (session_01LAau6KduFZLkr8Y393qaoN) from files the Pi sent**: 95cc70f (boot.sh, pin_hunt.sh, say.py), dc632cc (HARDWARE_LOG.md), b4e0440 (boot.sh, pulse_seq.sh, dance_sda.sh, gremlin_show.py, dance_launch.py GEMINI_MAX patch, full HARDWARE_LOG to ~01:05), 9925391 (bear_loop.sh, boot.sh greeting patch), 833bf2b (bear_auto.cc wheel-2 STEP=16). The last batches "Pi files 1/4–3/4" (run_both.cc, wheel_real.cc, sos_real.cc, step_pin.cc, wheel_pin_hunt.sh, test_creepy_fx.py, bear_voices.py, creepy_show.py, latest boot.sh) were sent at 03:00–03:02, but the transcript ends before any commit confirmation. Batch 4/4 (HARDWARE_LOG wheel sections) was never sent. **creepy_fx.py was never sent**: it was skipped as too big (26,653 B), so this rebuild is likely its only copy. |
