# URGENT: Frankie not running after the 11:34 reboot (show 12:00)

## Context
The Pi rebooted at about 11:34, probably power again; `throttled=0x0` now. `boot.sh` started the new guardian, but the guardian never started `bear_loop.sh`.

The cause is that its check, `pgrep -f 'tony-tests/[b]ear_loop.sh'`, matches the guardian's **own** command line. That command line contains the literal path `/home/spauly/tony-tests/bear_loop.sh` in its `setsid nohup` line, so the guardian always thinks the bear is already running. The result: no camera, no Frankie.

Two things were also lost in the reboot:
- the 11:45 volume job;
- the timing agent, which last edited `frankie_pipe.py` at 11:25 and needs a compile check.

## Steps (in order, fast)
1. Check that `frankie.py`, `frankie_pipe.py`, `frankie_voice.py` and `frankie_fast.py` all pass `python3 -m py_compile`.
   - If `frankie_pipe.py` fails, restore `.frankie_pipe.py.bak-linger`, the timing agent's backup from before its edits.
2. **Start Frankie now:** `cd ~/tony-tests && setsid nohup ./bear_loop.sh >/dev/null 2>&1 < /dev/null &`.
   - Confirm `frankie.py` is running and `bear_loop.log` shows the start line, the intro and `gemini call`/`[ai]`.
3. **Fix the guardian in `boot.sh`** for the next reboot (backup `.boot.sh.bak-1138`, write new file, `mv`, `bash -n`).
   - Change the check to `pgrep -f '^/bin/bash .*bear_loop\.sh$'`. That matches only the real loop process (`/bin/bash /home/spauly/tony-tests/bear_loop.sh` or `/bin/bash ./bear_loop.sh`), never the `bash -c while…` guardian.
   - Then kill the broken running guardian (pid 1579, by PID) and start a fixed one the same way `boot.sh` does, so a crash of `bear_loop` before the next reboot is also covered.
   - Verify with `DRY=1`, and check that `pgrep` against the live processes returns only the real loop.
4. **Re-create the 11:45 volume raise** as a background job (`until 11:45; wpctl set-volume @DEFAULT_AUDIO_SINK@ 1.5`).
5. Leave the timing agent stopped; there's no time before the show. Note it in HARDWARE_LOG and tell Tony.
6. Append the reboot and the guardian fix to `HARDWARE_LOG.md`.

## Verification
- `ps` shows exactly one `bear_loop.sh` and one `frankie.py`.
- The log shows the intro, then "activated", then `[ai]` lines; no Traceback.
- The volume reads 0.6 now and 1.5 after 11:45.
- Tony confirms by hand: a peace sign plays the song, a middle finger gets a dance.
