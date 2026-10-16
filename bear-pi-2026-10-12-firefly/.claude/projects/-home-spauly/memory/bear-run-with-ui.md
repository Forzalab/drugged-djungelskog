---
name: bear-run-with-ui
description: Always run the barnaby bear app with its preview UI window on the Pi, never --headless
metadata:
  type: feedback
---

Always run `python -m barnaby` with the preview window (no `--headless`). Export XDG_RUNTIME_DIR=/run/user/1000, WAYLAND_DISPLAY=wayland-0, DISPLAY=:0 so the window pops up on the Pi desktop.

**Why:** the user is watching at the Pi, and said headless runs time out.
**How to apply:** for every camera/scene/TTS test of the bear on this Pi, launch with the UI. Tell the user when the speaker should play (TTS only fires after a Gemini description comes back). Keep chat replies short. Related: [[bear-project-sessions]]
