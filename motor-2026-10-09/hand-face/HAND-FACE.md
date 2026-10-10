# HAND-FACE: per-person trigger_id + hand-to-person association (Pi 5, CPU)

Researched 2026-10-10. Every claim has a URL. **[UNVERIFIED]** means I could not confirm it from a source in this session (my own estimate or inference). **[EST]** means I derived the number myself from cited figures.

Context read (read-only): `src/barnaby/vision.py` runs YuNet + FER + MediaPipe palm and hand ONNX through `cv2.dnn` and picks only the largest face and best hand ("this is not identity tracking"). Archived patches in `brain/.../archive/multi-person-2026-10-09/`: `0001` pairs each hand with the **nearest face centre** and notes "crossed arms will mis-pair"; `0002` is a latest-frame-wins Gemini client (`gemini-2.0-flash`, 320 px JPEG, 8 s timeout, results dropped after 3 s).

---

## TL;DR

- **Top:** a **person detector, then a cheap IoU/Kalman tracker (ByteTrack or SORT) for `trigger_id`**. Hands are assigned through **body-pose wrist keypoints**, and pose runs **only on person boxes that overlap a detected palm**. Use permissive models: YOLOX-nano (Apache-2.0) or NanoDet (Apache-2.0) as the detector, Roboflow `trackers` (Apache-2.0) or Norfair (BSD-3) as the tracker, and RTMPose-t/s through `rtmlib` (Apache-2.0) as the pose model.
- **Runner-up:** a **one-stage multi-person pose model** that outputs a box and keypoints per person in one pass: RTMO via rtmlib (Apache) or YOLO11n-pose (**AGPL-3.0**, reported at about 6 fps with NCNN). Feed its boxes to the same tracker.
- **Why not nearest-face:** see the precedence rule in section 1.
- **Masks:** tracking and hand ownership must not depend on the face. YuNet and the face-based MediaPipe person detector both need a face (section 2).
- **Where it runs:** on the Pi 5 alone (section 7). Tracking is detector + Kalman/IoU math, with no recognition NN.

---

## 1. Associating a hand with a person (ranked)

| Rank | Method | Strength | Failure cases |
|---|---|---|---|
| 1 | **Wrist-keypoint match.** A multi-person body pose gives wrist→elbow→shoulder per person, so the hand belongs to the person whose wrist keypoint is nearest the hand model's wrist landmark (MediaPipe landmark 0). | The arm chain is physically connected, so a reach across someone else still resolves correctly. | Pose fails on heavy costume occlusion (cloaks, inflatables). This needs the pose model's cost (section 3). |
| 2 | **Whole-body pose** (COCO-WholeBody, 133 kpts: body + face + hands per person by construction). Examples: RTMW/DWPose via rtmlib ([rtmlib, Apache-2.0](https://github.com/Tau-J/rtmlib)), MMPose. | The face, hands and body come out already grouped per person. | Heaviest option: top-down, one run per person. No Pi 5 number found **[UNVERIFIED]**. |
| 3 | **Person-box containment.** The hand centre lies inside exactly one tracked person box. | Free once a tracker exists. | Ambiguous when boxes overlap (two people close together), and an outstretched arm can leave its own box. |
| 4 | **Nearest face or head** (archived patch `0001`). | Free. | (a) **Reach-across**: A's hand lands in front of B's face, so it is assigned to B. (b) **Two people close together**: centre distances tie and the assignment flips between frames. (c) **Masked or turned-away person**: no face, so the hand goes to a wrong face or stays unassigned. (d) A raised hand is often nearer to a shorter neighbour's face. **[UNVERIFIED as a measured rate; these are geometric failure modes, and `0001` itself notes "crossed arms will mis-pair"]** |
| 5 | **MediaPipe Holistic.** | Simple. | Built around **one** prominent person ("It will try to detect the most prominent person", [Holistic docs](https://cdn.jsdelivr.net/npm/@subhajit-gorai/react-native-mediapipe-llm@1.0.3/mediapipe/docs/solutions/holistic.md)). The newer Pose Landmarker does support `num_poses` > 1, default 1 ([Google docs](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker)), but the BlazePose detector uses "a fast on-device face detector as a proxy for a person detector" ([BlazePose paper](https://arxiv.org/pdf/2006.10204)), so it is **mask-fragile**. |

**Precedence rule (proposed):**
1. Wrist keypoint of a tracked person within about 0.5 hand-widths of the hand-model wrist, and the forearm direction (elbow→wrist) consistent with the hand → assign to that person.
2. Otherwise, if the hand lies inside exactly one person box → that person.
3. Otherwise, if it lies inside several boxes → the box whose shoulder keypoint, or upper-box corner on the same side, is nearest to the hand.
4. Otherwise, nearest face or head **only if** it is within k × face width and *below* the hand.
5. Otherwise, the hand is **unassigned**: the bear may react generically, but no `trigger_id` is attributed.

Add hysteresis: keep the previous owner unless a different person wins for N consecutive frames. **[UNVERIFIED design; it needs tuning on footage]**

## 2. Per-person tracking without faces, and the effect of masks

- **Trackers.** All of these do association with Kalman motion plus IoU and need no NN:
  - SORT, ByteTrack (adds association of low-score boxes) and OC-SORT: MIT, about 1.1k stars ([OC-SORT](https://www.opentrain.ai/papers/observation-centric-sort-rethinking-sort-for-robust-multi-object-tracking--arxiv-2203.14360/), [stars/license via ecosyste.ms](https://repos.ecosyste.ms/topics/ocsort)).
  - BoT-SORT and DeepSORT optionally add an **appearance re-ID embedding**, which is a CNN per box and the heavier part.
  - Clean-room Apache-2.0 implementations of SORT, ByteTrack, OC-SORT and BoT-SORT are in [roboflow/trackers](https://github.com/roboflow/trackers) (3.9k stars). They accept any boxes, and the base install needs no inference library.
  - [Norfair](https://github.com/tryolabs/norfair) (BSD-3, 2.7k stars) is detector-agnostic, supports custom distance functions, and can track keypoints.
  - BoxMOT aggregates many trackers (about 7.4k stars, [ecosyste.ms](https://repos.ecosyste.ms/topics/ocsort)). Its license is **[UNVERIFIED]**; I believe it is AGPL.
  - Official ByteTrack and BoT-SORT repos being MIT: **[UNVERIFIED in-session]**.
- **Detectors that ignore faces:**
  - COCO "person" detectors (YOLOX-nano, NanoDet) and body-pose models are trained on whole-body appearance. A mask changes a small part of the box, so they should keep working **[UNVERIFIED]**.
  - Head detectors trained on crowds (CrowdHuman, SCUT-Head): [Head-Detection-Yolov8](https://github.com/Owen718/Head-Detection-Yolov8) (Ultralytics-based, so AGPL-encumbered **[UNVERIFIED]**), [HeadHunter](https://github.com/Sentient07/HeadHunter-T). These would cover Tony's "non-human faces", meaning masked heads and the backs of heads, but I found no Pi-ready ONNX release **[UNVERIFIED]**.
- **What masks break:**
  - YuNet face detection and FER.
  - MediaPipe/BlazePose person detection, which is face-proxy ([paper](https://arxiv.org/pdf/2006.10204)). The opencv_zoo `person_detection_mediapipe` model is derived from BlazePose ([HF card, Apache-2.0](https://huggingface.co/opencv/person_detection_mediapipe/blob/main/README.md)), so expect the same weakness **[inference]**.
  - Face-recognition embeddings.
- **What masks don't break:** box detection, IoU tracking and body-pose wrists.
- **Re-ID by clothing** (DeepSORT/BoT-SORT appearance) can work for costumes, which are actually distinctive. It only helps with re-entry after occlusion and is not needed for a short demo.

## 3. What runs on a Pi 5 CPU (reported numbers)

Pi 5 = 2.4 GHz quad Cortex-A76, "between two and three times the CPU ... performance" of Pi 4 ([Raspberry Pi](https://www.raspberrypi.com/news/introducing-raspberry-pi-5/)).

| Model | Runtime | Reported speed | License |
|---|---|---|---|
| NanoDet 320 / YOLOX-nano 416 | ncnn | about 43 / 38.6 fps on Pi 5, inference only ([Q-engineering table](https://github.com/Qengineering/YoloX-ncnn-Raspberry-Pi-4); the column mapping is partly garbled in the fetch, so **[UNVERIFIED column]**) | Apache-2.0 upstream **[UNVERIFIED]**; repo BSD-3 |
| YOLOv8n 640 | ncnn | about 16 fps Pi 5 (same table) | **AGPL-3.0** |
| YOLO11n 640 | ONNX | 6.79 fps Pi 5 ([Ultralytics docs](https://docs.ultralytics.com/guides/raspberry-pi)) | **AGPL-3.0** or paid Enterprise ([Ultralytics license](https://ultralytics.com/license)) |
| YOLO26n | NCNN | 67 ms (about 15 fps) Pi 5 ([Ultralytics docs](https://docs.ultralytics.com/guides/raspberry-pi)) | AGPL-3.0 |
| YOLO11n-pose | NCNN | about 6 fps (from about 2 unexported) ([lmlab blog](https://lmlab.net/posts/2024/2024-12-03-use-ncnn-for-yolo-on-raspberry-pi.html)); about 1.5 fps unoptimised ([Core Electronics](https://core-electronics.com.au/guides/getting-started-with-yolo-pose-estimation-on-the-raspberry-pi/)) | AGPL-3.0 |
| MoveNet MultiPose Lightning | TFLite | "probably 9 fps" on Pi 5, an estimate ([hackaday log](https://hackaday.io/project/162944/log/228804)); SinglePose Lightning 95 ms on **Pi 4** ([TF](https://www.tensorflow.org/hub/tutorials/movenet?hl=en.)) | Apache-2.0 **[UNVERIFIED]** |
| opencv_zoo MPPersonDet / MPPose / MPPalmDet / MPHandPose / YuNet | cv2.dnn | **Pi 4**: 105.6 / 116.2 / 97.1 / 42.6 / 6.2 ms ([opencv_zoo benchmark](https://raw.githubusercontent.com/opencv/opencv_zoo/main/benchmark/README.md)); about 2–3x faster on Pi 5 **[EST]** | Apache-2.0 |
| RTMPose / RTMO / RTMW (rtmlib, ONNX Runtime) | ORT | **No Pi number found** **[UNVERIFIED]**. RTMPose-s is reported at 70+ fps on a Snapdragon 865 ([search summary of the mmpose project](https://cdn05042023.gitlink.org.cn/OpenMMLab/mmpose/src/branch/main/projects/rtmpose)) | Apache-2.0 ([rtmlib](https://github.com/Tau-J/rtmlib), 685 stars) |

**Budget [EST]:** the existing pipeline costs about 146 ms per frame on Pi 4 (palm 97 + hand 43 + YuNet 6, plus FER), so roughly 50–70 ms on Pi 5. Adding NanoDet or YOLOX-nano at about 25 ms plus a tracker at under 1 ms keeps the loop at about 8–10 fps. Adding top-down pose **only for palm-overlapping people** costs one pose run per waving person. **Benchmark on the device before committing.**

## 4. Repos and integration sketch

**Option A (top): detector + tracker + gated pose.**
1. In the existing per-frame loop, after `Vision.infer`, run YOLOX-nano or NanoDet (ONNX via `cv2.dnn` or onnxruntime) on the 320-wide inference frame and keep the `person` class.
2. Pass the boxes to `trackers.ByteTrack` (or Norfair). The returned `tracker_id` becomes `trigger_id`.
3. For each detected hand, find the tracked boxes it overlaps. If there is exactly one, assign it. If there are several, crop those boxes and run RTMPose-t (rtmlib `Body`), then apply the precedence rule from section 1.
4. Emit `PerceptionEvent(trigger_id, gesture, ...)`.
5. Run the detector every frame. Pose only runs when there is ambiguity.

Repos: [roboflow/trackers](https://github.com/roboflow/trackers), [tryolabs/norfair](https://github.com/tryolabs/norfair), [Tau-J/rtmlib](https://github.com/Tau-J/rtmlib), [Qengineering YOLOX-ncnn](https://github.com/Qengineering/YoloX-ncnn-Raspberry-Pi-4).

**Option B (runner-up): one-stage multi-person pose.**
- RTMO via rtmlib (Apache), or YOLO11n-pose NCNN (AGPL, about 6 fps). Run it every frame.
- Use its boxes for the tracker and its wrists for direct hand matching.
- Simpler logic, but a higher constant cost. rtmlib's `PoseTracker` with `det_frequency` (run the detector every N frames) can amortise it ([rtmlib](https://github.com/Tau-J/rtmlib)).

## 5. Privacy and public-demo notes

- **What a stable per-person `trigger_id` needs:** a session-local integer from the IoU tracker. It does **not** need any face or biometric embedding. Keep ids in RAM only, drop a track after a few seconds of absence, and never write ids, crops or embeddings to disk.
- **Recording:** `--save-video` writes annotated footage. Keep it off at a public event, or post a sign.
- **Re-ID embeddings:** if they are ever added, they are biometric-adjacent. Keep them in memory only and expire them with the track. **[legal status jurisdiction-dependent, UNVERIFIED]**
- **Cloud and children:** the Gemini API terms say you "may not use the Services in an application ... likely to be accessed by individuals under the age of 18". A Halloween crowd has children. The terms also say unpaid tiers may be human-reviewed and used for improvement ("Do not submit ... personal information to the Unpaid Services") ([Gemini API terms](https://ai.google.dev/gemini-api/terms)).
- **Signage:** post a "camera in use, nothing stored" sign **[UNVERIFIED legal requirement; good practice]**.

## 6. YAGNI fallback (one-person demo)

- Do not track. Use `trigger_id = 0` whenever any person or face/palm is present.
- Reset to a new id after the scene is empty for T seconds (for example 3 s). This is a simple presence counter.
- The largest palm wins, which matches what `vision.py` already does.
- This covers a single visitor at a booth with zero new models.

## 7. Where to run it (addendum from Tony)

**Tracking vs recognition:**
- **Tracking** is a detector NN plus SORT/ByteTrack association with a Kalman filter and IoU/Hungarian matching: CPU math, no NN. SORT reports 260 Hz on a CPU ([SORT paper](https://arxiv.org/abs/1602.00763) **[from memory, not re-fetched]**).
- **Recognition / re-ID** adds an embedding CNN per box per frame: DeepSORT, BoT-SORT with re-ID, or face recognition (for example SFace).
- **A per-person `trigger_id` only needs tracking.** Re-ID is only needed to keep the same id after someone leaves the frame and returns. That is unnecessary for this demo, and impossible via faces anyway with masks.

| | (a) Pi 5 only (Tony's preference) | (b) Cloud API (Gemini / face services) | (c) Second Pi |
|---|---|---|---|
| Latency | Per frame about 100–150 ms with the detector **[EST]** | A VLM round trip takes seconds. Artificial Analysis lists 10–27 s TTFT for Gemini 3.5/3.6 Flash text-heavy runs ([AA](https://artificialanalysis.ai/de/models/gemini-3-6-flash/providers)). The image path is not benchmarked **[UNVERIFIED]**, and the archived client already uses an 8 s timeout and 3 s staleness. | Same as (a) plus LAN hop (a few ms) **[UNVERIFIED]** |
| FPS | About 6–10 **[EST]** | Below 1 result/s with latest-frame-wins. Unusable for frame-to-frame ids; it can only re-pick a target occasionally. | About 2x the budget (for example pose on Pi #2) |
| Network | None | Required. Venue Wi-Fi/LTE at a public event is a single point of failure, so local must stay the primary path (as `remote.py` already does). | Local Ethernet only |
| Cost | Zero marginal | Per-image token cost. Paid tier is needed for no-training. **[pricing UNVERIFIED]** | One more board, power and cable. Tony avoids this. |
| Privacy | Frames never leave the device | Visitor faces (minors) go off-device. This conflicts with the Gemini under-18 clause and the unpaid-tier review/training terms ([terms](https://ai.google.dev/gemini-api/terms)). Needs consent signage at minimum. | Stays on the LAN |

**Verdict:** (a). Tracking ids are cheap enough for the single Pi 5. (b) cannot provide ids at all at its latency and carries a consent and minors problem. Keep (c) in reserve only if on-device benchmarks show pose plus detector below 5 fps.
