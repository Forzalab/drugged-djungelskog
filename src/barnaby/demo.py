"""Download a smiling/waving sample and simulate a camera without a webcam."""

import argparse
from pathlib import Path
from urllib.request import Request, urlopen

from .app import main as run_camera
from .models import verified

CLIP = {
    "filename": "smiling-wave.mp4",
    "url": "https://videos.pexels.com/video-files/10374292/10374292-hd_1280_720_24fps.mp4",
    "size": 2806631,
    "sha256": "9746732e08af8d2bae700712975c365d70369432e998fed7e772376c0229c82c",
}
SOURCE = "https://www.pexels.com/video/man-waving-his-hand-while-looking-at-the-camera-10374292/"


def download_clip(directory: Path) -> Path:
    path = directory / CLIP["filename"]
    if verified(path, CLIP):
        return path
    directory.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".mp4.part")
    request = Request(CLIP["url"], headers={"User-Agent": "Mozilla/5.0"})
    print("Downloading demo clip by RDNE Stock project / Pexels.")
    try:
        with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        if not verified(temporary, CLIP):
            raise ValueError("Demo video checksum/size mismatch")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Play once instead of looping")
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument("--recordings-dir", type=Path, default=Path("recordings"))
    args, camera_args = parser.parse_known_args()
    try:
        path = download_clip(args.recordings_dir)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Demo download failed: {error}\n")
    print(f"Sample: {path} | Source: {SOURCE}")
    if not args.download_only:
        options = ["--source", str(path), "--realtime", "--inference-width", "640"]
        if not args.once:
            options.append("--loop")
        run_camera(options + camera_args)


if __name__ == "__main__":
    main()
