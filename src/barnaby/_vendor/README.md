These inference helpers are copied unchanged from
https://github.com/opencv/opencv_zoo/tree/47534e27c9851bb1128ccc0102f1145e27f23f98

- `mp_palmdet.py`: `models/palm_detection_mediapipe/mp_palmdet.py`
- `mp_handpose.py`: `models/handpose_estimation_mediapipe/mp_handpose.py`
- `facial_fer_model.py`: `models/facial_expression_recognition/facial_fer_model.py`

The upstream project and these model directories use Apache 2.0; a copy is
included as `LICENSE`. The facial expression directory's README declares
Apache 2.0, although that directory has no separate LICENSE file at this revision.
The facial expression helper retains its upstream copyright notice.

The separately downloaded YuNet model uses MIT; its upstream license is
included as `LICENSE-YUNET`. Model sources, sizes, and SHA-256 digests are
recorded in `../model_manifest.json`.
