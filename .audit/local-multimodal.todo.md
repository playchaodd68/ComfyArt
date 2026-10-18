# Local multimodal adaptation

- [x] Read the Principles section of poteto-mode.
- [x] Phase A: Frame. Fork upstream and inspect the live installation without modifying it.
- [x] Phase B: Design the workflow. Compare model binding and modality designs against live node schemas.
- [x] Phase C: Run the loop. Implement and verify independently reviewable units.
- [x] Capture baseline model/node availability and workflow validation.
- [x] Bind Qwen Image 2.1, MiniMax H3 and Krea2 to compatible local model variants.
- [x] Integrate Drama3 speech, Trellis2 3D and Yue2 music with honest dependency status and output handling.
- [x] Verify built frontend, unit/integration tests and real available model outputs.
- [x] Phase D: Keep the audit trail. Record evidence and unresolved model/runtime constraints.
- [x] Phase E: Verify and hand back. Independent review, branch push, PR and safe live integration.

Done means the fork contains the adaptation, the UI and Codex tools expose actual supported capabilities, compatible installed models generate validated outputs, and missing dependencies are explicit instead of falsely marked available. No paid downloads, upstream merges, or overwriting the running plugin without a recoverable backup.

Throughput checkpoint: model/node discovery and frontend inspection run independently; GPU generation runs serially against an idle queue.
