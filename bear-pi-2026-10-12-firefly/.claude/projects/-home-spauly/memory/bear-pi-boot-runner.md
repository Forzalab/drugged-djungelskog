# PARTIAL — rebuilt from transcript fragments; missing: ~3 unknown lines (Pi `grep -c` reported 19 lines at 01:06:47, the replayed Write+edits give 16 there; something not visible in the transcript also wrote to this file)
---
name: bear-pi-boot-runner
description: Bear Pi boot runner (cron @reboot → ~/tony-tests/boot.sh): silent, starts claude rc when online; campus wifi SC_GUEST; BT speaker; working dance trigger on SDA1
metadata:
  type: project
---

Installed 2026-10-13: `@reboot /bin/bash /home/spauly/tony-tests/boot.sh` in spauly's crontab. Plain bash. Since 2026-10-13 02:08: one spoken greeting only ("Hi Logan! Hiiii, Yooooo-saf!"), starts ~/tony-tests/bear_loop.sh (bear detection forever, restarts on crash; stop with `touch ~/tony-tests/NO_BEAR` + `pkill -f tony-tests/dance_launch.py`), and starts `claude rc` when online via `nohup setsid script -qfc "claude rc"` (no tmux on the Pi). Logs to ~/tony-tests/boot.log; `DRY=1` = no GPIO.
- Speaker is the Bluetooth SoundCore 2 (E8:09:59:20:51:92); only wired audio is HDMI, so Bluetooth connects before any spoken cue. It can come up in headset mode (HFP, silent/quiet): boot.sh forces a2dp-sink and sets max volume (user wants max volume on connect). The Pi has no screen at the bear; boot status goes only to boot.log now (boot is silent).
- Campus wifi: SC_GUEST is open (free) on 10+ access points. Match by NAME, never by router; "free + internet" = generate_204 returns 204.
- One-shot flags: ~/tony-tests/RUN_PIN_HUNT (relay pins, no wheels), RUN_WHEELS (Tony decides).
- McKay's repo ~/Desktop/barnaby/evil-autonomous-bear-proj is read-only; Tony's work goes in ~/tony-tests and ~/tony-bear.

Related: [[bear-run-with-ui]], [[bear-test-limits]]
- Working dance trigger (2026-10-13): SIG on SDA1 (BCM2, pull-up → relay ON at rest), `~/tony-tests/dance_sda.sh` = LOW 0.3 s then release. Short ON pulses on GPIO17 did not work after the wiring was taped. The Pi reboots during actuator use (power bank), so expect container restarts.
- The Pi has no GitHub credentials: send files to the "Bear project deadline" cloud session to commit/push (Forzalab/evil-autonomous-bear-proj, branch ccr-0e989f41-17205e, PR #5).
- Wheels (2026-10-13 03:42): real map wheel1 STEP=BCM13 DIR=BCM26, wheel2 STEP=BCM16 DIR=BCM21 (not 20); binaries ~/tony-tests/wheel_real, sos_real. "No spin" was the DRV8825 Vref screw (too high → overcurrent latch until power cycle; too low → no torque). Brain lives at ~/brain (account alt; set BRAIN_DIR=/home/spauly/brain for save.sh).
