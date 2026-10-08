from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from barnaby.app import main
from barnaby.camera import Camera


class VideoPlaybackTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "input.avi"
        writer = cv2.VideoWriter(str(self.path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
        self.assertTrue(writer.isOpened())
        for value in (20, 100, 220):
            writer.write(np.full((48, 64, 3), value, dtype=np.uint8))
        writer.release()

    def test_file_stops_at_end_without_looping(self):
        camera = Camera(str(self.path), 64, 48)
        self.addCleanup(camera.close)
        self.assertAlmostEqual(camera.fps, 10)
        for expected in (20, 100, 220):
            ok, frame = camera.read()
            self.assertTrue(ok)
            self.assertAlmostEqual(float(frame.mean()), expected, delta=3)
        self.assertFalse(camera.read()[0])

    def test_loop_rewinds_and_realtime_paces_playback(self):
        camera = Camera(str(self.path), 64, 48, realtime=True, loop=True)
        self.addCleanup(camera.close)
        with patch("barnaby.camera.time.monotonic", return_value=0.0), \
             patch("barnaby.camera.time.sleep") as sleep:
            self.assertTrue(camera.read()[0])
            self.assertTrue(camera.read()[0])
            sleep.assert_called_with(0.1)
            self.assertTrue(camera.read()[0])
            ok, frame = camera.read()
            self.assertTrue(ok)
            self.assertTrue(camera.looped)
            self.assertAlmostEqual(float(frame.mean()), 20, delta=3)
            camera.read()
            self.assertFalse(camera.looped)

    def test_video_options_reject_a_live_camera(self):
        with patch("barnaby.camera.cv2.VideoCapture") as capture:
            with self.assertRaises(ValueError):
                Camera("0", 64, 48, realtime=True)
            capture.assert_not_called()

    def test_recording_cannot_overwrite_input(self):
        original = self.path.read_bytes()
        with self.assertRaises(SystemExit) as exit_code:
            main(["--source", str(self.path), "--save-video", str(self.path), "--headless"])
        self.assertEqual(exit_code.exception.code, 2)
        self.assertEqual(self.path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
