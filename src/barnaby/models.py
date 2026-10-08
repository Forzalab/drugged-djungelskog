"""Download pinned ONNX weights without adding them to Git."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

MANIFEST = json.loads(Path(__file__).with_name("model_manifest.json").read_text())
DEFAULT_MODEL_DIR = Path("models")


def verified(path: Path, entry: dict) -> bool:
    if not path.is_file() or path.stat().st_size != entry["size"]:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == entry["sha256"]


def model_paths(directory: Path) -> dict[str, Path]:
    paths = {}
    for key, entry in MANIFEST["models"].items():
        path = directory / entry["filename"]
        if not verified(path, entry):
            raise FileNotFoundError(
                f"Missing or invalid model: {path}. Run: "
                f'python -m barnaby.models --model-dir "{directory}"'
            )
        paths[key] = path
    return paths


def download(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for entry in MANIFEST["models"].values():
        destination = directory / entry["filename"]
        if verified(destination, entry):
            print(f"Verified {destination.name}")
            continue
        temporary = destination.with_suffix(".onnx.part")
        print(f"Downloading {destination.name} ({entry['size'] / 1e6:.2f} MB)")
        try:
            with urlopen(entry["url"], timeout=60) as response, temporary.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            if not verified(temporary, entry):
                raise ValueError(f"Checksum/size mismatch for {destination.name}")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    args = parser.parse_args()
    try:
        download(args.model_dir)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Model download failed: {error}\n")


if __name__ == "__main__":
    main()
