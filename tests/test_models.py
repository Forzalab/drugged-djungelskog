import hashlib
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from barnaby.models import download, verified


class ModelsTest(unittest.TestCase):
    def setUp(self):
        self.content = b"test weights"
        self.entry = {"filename": "test.onnx", "size": len(self.content),
                      "sha256": hashlib.sha256(self.content).hexdigest(),
                      "url": "https://example.invalid/test.onnx"}

    def test_rejects_same_size_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.onnx"
            path.write_bytes(self.content)
            self.assertTrue(verified(path, self.entry))
            path.write_bytes(b"x" * len(self.content))
            self.assertFalse(verified(path, self.entry))

    def test_invalid_download_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.onnx"
            path.write_bytes(b"old")
            with patch("barnaby.models.MANIFEST", {"models": {"test": self.entry}}), \
                 patch("barnaby.models.urlopen", return_value=BytesIO(b"bad")):
                with self.assertRaises(ValueError):
                    download(Path(directory))
            self.assertEqual(path.read_bytes(), b"old")
            self.assertFalse(path.with_suffix(".onnx.part").exists())

    def test_verified_download_is_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("barnaby.models.MANIFEST", {"models": {"test": self.entry}}), \
                 patch("barnaby.models.urlopen", return_value=BytesIO(self.content)) as fetch:
                download(Path(directory))
                download(Path(directory))
                self.assertEqual(fetch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
