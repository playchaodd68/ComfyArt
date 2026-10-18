# Use local multimodal models

This fork checks the active ComfyUI node schemas and model filenames before it enables a model. It resolves approved precision variants within each model category. It does not rename, copy, or download weights when you generate.

## Choose a model

Open **Model preferences** beside the composer. The tabs contain images, video, speech, music, and 3D. An unavailable entry shows the missing node or file. Refresh ComfyArt after you install models or custom nodes.

Automatic selection uses available models. When automatic selection is off, checked models control the Agent's choices. Manual generation can still use any installed model.

The added local paths are:

- Qwen Image 2.1 accepts the native INT8 ConvRot or BF16 diffusion weights with its dedicated encoder and VAE. Image editing uses the same resolution mechanism. Multiangle also requires its camera-angle LoRA.
- MiniMax H3 accepts the specified FL2VA and REF2VA native variants. First-frame, reference, motion, and lip-sync capabilities are checked separately. Fine-tuned hybrid checkpoints are not silently substituted.
- Krea2 Turbo uses the native Krea2 CLIP type, Qwen3-VL 4B encoder, and Qwen Image VAE. This preset generates images from text.
- Fish Audio Drama3 generates speech. To clone a voice, select a reference audio element and provide its transcript. This uses the local Drama3 nodes, not a paid Fish Audio endpoint.
- YuE2 generates music with the native combined checkpoint. Duration is a maximum, so output can be shorter.
- Trellis2 converts an input image to a GLB model with native structure, shape, and texture stages.

Use **Insert → Generate audio** for speech or music. Select an image and use **Image to 3D** for Trellis2. Audio outputs remain playable audio elements. GLB outputs remain interactive model elements.

## Configure Codex

Enable MCP and Agent in **Agent settings**, then choose **Codex**. ComfyArt uses the existing local Codex login. Keep the project open while the Agent works, because canvas tools execute in that page.

The Agent's `list_models` tool reports each modality, availability, missing dependencies, and enabled preferences. `text_to_speech`, `generate_music`, and `image_to_3d` accept an optional `model` workflow ID. For example, use `speech-drama3.api.json` for local speech and `music-yue2.api.json` for music.

## Install the optional native weights

The pinned download script prints its manifest unless you pass `--download`:

```powershell
python scripts/download_native_models.py --root 'F:\Comfy\Shared\models\main'
python scripts/download_native_models.py --root 'F:\Comfy\Shared\models\main' --download
```

Downloads remain `.part` files until their size and SHA-256 match the published manifest. Existing files with a different hash are preserved and reported as errors.

YuE2 weights use CC BY-NC 4.0. Check the individual model licenses before commercial use. Code licensing does not replace the model licenses.

## Verify an installation

```powershell
python scripts/verify_local_models.py --url http://127.0.0.1:8188
```

`READY` means the required node types, fixed enum values, and model files are available. It is a dependency check, not proof of a completed generation. The smoke script queues a real job, downloads its output, and checks the media:

```powershell
python scripts/smoke_native_models.py qwen --url http://127.0.0.1:8288
python scripts/smoke_native_models.py krea --url http://127.0.0.1:8288
python scripts/smoke_native_models.py speech --url http://127.0.0.1:8288
python scripts/smoke_native_models.py music --url http://127.0.0.1:8288
python scripts/smoke_native_models.py h3 --url http://127.0.0.1:8288
python scripts/smoke_native_models.py trellis --url http://127.0.0.1:8288 --input reference.png
```

The examples use a separate test instance. Run GPU jobs serially. The Trellis image must already exist in that instance's input directory.
