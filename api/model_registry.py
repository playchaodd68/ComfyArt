"""Resolve workflow model roles against the active ComfyUI installation."""

from copy import deepcopy
from pathlib import Path

import folder_paths

WORKFLOWS = Path(__file__).resolve().parent.parent / "workflows"

RECIPES = (
    ("qwen-image-2.1-t2i.api.json", "Qwen Image 2.1", "image"),
    ("z-image-turbo-t2i.api.json", "Z-Image Turbo", "image"),
    ("flux2-klein-9b-t2i.api.json", "Flux.2 Klein 9B", "image"),
    ("qwen-image-2512-t2i.api.json", "Qwen Image 2512", "image"),
    ("ideogram4-t2i.api.json", "Ideogram 4", "image"),
    ("krea2-turbo-t2i.api.json", "Krea2 Turbo", "image"),
    ("t2v-minimax-h3.api.json", "MiniMax H3", "video"),
    ("speech-drama3.api.json", "Fish Audio Drama3", "speech"),
    ("speech-kokoro.api.json", "Kokoro", "speech"),
    ("voice-clone-indextts.api.json", "IndexTTS", "speech"),
    ("music-yue2.api.json", "YuE2", "music"),
    ("music-ace-step.api.json", "ACE-Step", "music"),
    ("sfx-stable-audio.api.json", "Stable Audio", "sfx"),
    ("image-to-3d-trellis2.api.json", "Trellis2", "model"),
)

# These lists contain verified variants of the same model role, never other
# architectures or fine-tunes. Category and exact basename must both match.
VARIANTS = {
    ("background_removal", "birefnet.safetensors"): (
        "birefnet.safetensors", "birefnet_fp32.safetensors"),
    ("vae", "ae.safetensors"): (
        "ae.safetensors", "z_image_ae.safetensors", "flux-ae.safetensors"),
    ("diffusion_models", "qwen_image_2.1_int8_convrot.safetensors"): (
        "qwen_image_2.1_int8_convrot.safetensors", "qwen_image_2.1_bf16.safetensors"),
    ("diffusion_models", "minimax_h3_fl2va_pruned_int8_convrot.safetensors"): (
        "minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        "minimax_h3_fl2va_int8_convrot.safetensors", "minimax_h3_fl2va_bf16.safetensors"),
    ("diffusion_models", "minimax_h3_ref2va_pruned_int8_convrot.safetensors"): (
        "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
        "minimax_h3_ref2va_int8_convrot.safetensors", "minimax_h3_ref2va_bf16.safetensors"),
    ("diffusion_models", "krea2_turbo_fp8_scaled.safetensors"): (
        "krea2_turbo_fp8_scaled.safetensors", "krea2_turbo_bf16.safetensors",
        "krea2_turbo_int8_convrot.safetensors"),
    ("diffusion_models", "flux-2-klein-9b-nvfp4.safetensors"): (
        "flux-2-klein-9b-nvfp4.safetensors", "flux-2-klein-9b-fp8.safetensors",
        "flux-2-klein-9b.safetensors"),
    ("text_encoders", "qwen3vl_8b_int8_convrot.safetensors"): (
        "qwen3vl_8b_int8_convrot.safetensors", "qwen3vl_8b_bf16.safetensors"),
    ("text_encoders", "qwen3vl_4b_fp8_scaled.safetensors"): (
        "qwen3vl_4b_fp8_scaled.safetensors", "qwen3vl_4b_bf16.safetensors"),
    ("text_encoders", "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"): (
        "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        "qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
        "qwen3vl_32b_minimax_h3_bf16.safetensors"),
}

CATEGORIES = {
    "unet_name": "diffusion_models", "ckpt_name": "checkpoints",
    "clip_name": "text_encoders", "clip_name1": "text_encoders",
    "clip_name2": "text_encoders", "vae_name": "vae",
    "lora_name": "loras", "clip_vision_name": "clip_vision",
    "bg_removal_name": "background_removal",
}
NODE_CATEGORIES = {
    ("CLIPVisionLoader", "clip_name"): "clip_vision",
    ("Drama3Loader", "model_name"): "diffusion_models",
    ("Drama3CodecLoader", "codec_name"): "vae",
    ("UpscaleModelLoader", "model_name"): "upscale_models",
    ("ModelPatchLoader", "name"): "model_patches",
}
MODEL_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".gguf")


def basename(name: str) -> str:
    return name.replace("\\", "/").rsplit("/", 1)[-1]


def resolve_name(expected: str, names: list[str], category: str) -> str:
    if expected in names:
        return expected
    candidates = VARIANTS.get((category, basename(expected)), (basename(expected),))
    for candidate in candidates:
        if candidate in names:
            return candidate
        matches = [name for name in names if basename(name) == candidate]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(f"ambiguous {category} model {candidate}: {', '.join(matches)}")
    raise ValueError(f"missing {category} model: {expected}")


def node_classes() -> dict:
    import nodes
    return nodes.NODE_CLASS_MAPPINGS


def combo_choices(spec) -> list[str] | None:
    if not isinstance(spec, (tuple, list)) or not spec:
        return None
    if isinstance(spec[0], list):
        return [item for item in spec[0] if isinstance(item, str)]
    if spec[0] == "COMBO" and len(spec) > 1 and isinstance(spec[1], dict):
        options = spec[1].get("options")
        if isinstance(options, list):
            return [item for item in options if isinstance(item, str)]
    return None


def resolve_graph(graph: dict, classes: dict | None = None) -> tuple[dict, dict, list[str]]:
    classes = node_classes() if classes is None else classes
    resolved = deepcopy(graph)
    bindings: dict[str, dict[str, str]] = {}
    missing: list[str] = []
    schemas: dict[str, dict] = {}
    inventories: dict[str, list[str]] = {}
    for node_id, node in resolved.items():
        if not isinstance(node, dict) or not isinstance(node.get("class_type"), str) or not isinstance(node.get("inputs"), dict):
            raise ValueError(f"invalid workflow node: {node_id}")
        kind = node["class_type"]
        cls = classes.get(kind)
        if cls is None:
            missing.append(f"missing node: {kind}")
            continue
        if kind not in schemas:
            try:
                groups = cls.INPUT_TYPES()
                schemas[kind] = {**groups.get("required", {}), **groups.get("optional", {})}
            except Exception as exc:
                missing.append(f"cannot inspect node {kind}: {exc}")
                continue
        for key, value in node["inputs"].items():
            if not isinstance(value, str):
                continue
            category = NODE_CATEGORIES.get((kind, key), CATEGORIES.get(key))
            spec = schemas[kind].get(key)
            choices = combo_choices(spec)
            if category is None and not value.lower().endswith(MODEL_EXTENSIONS):
                if choices is not None and value and key not in ("image", "audio", "file") and value not in choices:
                    missing.append(f"unsupported {kind}.{key}: {value}")
                continue
            if category is None and not isinstance(choices, list):
                continue
            if choices is not None:
                names = choices
            elif category:
                if category not in inventories:
                    inventories[category] = folder_paths.get_filename_list(category)
                names = inventories[category]
            else:
                continue
            try:
                actual = resolve_name(value, names, category or kind)
            except ValueError as exc:
                missing.append(str(exc))
                continue
            node["inputs"][key] = actual
            bindings.setdefault(str(node_id), {})[key] = actual
    return resolved, bindings, list(dict.fromkeys(missing))


def catalog(classes: dict | None = None) -> dict:
    import json
    classes = node_classes() if classes is None else classes
    models = []
    inspected = {}

    def inspect(filename):
        if filename not in inspected:
            path = WORKFLOWS / filename
            inspected[filename] = resolve_graph(json.loads(path.read_text(encoding="utf-8")), classes) if path.is_file() else ({}, {}, [f"missing workflow: {filename}"])
        return inspected[filename]

    for filename, label, modality in RECIPES:
        _, bindings, missing = inspect(filename)
        capabilities = {}
        if filename == "qwen-image-2.1-t2i.api.json":
            capabilities["multiangle"] = not inspect("multiangle-qwen-image-2.1.api.json")[2]
            capabilities["image_edit"] = not inspect("edit-qwen-image-2.1.api.json")[2]
        if filename == "t2v-minimax-h3.api.json":
            first = not inspect("i2v-minimax-h3.api.json")[2]
            refs = not inspect("r2v-minimax-h3.api.json")[2]
            capabilities.update(first_frame=first, reference_images=refs, reference_videos=refs,
                                reference_audios=refs, lip_sync=first and "MiniMaxH3AddGuide" in classes)
            motion = {
                "pose": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sdpose_wholebody_fp16.safetensors"}},
                "detect": {"class_type": "UNETLoader", "inputs": {"unet_name": "rt_detr_v4-x-hgnet_fp16.safetensors"}},
                "patch": {"class_type": "ModelPatchLoader", "inputs": {"name": "minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors"}},
            }
            for node in ("RTDETR_detect", "SDPoseKeypointExtractor", "SDPoseDrawKeypoints", "MiniMaxH3FunControlNetApply"):
                motion[node] = {"class_type": node, "inputs": {}}
            capabilities["motion_control"] = refs and not resolve_graph(motion, classes)[2]
        models.append({"id": filename, "label": label, "modality": modality,
                       "available": not missing, "missing": missing, "bindings": bindings,
                       "capabilities": capabilities})
    return {"version": 1, "models": models}
