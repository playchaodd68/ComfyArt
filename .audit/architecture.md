# Local model integration architecture

Status: selected design implemented in the frontend; backend and runtime verification are coordinated by the root agent. Existing workflow IDs, project schemas, media shapes, and original model files stay compatible.

## Grounding

The installed model picker previously checked only diffusion filenames from a fixed image/video list. `api/models.py` supplied a global basename map, while `src/comfy.ts` rewrote every matching string before queueing. This could mistake an identically named asset in a different model category and did not verify text encoders, VAEs, loaders, or optional control models.

Image generation is built in `src/generate.ts`, with family-specific workflow JSON and metadata in `src/models.ts`. H3 builders live in `src/workflows.ts` and dynamically alter the text/image/reference graphs. The application already supports audio and 3D: `src/assetGen.ts` builds graphs, `src/jobs.ts` resumes jobs and extracts result references, and `src/shapes/EmbedShapes.tsx` supplies audio playback and an interactive mesh viewer. The `audio` and `3d` history keys were already recognized by `waitForImages`; new model support does not require inventing new output shape types.

Codex calls tool declarations from `api/mcp_tools/canvas.py`. Python forwards canvas commands through the Comfy websocket; the open page runs `src/botCommands.ts` against the actual editor and uses the same generation path as the direct UI. Thus availability enforcement belongs below both the UI and tools rather than inside only one caller.

Live `/object_info` on port 8188 exposed native Krea2, H3, YuE2, Trellis2 and Drama3 classes. Local main-weight variants include Qwen Image 2.1 BF16, Krea2 BF16/FP8/int8, and H3 FL2VA and Ref2VA variants. Node registration alone is not proof that all associated weights are installed. Separate backend checks own these conclusions.

## Two candidate designs

### A. Frontend variant aliases

Extend each `ModelDef` with alternate filenames and node requirements. Fetch `/object_info` and every `/models/<category>` endpoint in the browser, then rewrite loader inputs there. This adds fewer server endpoints but duplicates Comfy's local category knowledge in JavaScript and exposes selection policy to every builder. The existing category-blind basename mapper becomes difficult to retire, and Python tests cannot directly cover frontend resolution. Rejected for split ownership of dependency resolution.

### B. Backend capability catalog and graph resolver (selected)

Keep frontend descriptions and graph-editing metadata, while the Python boundary owns local dependency resolution. `GET /comfyart/model-catalog` returns current status and chosen loader bindings; `POST /comfyart/resolve-workflow` validates and resolves the exact graph immediately before submission. All ComfyArt workflows, including generated H3 variants and existing edit tools, use that single boundary. Missing or ambiguous dependencies produce a useful error before `/prompt` is queued.

This concentrates category knowledge and installed-node validation in one module without introducing a new execution service, new project schema, or new asset type.

## Selected contract

```ts
type ModelModality = 'image' | 'video' | 'speech' | 'music' | 'model'
interface ModelStatus {
  id: string                 // stable workflow filename; old IDs remain valid
  available: boolean         // true only after all mandatory dependencies resolve
  missing: string[]          // actionable node/file/category diagnoses
  capabilities: Record<string, unknown>
}

// GET /comfyart/model-catalog
{ version: 1, models: Array<ModelStatus & {
  label: string
  modality: ModelModality
  bindings: Record<string, Record<string, string>>
}> }

// POST /comfyart/resolve-workflow
{ graph: PromptGraph, model_id?: string } -> { graph: PromptGraph }
// Failure: HTTP 400 { error: string, missing: string[] }
```

The catalog defines dependency readiness, not a claim that a completed output has been generated. Agent selection additionally enforces user preferences. Before catalog load, models are unverified and unavailable; no automatic fallback to an absent model exists. Explicit manual model selection validates installed dependencies independently of Agent preferences; Agent tools validate both availability and the Agent's enabled list.

Category-aware bindings affect loader fields, never prompt text. Approved variants must be explicit; a similarly named edit model cannot be substituted for a text-to-image model. Resolution re-runs at submission because the catalog could be stale. The legacy `/model-paths` endpoint is retained for compatibility; new `queuePrompt` no longer invokes the global string replacement.

## Frontend and tool ownership

- `src/models.ts`: all five modality groups, catalog parsing/status, automatic/manual preference selection, useful missing-dependency errors. Existing image/video metadata and workflow IDs remain the graph builder's contract.
- `src/ui/ModelPrefs.tsx`: derives tabs/rows from model groups and reports exact missing dependencies.
- `src/assetGen.ts`: reuses existing audio/model placers. Drama3 locates typed generate/codec/save nodes and supports a reference transcript for voice cloning. YuE2 binds style, lyrics, duration ceiling and random seeds. Legacy Kokoro, IndexTTS, ACE Step and Stable Audio builders remain available if their dependencies are present.
- `src/ui/AudioDialog.tsx`: offers available model selection and the Drama3 reference transcript when cloning; no fabricated voice list for Drama3.
- `src/botCommands.ts`: exposes every modality's statuses through `list_models`; existing generation tools gain optional model choice. `api/mcp_tools/canvas.py` documents these compatible additions.
- `src/comfy.ts`: resolve the final graph before `/prompt`; preserve existing media history extraction.
- `src/generate.ts`, `src/ui/Composer.tsx`: handle an empty available model set safely and fail before generation when a saved preference refers to an absent/disabled model.

## Compatibility and verification

No project shape migration is needed. Audio remains `ca-audio`, 3D remains `ca-model`, generated images/videos retain their assets, and saved image/video workflow IDs retain their meaning. No model files are renamed, copied, or downloaded by this design.

Backend tests should cover category collision, compatible explicit alternatives, missing loader/encoder/VAE, unknown node, no arbitrary prompt replacement, failed resolver never queueing, and stale catalog revalidation. Frontend verification must cover five tabs, unavailable reasons, strict manual preferences, model choice in audio generation, and generated output playback/mesh loading. Typecheck and production build passed after the frontend integration. Actual generation and result decoding remain a separate acceptance gate; missing Trellis2/YuE2 weights must stay unavailable rather than be described as tested.

## Accepted deviations during implementation

The request initially assumed audio and 3D needed new output types, but source inspection showed the upstream fork already implements them. The selected design reuses those types and placers. Drama3 and YuE2 use `SaveAudioAdvanced`, not only `SaveAudio`; builders accept both native saver classes. Krea2 uses its own no-reference template and VAE node 4 rather than inheriting Flux reference assumptions. These changes preserve the shared contract and reduce scope.

Independent review follow-up: hide unsupported Kokoro voice cloning, derive H3 first-frame/reference/motion/lip-sync capabilities from backend status with unknown values treated as unavailable, and hide unavailable multiangle/3D/animation toolbar entries. Generation checks the same H3 feature status before building a graph. Retained graphs with unsupported modes remain editable but cannot submit until their inputs/mode are changed.
