# Project Eclipse

Local-first AI studio. **Atelier** (Galaxy S24+ APK) talks to a headless engine on **MattsGamingPC**. Spec: `docs/`.

## Phase 2 (now)

Logged chats + GGUF text handler (Ollama if it’s running, else llama-cpp-python). History lives on the PC. Image **Make** is still honest until Phase 3.

Library (Phase 1): paste-link acquire + Search this PC.

```bash
cd engine
pip install -r requirements.txt
python run.py
```

Open `http://<pc>:7740` — Atelier lab UI (same look as the signed-off mockup). Pair with the 6-digit code printed in the terminal.

Android product shell: `atelier-android/` (build in Android Studio on the PC).

## Layout

| Path | What |
|---|---|
| `engine/` | Python FastAPI engine (`0.0.0.0:7740`) |
| `engine/atelier/` | Atelier lab UI served by the engine |
| `atelier-android/` | Kotlin Compose APK source |
| `ui_mockup/` | Signed-off visual direction |
| `docs/` | Spec v1.6 + logistics manual |
| `docgen/` | Regenerates the Word docs |

No content filters. Mode-sticky residency is Resource OS (swap on mode or model change only). Long disconnect (~12 min) is the only idle unload.

```
cd engine && python -m pytest tests -v
```
