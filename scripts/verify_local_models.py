"""Inspect the fork's recipes against a running ComfyUI without queuing work."""

import argparse
import importlib.util
import json
import sys
import types
from pathlib import Path
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8188")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    schemas = json.load(urlopen(args.url + "/object_info"))
    sys.modules["folder_paths"] = types.SimpleNamespace(get_filename_list=lambda category: [])
    path = Path(__file__).resolve().parents[1] / "api" / "model_registry.py"
    spec = importlib.util.spec_from_file_location("registry", path)
    registry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(registry)
    classes = {name: type(name, (), {"INPUT_TYPES": staticmethod(lambda item=item: item.get("input", {}))})
               for name, item in schemas.items()}
    result = registry.catalog(classes)
    result["source"] = args.url
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    for model in result["models"]:
        print(f"{model['label']}: {'READY' if model['available'] else 'UNAVAILABLE'}")
        for reason in model["missing"]:
            print(f"  {reason}")


if __name__ == "__main__":
    main()
