#!/bin/bash
# dance_gpio17.sh — trigger the bear with SIG on GPIO17 (physical pin 11): same pattern as dance_sda.sh.
# Relay held ON (closed) at rest by driving 17 HIGH; a dance = OFF 0.3 s, then ON again and held.
# First call after boot (17 idles LOW = open) just closes the relay (close edge = the plug-in "kickstart").
trap 'pinctrl set 17 op dh' EXIT
pinctrl set 17 op dl; sleep "${G17_OFF_S:-0.3}"; pinctrl set 17 op dh
echo "$(date '+%T') dance_gpio17: relay OFF ${G17_OFF_S:-0.3}s then ON" >> /home/spauly/tony-tests/pulse_seq.log
