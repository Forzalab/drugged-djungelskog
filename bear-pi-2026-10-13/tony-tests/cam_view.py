"""cam_view.py — plain camera feed, no McKay code (Tony 12:59: gestures/expressions/Frankie off).
Shows the webcam in a window titled 'Barnaby Bear' (so screenshots still find it) and writes the latest frame to
~/tony-tests/cam.jpg about once a second for scene_cam.py. One camera = one process: Frankie must be off (NO_BEAR).
Run: setsid nohup <venv python> -u ~/tony-tests/cam_view.py &      Stop: touch ~/tony-tests/NO_CAM
"""
import os, time
from pathlib import Path

os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
os.environ.setdefault("WAYLAND_DISPLAY", "wayland-0")
os.environ.setdefault("DISPLAY", ":0")
import cv2  # noqa: E402

HERE = Path.home() / "tony-tests"
OUT, TMP = HERE / "cam.jpg", HERE / ".cam.tmp.jpg"


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    show = True
    last_save = 0.0
    while not (HERE / "NO_CAM").exists():
        ok, frame = cap.read()
        if not ok:
            print("camera read failed, retry in 2 s", flush=True)
            time.sleep(2)
            cap.release()
            cap = cv2.VideoCapture(0)
            continue
        if time.monotonic() - last_save > 1.0:
            cv2.imwrite(str(TMP), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            os.replace(TMP, OUT)  # atomic: readers never see a half-written file
            last_save = time.monotonic()
        if show:
            try:
                cv2.imshow("Barnaby Bear", frame)
                cv2.waitKey(1)
            except cv2.error:
                show = False  # no desktop: keep saving frames headless
    cap.release()


if __name__ == "__main__":
    main()
