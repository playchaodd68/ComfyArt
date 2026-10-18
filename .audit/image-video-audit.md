# Local image and video integration audit

Audited on 2026-10-18. Read-only inspection against the live ComfyUI at `http://127.0.0.1:8188`, installed source at `F:/Comfy/Installations/ComfyUI D/ComfyUI`, model headers and shared workflows. No inference was queued and no installed files or running processes were changed. Added the standalone Krea2 graph in this fork after coordinator authorization.

Throughput checkpoint: n/a, read-only investigation.

## Main conclusion

Qwen Image 2.1 and native MiniMax H3 graphs can retain their existing structure. Their model roles must resolve to available variants and required node capabilities must be checked. Krea2 needs a new graph with its own CLIP type, not a renamed Qwen graph. File existence does not prove a particular inference path has completed.

## Available candidates and suggested priority

Paths below are names returned by the live `/models/<category>` API, relative to the corresponding model category.

| Role | Preferred | Fallback |
| --- | --- | --- |
| Qwen Image 2.1 diffusion | `Qwen Image 2.1\qwen_image_2.1_bf16.safetensors` | No other native 2.1 variant is exposed locally |
| Qwen Image 2.1 encoder | `qwen3vl_8b_int8_convrot.safetensors` | `qwen3vl_8b_bf16.safetensors` |
| Qwen Image 2.1 VAE | `qwen_image_2.1_vae_bf16.safetensors` | None required |
| H3 FL2VA diffusion | `MiniMax H3\minimax_h3_fl2va_int8_convrot.safetensors` | `MiniMax H3\minimax_h3_fl2va_bf16.safetensors` |
| H3 REF2VA diffusion | `MiniMax H3\minimax_h3_ref2va_int8_convrot.safetensors` | `MiniMax H3\minimax_h3_ref2va_bf16.safetensors` |
| H3 encoder | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `qwen3vl_32b_minimax_h3_int8_convrot.safetensors`, then BF16 |
| H3 video VAE | `minimax_h3_video_vae_fp16.safetensors` | Keep existing canonical VAE; do not substitute TRT assets by filename |
| H3 audio VAE | `minimax_h3_audio_vae_fp32.safetensors` | None required |
| Krea2 diffusion | `Krea2\krea2_turbo_fp8_scaled.safetensors` | `Krea2\krea2_turbo_bf16.safetensors`, then `Krea2\krea2_turbo_int8_convrot.safetensors` |
| Krea2 encoder | `qwen3vl_4b_fp8_scaled.safetensors` | `qwen3vl_4b_bf16.safetensors` |
| Krea2 VAE | `qwen_image_vae.safetensors` | `krea2RealVae_v10.safetensors` exists but is a user variant, not an automatic equivalent |

The Krea2 INT8 file is served by the live model API but physically resides in the configured legacy model tree. Prefer the main-tree FP8 or BF16 assets. Keep model-role aliasing category-aware to prevent equal basenames in different model categories colliding.

## Qwen Image 2.1

The local main model header reports 14,230,280,616 bytes, BF16 `img_in.weight` with shape `[4096,64]`, and 265 tensors. The native `QwenImage21` model and `TextEncodeQwenImage21` node exist in the live runtime.

Resolve the canonical `qwen_image_2.1_int8_convrot.safetensors` token in all four recipes, not just the top-level model menu:

- `workflows/qwen-image-2.1-t2i.api.json`
- `workflows/edit-qwen-image-2.1.api.json`
- `workflows/outpaint-qwen-image-2.1.api.json`
- `workflows/multiangle-qwen-image-2.1.api.json`

Keep CLIPLoader type `qwen_image`. The 2.1 path is selected from the encoder architecture. Keep the dedicated 2.1 VAE. Existing editing/cache wiring is correct for the installed native nodes. `TextEncodeQwenImage21` has flattened dynamic inputs such as `images.image_1`; the apparent absence of a literal `images` input is normal, including empty-reference text generation.

`creativeUpscaleGraph`, `expandGraph`, `editGraph`, `styleGraph`, `touchGraph` and `anglesGraph` all use these recipes, so resolving only the main generation recipe is incomplete.

The camera-angle LoRA `qwen-image-2.1-qma-camera-angles.safetensors` is absent from the live LoRA inventory. Gate multiangle capability on that dependency; do not substitute a Krea2 or Qwen Image 2511 LoRA. Qwen Image Layered is a distinct capability and must remain unavailable unless its own model and VAE are present.

## MiniMax H3

The two local INT8 models are full, unpruned native H3 checkpoints. Both headers specify 50 transformer layers, hidden size 5376, text dimension 5120, 24 video latent channels, 32 audio latent channels, and time embedding dimension 2688. `time_embedder.proj_in.weight` is `[5376,256]`; `time_embedder.proj_out.weight` is `[2688,5376]`. Neither header uses `adaln_t_table`.

Native `comfy/model_detection.py` detects full versus curve-pruned models from tensors, not filenames. A local full checkpoint can therefore fill the existing FL2VA/REF2VA model roles without editing sampler wiring or inventing a fake filename. Do not automatically substitute custom hybrids, VDN or FastH3 models.

All node classes referenced by the three shipped H3 recipes exist in the live API. The optional missing literal `values` input on `ComfyMathExpression` is normal because recipes supply `values.a`.

Dimensions must remain multiples of 32. The native frame grid is `17k+5` at 24 fps. Upstream's math expression correctly rounds up to that grid. The runtime describes 124 to 362 frames as its training range. A five-second request resolves to 124 frames, approximately 5.17 seconds. A very short smoke run may use 22 or 39 frames, but that is outside the documented training range and cannot establish normal quality.

The vanilla shipped mode has its turbo switch disabled and uses 20 steps. That is the safest initial validation mode. The turbo branch previously picked 6 steps although the selected LoRA is named 8-step. With coordinator authorization, changed only the turbo step constant to 8 in `t2v-minimax-h3.api.json` node 138 and `i2v-minimax-h3.api.json` node 105:125. The REF2VA recipe has no such turbo switch. The local generic and 768p 8-step LoRA headers both identify `Comfy-Org/MiniMax-H3 minimax_h3_fl2va_bf16.safetensors` as their base and rank 128. Their header target dimensions match the full local checkpoints. Curve-pruned-specific LoRAs and full-model LoRAs are not interchangeable by filename; keep this choice explicit.

`motionGraph` separately requires `minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors`, which is not exposed in the model-patch inventory. Do not present motion-control as available merely because H3 generation is available. First/last frame and reference generation are separate native supported capabilities.

## Krea2

Added `workflows/krea2-turbo-t2i.api.json`. Required classes are `UNETLoader`, `CLIPLoader`, `VAELoader`, `EmptySD3LatentImage`, `CLIPTextEncode`, `KSampler`, `VAEDecode`, `SaveImage`. Every class is live. It uses 10 Euler/simple steps, CFG 1, and default 1024 square output.

The local BF16 and FP8 headers both have `first.weight` `[6144,64]` and `txtfusion.projector.weight` `[1,12]`. Native model detection identifies Krea2 from the `txtfusion` projector. Its CLIP type must be `krea2`, which extracts a 12-layer stack from Qwen3-VL-4B. Using `qwen_image` would select the wrong conditioning layout. The local native model uses Wan21's 16-channel latent format; `EmptySD3LatentImage` constructs a compatible initial tensor and avoids relying on implicit channel conversion.

The graph's IDs deliberately align with the existing standard KSampler generation path. Model metadata should use prompt `text`, seed `[7,seed]`, sizes `[5]`, VAE `4`, and 10-step default. Do not set `refs: 'latent'` because `src/refModes.ts` hardcodes Flux graph IDs and its model behavior. Krea2 reference/edit mode uses distinct local custom nodes and often a task LoRA; simply turning on the current Flux latent-reference branch would fail.

Local shared Krea2 editing recipes use `Krea2EditGroundedEncode` plus `Krea2EditModelPatch` with the identity edit LoRA. Style-reference recipes use `TextEncodeKrea2OstrisEdit` plus `Krea2OstrisEditModelPatch` and `krea2_style_reference.safetensors`. Those are separate future capabilities, not implied by the new text-to-image graph.

## Verification options

- Structural live-schema check. Resolve category-aware model names, verify every class exists, every fixed COMBO value is listed, every link's node/output exists, and every non-dynamic required input is present. This performs no generation.
- Qwen smoke. Clone `qwen-image-2.1-t2i.api.json`, resolve main model, set node 5 to 256 square, node 6 prompt to `A red ceramic cup on a white table, studio photograph`, node 7 to one step and fixed seed. Queue and inspect saved PNG. Then run a normal 1024/25-step image for usable-quality acceptance.
- Krea2 smoke. Same 256 square/one-step substitutions in its new recipe, then normal 1024/10 steps. One-step output checks execution only.
- H3 smoke. Clone `t2v-minimax-h3.api.json`, use full INT8, force turbo=false, remove duration math and set node 131 to 320x192 with length=22, set 137 to one step. Expect low quality outside the training range. Normal acceptance should use 1344x768, 124 frames, vanilla 20 steps or verified 8-step turbo. Check both video and non-silent audio, plus full decode. Coordinate GPU use before either run.

No smoke generation was queued by this audit. The coordinator owns scheduling and final rendered-output verification.

## Evidence locations

### Z-Image VAE follow-up

The missing canonical `ae.safetensors` can resolve to `z_image_ae.safetensors`, with `flux-ae.safetensors` as a fallback. Both local files are byte-identical: 335,304,388 bytes and SHA256 `AFC8E28272CD15DB3919BACDB6918CE9C1ED22E96CB12C4D5ED0FBA823529E38`. Both headers identify `Flux.1-AE`, with encoder output `[32,512,3,3]` and decoder input `[512,16,3,3]`, matching the 16-channel Flux latent format inherited by native `ZImage` through `Lumina2`. The existing local Z-Image workflow already points to `z_image_ae.safetensors`. This is an evidenced alias, not an arbitrary renamed VAE. No source or model files were renamed.

- Live `/models/diffusion_models`, `/models/text_encoders`, `/models/vae`, `/models/loras`, `/object_info`.
- Installed `comfy/model_detection.py` around lines 390-420 and 1010-1025.
- Installed `comfy/supported_models.py` around lines 1988-2015 and 2074-2101.
- Installed `comfy/text_encoders/krea2.py`.
- Local shared `01_图像/图像工具｜Qwen Image 2.1.json`, `图像编辑-综合｜Krea2.json`, `图像编辑-风格参考｜Krea2.json`, `角色四视图｜Krea2.json`.

Memory was used only to locate the active installation and shared workflow root. Those paths and relevant assets were reverified live. Registry pointer is `MEMORY.md:259-262`, rollout `01a14a8f-cfe3-7571-b24f-a3c37d6da5f7`.
