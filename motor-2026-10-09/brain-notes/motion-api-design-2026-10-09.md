---
name: motion-api-design-2026-10-09
description: Tony's draft motion API for the bear cart (Fri 16:5x–17:1x PT, Cluck session) — signatures, decisions, open attacks
type: decision
status: draft
stale_after: 2026-10-24
---
- Draft (C++-ish pseudocode, Tony):
  - `Promise move(direction_enum, milliseconds, lambda_after, trigger_id);` — queued, mutex, one motion at a time.
  - `Promise dismiss(trigger_id, lambda_after);` — drop all queued moves of that trigger_id.
  - Promises auto-reject with a reason.
- trigger_id = per HUMAN (Tony). Needs cross-frame identity → Tony scope: FACE tracking only, as a NEW module/file bolted on top of McKay's vision code (McKay's files stay read-only, per rule).
- Language: Tony prefers C++; app is Python. Bridge options not yet discussed (subprocess to C++ binary vs Python GPIO).
- Open attacks (Cluck, one per turn): hand↔face ownership (gesture from a hand, id from a face); Halloween masks/turned faces; one-person demo fallback (global id + dismiss after N s no face) = YAGNI option; does dismiss abort the running segment (abrupt stop = jerk → resonance/tip, see motor-hardware §10); reject reasons enum (dismissed / busy / unsafe during 20 s Try Me / estop — whiteboard lists "E-stop"); ms vs steps; Promise + lambda_after duplicate; missing ramp / random-dwell params (Fable profile).

## Hand↔person research (17:2x PT) — _files/hand-face/HAND-FACE.md (URLs inside; Pi 5 fps mostly UNVERIFIED → time it on the Pi first)
- trigger_id needs TRACKING (box overlap + motion math, no NN), not recognition. Run on the single Pi 5; cloud = seconds/frame + venue Wi-Fi + Gemini API terms bar apps likely used by under-18s; 2nd Pi only if Pi 5 < 5 fps.
- TOP: person detector (YOLOX-nano / NanoDet, ncnn; ~38–43 fps model-only, unconfirmed) + ByteTrack/SORT (roboflow/trackers Apache-2.0 or Norfair BSD-3); hand→person: RTMPose-t (rtmlib, Apache) only on person boxes overlapping a palm, match hand to nearest wrist. Est 6–10 fps with existing models (estimate).
- RUNNER-UP: one-pass multi-person pose (RTMO via rtmlib, Apache, no Pi number; YOLO11n-pose ~6 fps ncnn but AGPL).
- Precedence: 1 wrist + forearm direction; 2 hand inside exactly one person box; 3 overlap → nearest shoulder; 4 nearest face only if close and below the hand; 5 else unassigned. Require a few frames of agreement before owner change. Nearest-face fails: reaching across, close faces flip, masks (archived patch 0001 admits "crossed arms will mis-pair").
- Masks: person boxes + tracker + body-pose wrists need no face; YuNet/expression/BlazePose do. No Pi-ready head detector found.
- Privacy: ids in memory only, expire with track, --save-video off at event.
- YAGNI fallback (one-person demo): trigger_id = 0; new id after scene empty ~3 s; largest palm wins (as vision.py now).

## Tony's architecture idea (17:2x PT)
- Identify visitor once at entry (detection/recognition), then hand off to a cheap tracking module; per-visitor state (LLM/scene output already generated for that id) moves with the track.
- PUSH-based: tracker pushes changes/events (enter, leave, gesture with id) to the decider (McKay's scene/reaction side) — observer pattern; new module, McKay files untouched.
- Open: is "recognition" = face recognition or just first detection? Who owns the per-visitor state (tracker vs decider)? Event list + payload = the interface to agree with McKay.
- Interface: ask McKay what input his decider wants; feed exactly that (he keeps ownership).

## Execution-layer contract (5 rules, from the physics; 18:1x PT)
1. Ramp every start/stop (S-curve ≥1 s), both wheels together, ratio held constant.
2. Random pauses (2–4 s), never a fixed cadence.
3. Full stop before reversing or changing turn side.
4. No cart motion during the 20 s Try Me dance.
5. First tests with the bear OFF the cart.
- Steering: optional `turn` param (see _files/steer/STEERING.md). McKay's decider layer = "if X then Y"; these rules live under it.
