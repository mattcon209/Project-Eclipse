# Project Eclipse

Local-first AI studio. **Atelier** talks to a headless engine on **MattsGamingPC**. Spec: `docs/`.

## Phase 3 (now)

Logged chats + GGUF text handler (Ollama if it’s running, else llama-cpp-python). Image **Make** runs the Qwen stack and AIO checkpoints already on disk through local ComfyUI (`--lowvram`). UNET-only Qwen Edit files load CLIP + VAE from disk. No fake stills. Audio / Talk / Video are later phases.

Library: paste-link acquire + Search this PC.

On MattsGamingPC keep the repo **off OneDrive**:

```powershell
cd "C:\Project Eclipse"
git pull
py run.py
```

Binds `0.0.0.0:7740`. `run.bat` in the repo root does the same.

Open `http://<pc>:7740` — Atelier lab UI (same look as the signed-off mockup). Pair with the 6-digit code printed in the terminal.

## Layout

| Path | What |
|---|---|
| `engine/` | Python FastAPI engine (`0.0.0.0:7740`) |
| `engine/atelier/` | Atelier lab UI served by the engine |
| `atelier-android/` | Kotlin Compose APK source (Phase 1 shell) |
| `ui_mockup/` | Signed-off visual direction |
| `docs/` | Spec v1.6 + logistics manual |
| `docgen/` | Regenerates the Word docs |

No content filters. Mode-sticky residency is Resource OS (swap on mode or model change only). Long disconnect (~12 min) is the only idle unload.

```
cd engine && python -m pytest tests -v
```
