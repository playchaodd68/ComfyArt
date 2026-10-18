# Media backend evidence, 2026-10-18

Scope is the running ComfyUI at `http://127.0.0.1:8188`, rooted at `F:/Comfy/Installations/ComfyUI D/ComfyUI`. All availability statements below were checked against its live `/object_info`. No generation was submitted, no service restarted, and no model downloaded. This is schema and model-discovery verification, not media-generation acceptance.

## Files changed

- `workflows/speech-drama3.api.json`, five native nodes. Result node `5` is `SaveAudioAdvanced`, returning saved FLAC metadata under history `audio`.
- `workflows/music-yue2.api.json`, ten native nodes. Result node `10` is `SaveAudioAdvanced`, returning saved FLAC metadata under history `audio`.
- `workflows/image-to-3d-trellis2.api.json`, retained its thirty-node graph and changed image crop `pad_factor` to `1.0`, as the live Trellis2Conditioning input tooltip specifies. Result node `30` is `SaveGLB`, returning saved GLB metadata under history `3d`.

## Drama3, discoverable locally

Live `Drama3Loader.input.required.model_name` offers `Drama3\\drama3_fp8experts_bf16.safetensors`. `Drama3CodecLoader.input.required.codec_name` offers `Drama3\\drama3_codec.safetensors`. The files exist under `F:/Comfy/Shared/models/main/diffusion_models/Drama3` and `vae/Drama3`. The template uses basenames, which the root-owned resolver must replace with these exact loader options.

Node sequence is `Drama3Loader` + `Drama3CodecLoader` -> `Drama3Generate` -> `Drama3Decode` -> `SaveAudioAdvanced`. Generate inputs are `model`, `text`, `voices`, `seed`, `temperature`, `top_p`, `top_k`, `max_frames`, `split_long_text`. Defaults match the existing curated `04_音频/中文配音｜Drama3.json`, including `experts="in VRAM"`, temperature 1, top_p .9, top_k 30 and max_frames 600. `max_frames` is a maximum per chunk, not seconds.

For cloning, add `LoadAudio` -> `Drama3EncodeVoice` using the codec and the reference's exact transcript, then set Generate input `voices.voice0` to that output. The flattened key is required by ComfyUI's v3 autogrow protocol. `comfy_api/latest/_io.py` Autogrow creates voice0..voice15 and reconstructs the nested voices dictionary. With no connected voice it supplies an empty dictionary. `Drama3LoadVoice` currently lists `OceanBase\\male_ic_00001_.safetensors`; it must not be silently used for a different user-selected voice. No ASR model is needed when the transcript is supplied explicitly.

The installed implementation is in `F:/Comfy/Shared/custom_nodes/ComfyUI-Drama3/nodes.py`. Live python_module reports the unified custom-node loader name `custom_nodes.comfyui_fearnworksnodes`; this is not proof that a different plugin should be installed. The real class IDs are the Drama3 names above. Do not substitute the `FishAudioTextToSpeech` class: that is the paid Comfy API integration and is unrelated to local Drama3.

## YuE2, native integration present, checkpoint missing

Live node classes `YuE2GenerateABC`, `YuE2GenerateMusic`, and `EmptyYuE2LatentAudio` are present from `comfy_extras.nodes_yue2`. The packaged primary-source template is `.venv/Lib/site-packages/comfyui_workflow_templates_json/templates/audio_yue2_text2music.json`.

Crucially, this model uses **one** `CheckpointLoaderSimple` checkpoint, `yue2_3b_int8_convrot.safetensors`, whose outputs provide the model, CLIP and VAE. The live `CheckpointLoaderSimple.ckpt_name` choices contain no Yue file. Do not require three fictitious separate weights or use the installed MiniMax Music3 as a substitute.

Graph is checkpoint -> ABC planning -> music conditioning and duration -> empty audio latent -> KSampler -> VAEDecodeAudio -> SaveAudioAdvanced. Style text lives at node `2` (`PrimitiveStringMultiline.value`), lyrics at node `3`; both feed planning and music. Seed fields are nodes `4`, `5`, `8`; max duration is node `5.max_duration`. KSampler uses the official template's 32 steps, cfg 1, dpm_2 and sgm_uniform. Default requested maximum duration is 30 seconds. This is an upper limit, not guaranteed output length.

Source references for a later explicitly authorized download are embedded in the packaged official template: `https://huggingface.co/Comfy-Org/YuE2/resolve/main/checkpoints/yue2_3b_int8_convrot.safetensors`, documented there as 3.69 GB. The link was read from the installed template, not fetched or downloaded.

## Trellis2, native integration present, five dependencies missing

All thirty classes used by the existing graph exist in live `/object_info`, including Trellis2Conditioning, structure/shape/texture stages, native VAEs, mesh postprocessing and SaveGLB. Live loader options contain none of:

| Loader field | Required basename |
| --- | --- |
| UNETLoader.unet_name | trellis_2_int8_convrot.safetensors |
| VAELoader.vae_name | trellis_2_shape_vae_bf16.safetensors |
| VAELoader.vae_name | trellis_2_texture_vae_bf16.safetensors |
| CLIPVisionLoader.clip_name | dino_v3_L_naf_fp32.safetensors |
| LoadBackgroundRemovalModel.bg_removal_name | birefnet.safetensors |

`LoadBackgroundRemovalModel` has an empty options list. Absence must be reported even though a generic validator may skip an empty list. The graph is image-to-3D; input node `1.image` must be set to an uploaded ComfyUI input. It is not text-to-3D. Geometry and texture are generated in separate stages; the final vertex-painted GLB is not a rendered PNG.

The local official template `3d_pixal3d_trellis2_image_to_model.json` uses the same stages/model filenames and contains optional Pixal3D, MoGe and texture baking paths not required by the ComfyArt graph. Do not add those optional weights as required dependencies.

## Checks and limits

Parsed all three JSON files and compared every node class, required non-dynamic input and connected output type against the live API. All node classes and connection types match. Bare Drama3 filenames are expected to fail the raw API's enum checks until the resolver supplies the folder-qualified options; actual choices above prove they are available. Yue2 and Trellis2 should remain unavailable in the UI with specific missing-file reasons. No inference from mere node presence is enough to mark either ready.

No inference was run for these newly integrated workflows. Actual audio and GLB output, duration, playback, decode, geometry and texture quality remain unverified. Physical GPU/RAM capacity was not measured in this subtask.
