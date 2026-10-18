from ComfyArt.api.model_registry import resolve_graph, resolve_name


def test_qwen_bf16_resolves_nested_path():
    assert resolve_name("qwen_image_2.1_int8_convrot.safetensors", [
        "Qwen Image 2.1\\qwen_image_2.1_bf16.safetensors"], "diffusion_models"
    ) == "Qwen Image 2.1\\qwen_image_2.1_bf16.safetensors"


def test_other_architectures_are_not_aliases():
    import pytest
    with pytest.raises(ValueError, match="missing"):
        resolve_name("qwen_image_2.1_int8_convrot.safetensors", [
            "qwen_image_edit_2511_bf16.safetensors"], "diffusion_models")


def test_duplicate_basename_is_rejected():
    import pytest
    with pytest.raises(ValueError, match="ambiguous"):
        resolve_name("model.safetensors", ["a/model.safetensors", "b/model.safetensors"], "vae")


def test_category_does_not_borrow_aliases():
    import pytest
    with pytest.raises(ValueError, match="missing"):
        resolve_name("qwen_image_2.1_int8_convrot.safetensors", [
            "qwen_image_2.1_bf16.safetensors"], "vae")


def test_graph_resolution_uses_node_choices_without_mutating_source():
    class Loader:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"unet_name": (["local/qwen_image_2.1_bf16.safetensors"],)}}
    graph = {"1": {"class_type": "UNETLoader", "inputs": {
        "unet_name": "qwen_image_2.1_int8_convrot.safetensors"}}}
    resolved, bindings, missing = resolve_graph(graph, {"UNETLoader": Loader})
    assert not missing
    assert resolved["1"]["inputs"]["unet_name"] == "local/qwen_image_2.1_bf16.safetensors"
    assert bindings["1"]["unet_name"] == "local/qwen_image_2.1_bf16.safetensors"
    assert graph["1"]["inputs"]["unet_name"] == "qwen_image_2.1_int8_convrot.safetensors"


def test_graph_reports_missing_nodes_instead_of_marking_available():
    _, _, missing = resolve_graph({"1": {"class_type": "MissingTrellis", "inputs": {}}}, {})
    assert missing == ["missing node: MissingTrellis"]


def test_v3_combo_resolves_drama_models_in_subfolders():
    class Drama:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"model_name": ("COMBO", {"options": [
                "Drama3/drama3_fp8experts_bf16.safetensors"]})}}
    graph = {"1": {"class_type": "Drama3Loader", "inputs": {
        "model_name": "drama3_fp8experts_bf16.safetensors"}}}
    resolved, _, missing = resolve_graph(graph, {"Drama3Loader": Drama})
    assert not missing
    assert resolved["1"]["inputs"]["model_name"] == "Drama3/drama3_fp8experts_bf16.safetensors"


def test_empty_native_combo_does_not_fall_back_to_unrelated_inventory():
    class Loader:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"vae_name": ("COMBO", {"options": []})}}
    _, _, missing = resolve_graph({"1": {"class_type": "VAELoader", "inputs": {
        "vae_name": "missing.safetensors"}}}, {"VAELoader": Loader})
    assert missing == ["missing vae model: missing.safetensors"]


def test_unsupported_clip_architecture_is_unavailable():
    class Clip:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"type": (["stable_diffusion", "qwen_image"],)}}
    _, _, missing = resolve_graph({"1": {"class_type": "CLIPLoader", "inputs": {
        "type": "krea2"}}}, {"CLIPLoader": Clip})
    assert missing == ["unsupported CLIPLoader.type: krea2"]


def test_recipe_input_placeholder_is_not_a_missing_model():
    class Image:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"image": (["existing.png"],)}}
    _, _, missing = resolve_graph({"1": {"class_type": "LoadImage", "inputs": {
        "image": ""}}}, {"LoadImage": Image})
    assert not missing


async def test_resolver_http_rejects_missing_model(bot_client, monkeypatch):
    from ComfyArt.api import model_registry
    class Loader:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"unet_name": ([],)}}
    monkeypatch.setattr(model_registry, "node_classes", lambda: {"UNETLoader": Loader})
    response = await bot_client.post("/comfyart/resolve-workflow", json={"graph": {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "absent.safetensors"}}}})
    assert response.status == 400
    assert (await response.json())["missing"] == ["missing diffusion_models model: absent.safetensors"]


async def test_resolver_http_returns_actual_node_binding(bot_client, monkeypatch):
    from ComfyArt.api import model_registry
    class Loader:
        @classmethod
        def INPUT_TYPES(cls):
            return {"required": {"unet_name": ("COMBO", {"options": ["Qwen/qwen_image_2.1_bf16.safetensors"]})}}
    monkeypatch.setattr(model_registry, "node_classes", lambda: {"UNETLoader": Loader})
    response = await bot_client.post("/comfyart/resolve-workflow", json={"graph": {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2.1_int8_convrot.safetensors"}}}})
    assert response.status == 200
    data = await response.json()
    assert data["graph"]["1"]["inputs"]["unet_name"] == "Qwen/qwen_image_2.1_bf16.safetensors"
