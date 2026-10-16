---
name: bear-test-limits
description: Bear tests — cap Gemini at 10 calls/min, use a system sound for generic speaker checks, scene model to use
metadata:
  type: feedback
---

- Cap all Gemini calls during bear tests at 10 per minute total (e.g. `--scene-interval 6` or slower for a single app run; count direct test calls too).
- For a generic "does the speaker trigger" test, play a built-in system sound instead of calling Gemini: `pw-play /usr/share/sounds/alsa/Front_Center.wav` (also /usr/share/sounds/freedesktop/stereo/*.oga).
- Use `--scene-model gemini-3.5-flash-lite`; the default gemini-3.8-flash returned 504 DEADLINE_EXCEEDED on 2026-10-12. Voice output via Piper was confirmed working by the user.

**Why:** the user wants to limit Gemini usage and keep speaker checks cheap.
**How to apply:** any camera/speaker/relay test on the Pi. Related: [[bear-run-with-ui]]
