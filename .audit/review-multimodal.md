# Multimodal correctness review

Read-only review of the uncommitted fork against HEAD on 2026-10-18. No generation, download, service mutation, or source edit was performed. Only this report was written. Current live `/object_info` was inspected as parsed JSON, including Drama3, YuE2, SaveAudioAdvanced and CLIPLoader. No repo-local AGENTS.md was found; the user-provided global instruction applies.

## P2: Manual image/video choices are rejected by agent-only preferences

Location: `C:/Users/Administrator/Documents/ComfyArt/src/models.ts:137-139` (new `requireModel`), called by new checks at `src/generate.ts:89` and `:131`.

`requireModel` selects from `agentModels`, which removes unchecked models when automatic selection is off. But the manual direct-generation picker deliberately lists `installedModels` (`src/ui/Composer.tsx:63-64`), and the preference explanation says the agent only uses checked models. Reproduction: disable auto, uncheck an installed image model, explicitly select that model in direct mode, then generate. The UI offers the choice but the new guard rejects it as disabled. Existing generator shapes using that model are also unable to regenerate after the preference change. Separate installed/capability validation from automatic agent selection, preserving explicit manual model choices, or consistently change both semantics and picker.

## P2: Kokoro offers a clone action that the new dispatcher always rejects

Location: `C:/Users/Administrator/Documents/ComfyArt/src/assetGen.ts:29-32`; conflicting UI at `src/ui/AudioDialog.tsx:90-92` and spec construction at `:47-50`.

With an audio shape selected and Kokoro chosen, the voice selector offers Clone selected. `spec()` creates a clone request with explicit model `speech-kokoro.api.json`, but `audioGraph` excludes exactly that ID for clone requests. Generate remains enabled, then fails; the old UI routed clone mode to IndexTTS. Restrict cloning to supported selected models, or explicitly switch to a compatible clone engine when the clone action is selected. Model switches also need to reset stale clone voice state so switching from Drama3 clone to Kokoro does not preserve an invalid request.

## P2: Dependency resolver ignores incompatible fixed enum values

Location: `C:/Users/Administrator/Documents/ComfyArt/api/model_registry.py:135-141`.

After obtaining combo choices, the resolver skips every non-model string without a recognized filename extension. This skips `CLIPLoader.type = krea2`, the distinguishing runtime capability for the new Krea2 recipe, as well as other fixed enums. A backend can therefore have the loader and all files yet be marked available and resolve successfully while `/prompt` rejects the enum. A standalone read-only reproduction imported the module with a stub CLIPLoader accepting the correct encoder filename but only `type = stable_diffusion`; resolving the Krea2 input returned `missing = []` and left `type = krea2`. Validate static non-file enum values separately, without applying filename aliases and without treating dynamic asset lists like model inventories. The current live backend does support krea2, so this is a compatibility/failure-state issue rather than a failure of today's live Krea2 schema.

## Additional capability gap

`src/botCommands.ts:241` continues advertising all H3 reference capacities when the catalog only checks the T2V recipe (`api/model_registry.py:160-178`). REF2VA uses a different diffusion checkpoint and dynamic graph. This was already broadly advertised in HEAD, so it is not counted as a newly introduced regression here, but the new capability contract should resolve first/last-frame, reference, motion and lip-sync dependencies independently. The new multiangle flag is truthful, but nothing in the direct action UI currently consumes it.

## Checked without finding a new wiring defect

- Drama3 clone uses `voices.voice0`, matching the native autogrow schema; codec/audio/transcript inputs match.
- YuE2 replaces both planning and music style/lyrics inputs with literals and sets music maximum duration; this correctly overrides the template's PrimitiveString connections.
- SaveAudioAdvanced result selection and Trellis2 result node 30 match the shipped graphs.
- Resolver model-name matching remains category-aware, rejects duplicate basenames, and honors empty native combo lists.
- No project-storage or migration edit was found in the reviewed source diff. This is not proof of an end-to-end project-load acceptance test.

Remaining verification: actual generated audio/video/GLB media, browser interaction, and external file preservation were not exercised in this read-only review.

## Re-review against 6e5cf582, 2026-10-18

The three original findings above are resolved in the inspected working tree: explicit image/video model choices now validate against installed models independently of Agent preferences; Kokoro no longer offers clone mode and model switches reset voice state; static COMBO enums are checked while input-file placeholders are exempt. H3 first-frame/reference/motion/lip-sync availability is now derived by the backend, consumed in model listings and generation guards, and reflected in the panel controls. Multiangle availability is consumed in the toolbar and Agent action.

**Current verdict: one remaining P2 manual-selection inconsistency; no P1 found.**

### P2: Manual Image-to-3D still inherits Agent exclusion

Location: `C:/Users/Administrator/Documents/ComfyArt/src/ui/ImageToolbar.tsx:202`, with dispatcher at `src/assetGen.ts:117-120` and selector at `src/models.ts:137-140`.

The toolbar makes Image to 3D visible when `installedModels('model').length > 0`, but invokes `imageTo3d` without an explicit model. This leaves `requireModel('model', undefined)` selecting from Agent-enabled models. If Trellis2 is installed and unchecked in non-auto Agent preferences, the manual toolbar action is visible but fails. Pass the explicit installed model from this manual entry point, retaining Agent-specific filtering in the Agent handler. This is the remaining narrow instance of the original manual/Agent selection issue, not a rejection of the corrected explicit-id behavior.

### Scripts and evidence

Reviewed all three new scripts. The downloader pins revisions and expected lengths/hashes, verifies existing targets, stages partials with a non-model extension, and verifies before publication. No severe defect found for the intended single invocation. The smoke runner records resolved graphs and prompt IDs, waits for result histories, and checks image/audio/video/mesh output using the appropriate decoders. No new GPU job or download was run during review.

Independently re-read the Qwen/Krea graph, history and verified reports; checked that recorded prompt IDs and submitted graphs match; recalculated output SHA-256; loaded all PNG pixels. Both are 512x512, hashes match the reports, and their saved histories record successful completed execution:

- Qwen: prompt `df638dae-aea2-4493-8abf-4c202276b85c`, SHA-256 `d5c1326ec8cc474baeaa5a3d05f2d9444c31cc496e08dbca3321721d8b3a08b3`.
- Krea: prompt `25398545-d4b9-4351-8e97-349150ff2b9c`, SHA-256 `51b185be746ac765122a1388f34df5d028095599f60a7348330a84432fd42a84`.

These prove the saved smoke artifacts and successful backend runs, not all interactive UI paths or all resolutions. Speech was pending at inspection; missing future outputs are not code-review failures. The coordinator reports 171 passing pytest tests and a passing build; this review inspected the added tests without repeating those runs.

Evidence housekeeping: `decisions.tsv` currently contains literal backslash-t sequences, so it is not yet a real tab-delimited audit trail. It has only the initial fork row. Earlier `media-backends.md` and download notes describe timestamped pre-download snapshots; append final results before handoff so those earlier missing-weight observations are not mistaken for current state. Neither point invalidates the verified PNG evidence.
