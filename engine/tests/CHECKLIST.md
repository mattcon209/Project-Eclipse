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
| 57 | Every static button is wired; favicon; Android searchPc | `test_ui_wiring.py` |
| 60–69 | Phase 2 chats: persist, pass-through, warm turns, search, persona, API | `test_chat.py` |
| 80–84 | Phase 3 stills: VAE/CLIP companions, stub PNG, unfiltered prompt, refuse non-PNG | `test_image.py` |
