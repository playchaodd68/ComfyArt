# Missing native ComfyUI model files

Read-only evidence collected 2026-10-18. Hugging Face repository metadata and anonymous HEAD requests were used. No weight bodies were downloaded, no paid API used and no server restarted.

## Recommended files for the current workflows

The pinned links below match the exact native workflow filenames. Sizes and SHA-256 come from Hugging Face LFS metadata, not rounded UI estimates.

| Native category / file | Bytes | GiB | Pinned download URL | SHA-256 |
| --- | ---: | ---: | --- | --- |
| `checkpoints/yue2_3b_int8_convrot.safetensors` | 3,960,938,800 | 3.689 | [download](https://huggingface.co/Comfy-Org/YuE2/resolve/2f76ca75e6ee094169de899cc7fc99d6887e2196/checkpoints/yue2_3b_int8_convrot.safetensors) | `96fe199377309001ed8cd26a944baeee8cc31a20ba7c36d1d3c0a7e1f4149db6` |
| `diffusion_models/trellis_2_int8_convrot.safetensors` | 5,253,048,192 | 4.892 | [download](https://huggingface.co/Comfy-Org/TRELLIS.2/resolve/430a9d09b2416687018c8fe8edced2ad4858a439/diffusion_models/trellis_2_int8_convrot.safetensors) | `d01952ad137213f6a868f86b6b877026276f84af5eec23069217475a0bad3a31` |
| `vae/trellis_2_shape_vae_bf16.safetensors` | 1,095,844,024 | 1.021 | [download](https://huggingface.co/Comfy-Org/TRELLIS.2/resolve/430a9d09b2416687018c8fe8edced2ad4858a439/vae/trellis_2_shape_vae_bf16.safetensors) | `de0cb4949a76c59ee5c091a995a69bcc8c51d5aeda939f0c641a50d2a72341f4` |
| `vae/trellis_2_texture_vae_bf16.safetensors` | 948,461,364 | 0.883 | [download](https://huggingface.co/Comfy-Org/TRELLIS.2/resolve/430a9d09b2416687018c8fe8edced2ad4858a439/vae/trellis_2_texture_vae_bf16.safetensors) | `714e5ebf094a610e12a8e3b5175c18a62f37f6ea4218acb6073644456b73ab0e` |
| `clip_vision/dino_v3_L_naf_fp32.safetensors` | 1,215,214,176 | 1.132 | [download](https://huggingface.co/Comfy-Org/Pixal3D/resolve/f37641be376725d324c56626007cc477f1249a69/clip_vision/dino_v3_L_naf_fp32.safetensors) | `4ad2ec4e0879a5b5b04cd97325cc37da954a7b6edca5170b86510f17f2b2290f` |
| `background_removal/birefnet.safetensors` | 444,473,596 | 0.414 | [download](https://huggingface.co/Comfy-Org/BiRefNet/resolve/25511f8787e51912e1480706b4e47b8f467fbf72/background_removal/birefnet.safetensors) | `9ab37426bf4de0567af6b5d21b16151357149139362e6e8992021b8ce356a154` |

YuE2 total is **3,960,938,800 bytes (3.961 GB, 3.689 GiB)**. It is a single CheckpointLoaderSimple file supplying MODEL, CLIP and VAE. SheetSage2 is only needed for music-cover transcription and is not required for the text-to-music graph.

Trellis2's five-file total is **8,957,041,352 bytes (8.957 GB, 8.342 GiB)**. If the existing local BiRefNet weights can be reused after validation, the transfer falls by 444,473,596 bytes. There is no need for Pixal3D's generator or MoGe for this graph. Only its DINO L_NAF vision weights are referenced by the current template.

## Access and license metadata

- [Comfy-Org/YuE2](https://huggingface.co/Comfy-Org/YuE2) at `2f76ca75e6ee094169de899cc7fc99d6887e2196` reports private=False, gated=False, license=`cc-by-nc-4.0`.
- [Comfy-Org/TRELLIS.2](https://huggingface.co/Comfy-Org/TRELLIS.2) at `430a9d09b2416687018c8fe8edced2ad4858a439` reports private=False, gated=False, license=`mit`.
- [Comfy-Org/Pixal3D](https://huggingface.co/Comfy-Org/Pixal3D) at `f37641be376725d324c56626007cc477f1249a69` reports private=False, gated=False, license=`mit`.
- [Comfy-Org/BiRefNet](https://huggingface.co/Comfy-Org/BiRefNet) at `25511f8787e51912e1480706b4e47b8f467fbf72` reports private=False, gated=False, license=`mit`.

YuE2's source [m-a-p/YuE2-3B](https://huggingface.co/m-a-p/YuE2-3B) also identifies its weights as CC BY-NC 4.0. Preserve that noncommercial restriction; repository code licensing does not replace the weight license. Trellis2's source [microsoft/TRELLIS.2-4B](https://huggingface.co/microsoft/TRELLIS.2-4B) states MIT. The original DINOv3 source [facebook/dinov3-vitl16-pretrain-lvd1689m](https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m) has its own terms/access flow; the Comfy-Org repack metadata alone is not a blanket statement about every upstream component's license.

Anonymous HEAD status, without reading response bodies:
- `checkpoints/yue2_3b_int8_convrot.safetensors`: `200`.
- `diffusion_models/trellis_2_int8_convrot.safetensors`: `200`.
- `vae/trellis_2_shape_vae_bf16.safetensors`: `200`.
- `vae/trellis_2_texture_vae_bf16.safetensors`: `200`.
- `clip_vision/dino_v3_L_naf_fp32.safetensors`: `200`.
- `background_removal/birefnet.safetensors`: `200`.

## What is already on the machine

1. The current server's `/object_info` returns no matching native choices for CheckpointLoaderSimple (YuE2), UNETLoader (Trellis2), VAELoader (Trellis2), CLIPVisionLoader (DINO), or LoadBackgroundRemovalModel (BiRefNet). `F:/Comfy/Shared/models/main/background_removal` contains only `put_background_removal_models_here`. The shared extra-model-paths map already registers this native category.
2. **BiRefNet weights do physically exist** at `F:/Comfy/Shared/models/main/RMBG/RMBG-2.0/model.safetensors`, 884,878,856 bytes, SHA-256 `566ed80c3d95f87ada6864d4cbe2290a1c5eb1c7bb0b123e984f60f76b02c3a7`. The file's header includes `bb.layers.1.blocks.0.attn.relative_position_index`, the exact key tested in native `comfy/bg_removal_model.py:load_background_removal_model`. It is a credible local reuse candidate, not proven load/inference success. The existing RMBG path is not in native `background_removal`, explaining why other custom background-removal tools may work while this native loader lists nothing. Do not rename/delete the source. A link or separate category entry plus a real loader test could avoid downloading BiRefNet.
3. **Original Trellis2 weights also physically exist** under `D:/AI/trellis/code/MODELS/hub/models--microsoft--TRELLIS.2-4B/snapshots/af44b45f2e35a493886929c6d786e563ec68364d/ckpts`. Files include sparse-structure flow, separate 512/1024 shape and texture flows, shape decoder and texture decoder. A TRELLIS-image-large snapshot beside it supplies the sparse-structure decoder. `D:/AI/trellis/code/MODELS/dinov3/model.safetensors` is 1,212,559,808 bytes; its config says DINOv3ViTModel, 1024 hidden size, 24 layers, 16px patches and 4 register tokens. `D:/AI/trellis/code/MODELS/RMBG-2.0/model.safetensors` is another background-removal copy.
4. Those original Trellis2 flow files have unprefixed state-dict keys such as `adaLN_modulation.1.weight`. Native ComfyUI model detection instead expects merged keys `img2shape.t_embedder.mlp.0.weight`, `shape2txt.t_embedder.mlp.0.weight`, and submodel prefixes. Its shape-VAE detector expects `shape_dec.blocks.1.16.to_subdiv.weight`; the original separate decoder is unprefixed. Merely changing filenames will not adapt these weights. Local conversion and validation is an alternative to downloading the repacks, but was not performed in this read-only task.
5. Searches covered registered F:/Comfy/Shared model trees, the active ComfyUI models directory, D:/Comfy and the D:/AI installation. No native Yue2 file was found there. This does not claim an exhaustive search of all drives or NAS storage.

## Alternative files and precise scope

The same Comfy-Org/TRELLIS.2 revision publishes `clip_vision/dino_v3_vit_l.safetensors` (1,212,559,776 bytes) and `diffusion_models/trellis_2_bf16.safetensors` (10,338,297,616 bytes). The current combined Pixal3D/Trellis2 template specifically selects DINO L_NAF from Pixal3D and INT8 ConvRot, so changing to either alternative requires an explicit compatibility check. Do not download both precision variants by default.

The locally installed primary template sources are `.venv/Lib/site-packages/comfyui_workflow_templates_json/templates/audio_yue2_text2music.json` and `3d_pixal3d_trellis2_image_to_model.json` under the active ComfyUI root. Their declared dependency URLs agree with the current pinned file inventory. HTTP metadata proves file availability, not model execution or output quality.
