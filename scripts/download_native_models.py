"""Download pinned native model files; verify hashes before exposing them to ComfyUI."""

import argparse
import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

FILES = [
    ("checkpoints/yue2_3b_int8_convrot.safetensors", "YuE2", "2f76ca75e6ee094169de899cc7fc99d6887e2196", 3960938800, "96fe199377309001ed8cd26a944baeee8cc31a20ba7c36d1d3c0a7e1f4149db6"),
    ("diffusion_models/trellis_2_int8_convrot.safetensors", "TRELLIS.2", "430a9d09b2416687018c8fe8edced2ad4858a439", 5253048192, "d01952ad137213f6a868f86b6b877026276f84af5eec23069217475a0bad3a31"),
    ("vae/trellis_2_shape_vae_bf16.safetensors", "TRELLIS.2", "430a9d09b2416687018c8fe8edced2ad4858a439", 1095844024, "de0cb4949a76c59ee5c091a995a69bcc8c51d5aeda939f0c641a50d2a72341f4"),
    ("vae/trellis_2_texture_vae_bf16.safetensors", "TRELLIS.2", "430a9d09b2416687018c8fe8edced2ad4858a439", 948461364, "714e5ebf094a610e12a8e3b5175c18a62f37f6ea4218acb6073644456b73ab0e"),
    ("clip_vision/dino_v3_L_naf_fp32.safetensors", "Pixal3D", "f37641be376725d324c56626007cc477f1249a69", 1215214176, "4ad2ec4e0879a5b5b04cd97325cc37da954a7b6edca5170b86510f17f2b2290f"),
]


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(root, item):
    name, repo, revision, size, sha = item
    target = root / name
    if target.exists():
        if target.stat().st_size != size or checksum(target) != sha:
            raise ValueError(f"Existing file differs; preserving it: {target}")
        return {"file": name, "sha256": sha, "status": "existing_verified"}
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + ".part")
    offset = part.stat().st_size if part.exists() else 0
    url = f"https://huggingface.co/Comfy-Org/{repo}/resolve/{revision}/{name}?download=true"
    print(f"Downloading {name}, {offset}/{size} bytes", flush=True)
    while offset < size:
        end = min(size - 1, offset + 64 * 1024 * 1024 - 1)
        for attempt in range(3):
            request = Request(url + f"&part={offset}", headers={"Range": f"bytes={offset}-{end}"})
            try:
                with urlopen(request, timeout=90) as response:
                    expected = f"bytes {offset}-{end}/{size}"
                    if response.status != 206 or response.headers.get("Content-Range") != expected:
                        raise ValueError(f"Unexpected byte range for {name}")
                    data = response.read(end - offset + 2)
                    if len(data) != end - offset + 1:
                        raise ValueError(f"Incomplete byte range for {name}")
                break
            except (OSError, ValueError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        with part.open("ab") as stream:
            stream.write(data)
        offset = end + 1
        print(f"{name}: {offset}/{size}", flush=True)
    if part.stat().st_size != size or checksum(part) != sha:
        raise ValueError(f"Download verification failed, partial retained: {part}")
    os.replace(part, target)
    print(f"Verified {name}", flush=True)
    return {"file": name, "sha256": sha, "status": "downloaded_verified"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.download:
        print(json.dumps(FILES, indent=2))
        return
    with ThreadPoolExecutor(max_workers=3) as pool:
        reports = list(pool.map(lambda item: download(args.root, item), FILES))
    text = json.dumps(reports, indent=2)
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
