"""USB/video input on either machine, or optional Picamera2 CSI input on the Pi."""

import math
import time

import cv2


class Camera:
    def __init__(self, source: str, width: int, height: int, picamera: bool = False,
                 realtime: bool = False, loop: bool = False):
        self._pi = None
        self._capture = None
        self.is_file = not picamera and not source.isdecimal()
        if (realtime or loop) and not self.is_file:
            raise ValueError("--realtime and --loop require a video file")
        self.realtime, self.loop = realtime, loop
        self.looped = False
        self.fps = 30.0
        self._next_frame_at = None
        if picamera:
            try:
                from picamera2 import Picamera2
            except ImportError as error:
                raise RuntimeError("Picamera2 is missing; see the CSI camera setup in README.md") from error
            self._pi = Picamera2()
            try:
                config = self._pi.create_video_configuration(main={"size": (width, height), "format": "RGB888"})
                # Picamera2 RGB888 arrays use BGR byte order, matching OpenCV.
                self._pi.configure(config)
                self._pi.start()
            except Exception:
                self._pi.close()
                raise
        else:
            selected = int(source) if source.isdecimal() else source
            self._capture = cv2.VideoCapture(selected)
            if not self._capture.isOpened():
                self._capture.release()
                raise RuntimeError(f"Could not open camera/video {source!r}; try --source 1 or --picamera")
            fps = self._capture.get(cv2.CAP_PROP_FPS)
            if math.isfinite(fps) and fps > 0:
                self.fps = fps
            if not self.is_file:
                self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        self.looped = False
        if self._pi is not None:
            return True, self._pi.capture_array("main")
        if self.realtime and self._next_frame_at is not None:
            time.sleep(max(0.0, self._next_frame_at - time.monotonic()))
        ok, frame = self._capture.read()
        if not ok and self.loop:
            if not self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0):
                raise RuntimeError("Could not rewind the video for looping")
            ok, frame = self._capture.read()
            self.looped = ok
            self._next_frame_at = None
        if self.realtime and ok:
            if self._next_frame_at is None:
                self._next_frame_at = time.monotonic()
            self._next_frame_at += 1.0 / self.fps
        return ok, frame

    def close(self):
        if self._pi is not None:
            self._pi.stop()
            self._pi.close()
        elif self._capture is not None:
            self._capture.release()
