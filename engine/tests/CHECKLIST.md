# Optimization boxes (backend)

Run from `engine/`:

```
python -m pytest tests -v
```

| Box | Contract | Test |
|---|---|---|
| 01 | Mode-sticky residency; consecutive prompts do not reload | `test_box01_*` |
| 02 | First byte before done | `test_box02_*` |
| 03 | Disk size-gate | `test_box03_*` |
| 04 | VRAM refuse-early (hardware, not content) | `test_box04_*` |
| 05 | Ladders change VRAM estimate | `test_box05_*` |
| 06 | One heavy job; second queues | `test_box06_*` |
| 07 | No content filter; prompt pass-through | `test_box07_*` |
| 08 | Long disconnect is the only idle unload | `test_box08_*` |
| 09 | No model → no fake picture | `test_box09_*` |
| 10 | Reload KPI = 1 per enter + 1 per model switch | `test_box10_*` |
| 11 | Calibrator writes inventory | `test_box11_*` |
| 12 | Watchdog heartbeat | `test_box12_*` |
| 13 | Pairing | `test_box13_*` |
| 14 | Jobs create/cancel | `test_box14_*` |
| 15 | Resources snapshot shape | `test_box15_*` |
| 16–20 | HTTP API: health, status, UI, auth, no content 403 | `test_api.py` |
| 21 | Make is honest and unfiltered | `test_box21_*` |
| 22 | KPI endpoint is paired | `test_box22_*` |
| 30–51 | Library, detect, allowlist, size-gate, paste→Ready, scan, Use | `test_library.py` |
| 52–56 | Search this PC + Ollama blobs | `test_box52_*`–`test_box56_*` |
| 70–74 | Comfy checkpoints / extra_model_paths / GameAI; Wan in diffusion_models is Video; AI-Video-Server portable | `test_box70_*`–`test_box74_*` |
| 57 | Every static button is wired; favicon; Android searchPc | `test_ui_wiring.py` |
| 60–69 | Phase 2 chats: persist, pass-through, warm turns, search, persona, API | `test_chat.py` |
| 80–88 | Phase 3 stills: VAE/CLIP companions, stub PNG, unfiltered prompt, refuse non-PNG, AIO checkpoint, seed, nested ckpt names, Qwen hybrid CLIP | `test_image.py` |
| 89 | Image canvas strip keeps stills; tap restores; no Gallery tab | `test_box89_*` |
| 90–93 | Delete still PNG, Enhance next ladder, Qwen edit graph, SD img2img | `test_box90_*`–`test_box93_*` |
| 94–100 | Phase 6 Train: probe folder, refuse Qwen/Flux, stub catalogs LoRA, production never fakes | `test_train.py` |
| 101–111 | Phase 7 Video: LTXV/Hunyuan/Wan graphs, still→clip, stub webp, production never fakes; Comfy sees Search paths; Wan VAE not taesdxl | `test_video.py` |
