"""Run one small real generation against the isolated ComfyArt instance."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PRESETS = {
    "qwen": ("qwen-image-2.1-t2i.api.json", "9", "image"),
    "krea": ("krea2-turbo-t2i.api.json", "9", "image"),
    "h3": ("t2v-minimax-h3.api.json", "92", "video"),
    "speech": ("speech-drama3.api.json", "5", "audio"),
    "music": ("music-yue2.api.json", "10", "audio"),
    "trellis": ("image-to-3d-trellis2.api.json", "30", "3d"),
}


def request(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    try:
        with urlopen(Request(url, data=data, headers={"Content-Type": "application/json"}), timeout=120) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(exc.read().decode()) from exc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=PRESETS)
    parser.add_argument("--url", default="http://127.0.0.1:8288")
    parser.add_argument("--output", type=Path, default=Path(".audit/local-runtime/evidence"))
    parser.add_argument("--input", help="Uploaded input filename for Trellis")
    args = parser.parse_args()
    filename, result_node, kind = PRESETS[args.kind]
    root = Path(__file__).resolve().parents[1]
    graph = json.loads((root / "workflows" / filename).read_text(encoding="utf-8"))
    if args.kind in ("qwen", "krea"):
        graph["5"]["inputs"].update(width=512, height=512, batch_size=1)
        graph["6"]["inputs"]["prompt" if args.kind == "qwen" else "text"] = "A red ceramic teapot on a pale blue table, soft studio light, clean product photograph."
        graph["7"]["inputs"].update(seed=42, steps=12 if args.kind == "qwen" else 10)
    elif args.kind == "h3":
        graph["131"]["inputs"].update(prompt="A red ceramic teapot rests on a pale blue table. Steam gently rises from the spout, static camera. Quiet room tone.", width=864, height=480)
        graph["133"]["inputs"]["value"] = 5
        graph["129"]["inputs"]["noise_seed"] = 42
    elif args.kind == "speech":
        graph["3"]["inputs"].update(text="你好，我是你的设计助手。语音连接测试成功。", seed=42)
    elif args.kind == "music":
        for node in graph.values():
            if node["class_type"] in ("YuE2GenerateABC", "YuE2GenerateMusic"):
                node["inputs"].update(style="instrumental, gentle piano, warm acoustic jazz, 90 bpm", lyrics="[instrumental]", seed=42)
            if node["class_type"] == "YuE2GenerateMusic":
                node["inputs"]["max_duration"] = 15
        graph["2"]["inputs"]["value"] = "instrumental, gentle piano, warm acoustic jazz, 90 bpm"
        graph["3"]["inputs"]["value"] = "[instrumental]"
    else:
        if not args.input:
            parser.error("--input is required for Trellis")
        graph["1"]["inputs"]["image"] = args.input
    for node in graph.values():
        if "filename_prefix" in node["inputs"]:
            node["inputs"]["filename_prefix"] = f"verification/{args.kind}"
    graph = request(args.url + "/comfyart/resolve-workflow", {"graph": graph})["graph"]
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f"{args.kind}-graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    start = time.monotonic()
    result = request(args.url + "/prompt", {"prompt": graph})
    prompt_id = result["prompt_id"]
    print(f"Queued {args.kind}: {prompt_id}", flush=True)
    (args.output / f"{args.kind}-pending.json").write_text(json.dumps({"prompt_id": prompt_id, "started": time.time()}), encoding="utf-8")
    while time.monotonic() - start < 3600:
        history = request(args.url + "/history/" + prompt_id).get(prompt_id)
        if history:
            (args.output / f"{args.kind}-history.json").write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
            errors = [item for item in history.get("status", {}).get("messages", []) if item[0] == "execution_error"]
            if errors:
                raise RuntimeError(json.dumps(errors, ensure_ascii=False))
            output = history.get("outputs", {}).get(result_node, {})
            records = output.get(kind, output.get("images", output.get("audio", output.get("3d", output.get("videos", [])))))
            if records:
                record = records[0]
                target = args.output / record["filename"]
                with urlopen(args.url + "/view?" + urlencode(record), timeout=120) as response:
                    target.write_bytes(response.read())
                report = {"kind": args.kind, "prompt_id": prompt_id, "seconds": time.monotonic() - start,
                          "file": str(target.resolve()), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
                if kind == "image":
                    from PIL import Image
                    with Image.open(target) as image:
                        report["size"] = image.size
                        image.verify()
                elif kind in ("audio", "video"):
                    probe = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(target)], capture_output=True, text=True, check=True)
                    report["probe"] = json.loads(probe.stdout)
                    subprocess.run(["ffmpeg", "-v", "error", "-i", str(target), "-f", "null", "-"], capture_output=True, check=True)
                else:
                    import trimesh
                    scene = trimesh.load(target, force="scene")
                    report["meshes"] = len(scene.geometry)
                    report["vertices"] = sum(len(mesh.vertices) for mesh in scene.geometry.values())
                    if not report["vertices"]:
                        raise RuntimeError("Empty 3D model")
                (args.output / f"{args.kind}-verified.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps({key: value for key, value in report.items() if key != "probe"}, ensure_ascii=False), flush=True)
                return
        time.sleep(3)
    raise TimeoutError(f"Generation still running: {prompt_id}")


if __name__ == "__main__":
    main()
