#!/bin/bash
# bear_loop.sh — keep Frankie running forever (frankie.py: gestures → dance/voice, Gemini roast every 20 s). Restarts on crash.
# Started by boot.sh. Gemini ON (flash-lite, every 20 s; NO_GEMINI=1 = gestures only).
# Stop:  touch ~/tony-tests/NO_BEAR ; kill the frankie.py python (pgrep -f tony-tests/frankie.py)    Resume: rm ~/tony-tests/NO_BEAR, run this script.
T=/home/spauly/tony-tests
REPO=/home/spauly/Desktop/barnaby/evil-autonomous-bear-proj
export HOME=/home/spauly XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 DISPLAY=:0
export BEAR_DANCE_BIN=$T/dance_gpio17.sh   # SIG on GPIO17 since 2026-10-13 09:40 (3/3). Old: dance_sda.sh (SDA1)
exec >>"$T/bear_loop.log" 2>&1
log() { echo "$(date '+%F %T') $*"; }
cd "$REPO" || exit 1
while [ ! -e "$T/NO_BEAR" ]; do
    for i in $(seq 60); do [ -e /dev/video0 ] && break; sleep 1; done
    [ -e /dev/video0 ] || { log "no webcam (/dev/video0), retry in 30 s"; sleep 30; continue; }
    ui=(); [ -S /run/user/1000/wayland-0 ] || ui=(--headless)   # window when a desktop exists, else headless
    log "start bear detection ${ui[*]:-with window}"
    .venv/bin/python -u "$T/frankie.py" --source 0 "${ui[@]}" </dev/null >/dev/null   # stderr (dances, yells, errors) → log
    log "bear detection exited ($?), restart in 5 s"
    sleep 5
done
log "NO_BEAR set, loop stopped"
