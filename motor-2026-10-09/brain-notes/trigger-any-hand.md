---
name: trigger-any-hand
description: Tony's trigger design (Oct 9 12:4x PT) — every hand signal makes the bear react, once per cooldown period; team still to agree at Fri build
type: decision
status: draft
stale_after: 2026-10-24
---
- Why: demo visitors won't know a magic gesture (thumbs_up). Crude gestures (middle finger, OK, V-at-mouth, licking) are what college kids will try → bear should react "angry/annoyed", be animative.
- Rule (proposal): any hand detected (gesture label != "none", incl. unknown) + cooldown passed → fire once; hands keep showing → fire again each cooldown period (≥1 reaction per period); no hand → nothing.
- Consequence: hand-detection recall matters more than gesture classification. Classifier labels become logs only.
- Hardware limit: bear = 1-bit Try Me → one dance; "angry" vs other moods needs another output (sound/LED) → UNKNOWN, ask team.
- Open for team (Fri 2–5pm): hands only, or faces too? cooldown length = longest measured dance + 2 s (bear-test-plan §6.1).
- Phone bugs that triggered this (Oct 9): middle finger → unknown; OK / V-at-mouth / licking → unknown/open_palm/none; grin → sad/neutral; tongue out → sad→neutral→happy. Gesture + emotion agents researching (session 01UqV5CF).
