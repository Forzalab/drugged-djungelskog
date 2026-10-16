#!/bin/bash
# dance_loop.sh — prod mode (Tony 12:20): press Try Me every DANCE_EVERY s (default 35; the bear locks ~25 s after a dance).
# Gesture dances from frankie.py still work on top. Stop: touch ~/tony-tests/NO_DANCE. Started/kept alive by guardian.sh.
T=/home/spauly/tony-tests
while [ ! -e "$T/NO_DANCE" ]; do
    "$T/dance_gpio17.sh"
    echo "$(date '+%T') dance_loop: auto dance" >> "$T/pulse_seq.log"
    sleep "${DANCE_EVERY:-35}"
done
