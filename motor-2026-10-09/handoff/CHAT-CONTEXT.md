# Chat-only context (main session, Fri Oct 9 2026, 15:30–18:00 PT) — not all of this is in brain files

## Timeline
- 15:30 Tony at bear build (ended ~16:30). Asked "how to test the motor code live". Repo tayG-oss/franky-fedbear (main.cc, a.out 32-bit armhf; author Tay). Read-only clone /home/user/tayg-oss/franky-fedbear.
- Learned live: STEP/DIR meaning; Try Me pigtail = momentary button, one 20 s cycle, mid-cycle tap ignored; stepper board drives cart; power SOLIX 12 V car socket via Wago; geared steppers 17HS15-1684S-PG5; 6 cm wheels; 2 rear driven wheels mirrored, front casters.
- Tony derived himself: 200 steps × gearbox → ~3.6–3.8 cm per segment (0.018 cm/step); exit-ritual/cleanup need (signal handling); earthquake/resonance concern; front-caster/load concern; zig-zag lean CoM cancellation (drew it); STEP1/STEP2 = one per wheel → independent stepping (Cluck question open: what happens if only STEP1 pulses → pivot/turn, differential drive = P2 is a CODE limit, not told yet).
- Tony raised P1 (20 s Try Me lock) at the build; team went quiet (taken seriously).
- Test B (run main.cc himself on the Pi) NOT done. Hands-on testing planned NEXT WEEK.

## Tony's API draft (C++ pseudocode; app is Python; bridge undecided)
- Promise move(direction_enum, milliseconds, lambda_after, trigger_id); queued, mutex.
- Promise dismiss(trigger_id, lambda_after); drop queued moves of that id. Promises auto-reject with reasons.
- trigger_id = per human. Identify once at entry, then cheap tracking; per-visitor state (LLM/scene data) moves with the track; PUSH events to the decider (observer). New module bolted on top; McKay's files read-only.
- Research: tracking not recognition; person detector + ByteTrack/SORT + RTMPose-t wrist matching; precedence rule; masks OK without faces; run on the single Pi 5; cloud rejected; fallback trigger_id=0.

## Open Cluck questions (do NOT answer for Tony; ask one per turn later)
1. Only STEP1 pulses 200 steps, STEP2 silent → what does the cart do; still "stuck" fwd/back?
2. Reach-across wave: which precedence rule catches it first, why (rule 1 wrist+forearm).
3. Grip fraction: how much of the weight can the drive use for grip (only 2 of 4 wheels driven; casters free).
4. Zip ties: which side works when the cart lurches forward (tension-only).
5. API attacks pending: dismiss mid-segment = abrupt stop (jerk → resonance); reject reason enum (dismissed/busy/unsafe during Try Me/estop — whiteboard lists E-stop); ms vs steps; Promise+lambda duplicate; ramp/random-dwell params (Fable's free fix); C++↔Python bridge; per-visitor state owner (tracker vs decider); event list + payload = interface for McKay.

## Notes
- Rule: never edit McKay-authored code; new modules sit on top.
- Exams: Sunday physics revision, Monday Oct 12 exam. Bear parked until after.
