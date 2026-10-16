"""Aggressive detection tuning for Frankie (wraps McKay's barnaby, READ-ONLY).

Usage from a wrapper (e.g. frankie.py), BEFORE barnaby.app.main():
    import detect_tuning
    detect_tuning.apply()
    barnaby.app.main(argv + detect_tuning.ARGS)   # later argparse flags win

No barnaby file is edited; apply() only patches classes/functions in memory.
Every patch is try/except and logs what it changed to stderr.

Knobs (old -> new, false-positive risk)
---------------------------------------
CLI (ARGS):
  --stable-frames  3 -> 2     Two consecutive matching frames (~2 x 0.08 s +
                              inference ~= 0.25 s) before a label publishes.
                              1 would flicker: a single misclassified frame
                              (e.g. a half-curled hand read as middle_finger)
                              fires a reaction. StableLabel resets on 'none',
                              and frankie.py already dedups the same gesture
                              for 10 s, so 2 costs ~one frame of latency and
                              kills most one-frame ghosts. Risk: low.
  --interval       0.15 -> 0.08  Min seconds between inference starts. Infer
                              itself takes ~50-90 ms at 320 px, so this runs
                              close to back-to-back (~8-10 Hz). CPU: ~1.3-1.6
                              cores of 4 with --threads 2; leaves ~2 cores for
                              Piper + audio. Risk: none (CPU only).
  --inference-width 320 -> 320  Unchanged. Palm detector letterboxes to 192x192
                              anyway; going lower hurts YuNet faces and hand
                              landmark crops for people far away in the hall.
  --threads        2 -> 2     Unchanged; 3+ starves Piper TTS on a 4-core Pi 5.

Runtime patches (apply()):
  MPPalmDet.score_threshold   0.65 -> 0.50  (palm box score; vision.py hardcodes
                              0.65). Finds smaller/angled/far palms. Risk:
                              medium - more palm boxes on faces/patterned
                              costumes, BUT every palm box must still pass the
                              hand-landmark model, which is the real gate.
  MPHandPose.conf_threshold   0.80 -> 0.65  (hand-landmark "is a hand" score).
                              Accepts blurrier / partially occluded hands.
                              Risk: medium - noisy landmarks -> 'unknown' more
                              often (harmless), occasionally a wrong finger
                              pattern; stable-frames 2 filters most.
  YuNet score threshold       0.80 -> 0.60  (face/person detection). Picks up
                              smaller, side-on, masked/painted faces. Risk:
                              medium-low - face is only used for expression,
                              and expression on a false face is just noise.
  YuNet NMS                   0.30 -> 0.30  unchanged (only the largest face is
                              used, so NMS doesn't matter).
  Palm NMS                    0.30 -> 0.30  unchanged.
  gestures._straight cosine  -0.75 -> -0.70 (finger "straight" if joint angle
                              > ~134 deg instead of ~139 deg). Slightly bent
                              fingers in a lazy peace sign / open palm still
                              count. Risk: low-medium - a half-curled index
                              next to a middle finger can read as 'peace'
                              instead of 'middle_finger'. Keep modest; set
                              STRAIGHT_COS = -0.75 to disable.
"""

import sys

ARGS = ["--stable-frames", "2", "--interval", "0.08",
        "--inference-width", "320", "--threads", "2"]

PALM_SCORE = 0.50   # was 0.65 (vision.py)
HAND_CONF = 0.65    # was 0.80 (vision.py)
FACE_SCORE = 0.60   # was 0.80 (vision.py, YuNet)
STRAIGHT_COS = -0.70  # was -0.75 (gestures._straight)

def _log(msg):
    print(f"[detect_tuning] {msg}", file=sys.stderr, flush=True)


def _tune_vision(vision):
    """Lower thresholds on a constructed barnaby.vision.Vision instance."""
    try:
        old = vision.palms.score_threshold
        vision.palms.score_threshold = PALM_SCORE
        _log(f"palm score_threshold {old} -> {PALM_SCORE}")
    except Exception as e:
        _log(f"palm threshold patch failed: {e!r}")
    try:
        old = vision.hands.conf_threshold
        vision.hands.conf_threshold = HAND_CONF
        _log(f"hand conf_threshold {old} -> {HAND_CONF}")
    except Exception as e:
        _log(f"hand threshold patch failed: {e!r}")
    try:
        old = vision.faces.getScoreThreshold()
        vision.faces.setScoreThreshold(FACE_SCORE)
        _log(f"YuNet score_threshold {old:.2f} -> {FACE_SCORE}")
    except Exception as e:
        _log(f"YuNet threshold patch failed: {e!r}")


def apply():
    """Patch barnaby in memory. Idempotent (markers), so safe to call again.
    Call after barnaby is importable (after frankie's sys.path insert) and
    before barnaby.app.main()."""

    # 1) Wrap Vision.__init__ so every Vision built afterwards is tuned.
    try:
        import barnaby.vision as bv
        original_init = bv.Vision.__init__
        if not getattr(original_init, "_frankie_tuned", False):
            def tuned_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                _tune_vision(self)
            tuned_init._frankie_tuned = True
            bv.Vision.__init__ = tuned_init
            _log("wrapped barnaby.vision.Vision.__init__ (thresholds set on construction)")
    except Exception as e:
        _log(f"Vision patch failed: {e!r}")

    # 2) Slightly looser finger-straightness test. classify_gesture looks up
    #    _straight in the gestures module globals, so replacing it there works
    #    for barnaby.vision.classify_gesture too.
    try:
        import numpy as np
        import barnaby.gestures as bg
        if STRAIGHT_COS != -0.75 and not getattr(bg._straight, "_frankie_tuned", False):
            def _straight(points, base, joint, tip):
                a, b = points[base] - points[joint], points[tip] - points[joint]
                denominator = np.linalg.norm(a) * np.linalg.norm(b)
                if denominator < 1e-8:
                    return False
                cosine = float(np.dot(a, b) / denominator)
                return cosine < STRAIGHT_COS and (
                    np.linalg.norm(points[tip] - points[0]) > np.linalg.norm(points[joint] - points[0]))
            _straight._frankie_tuned = True
            bg._straight = _straight
            _log(f"gestures._straight cosine -0.75 -> {STRAIGHT_COS}")
    except Exception as e:
        _log(f"gesture patch failed: {e!r}")

    _log(f"suggested CLI args: {' '.join(ARGS)}")
