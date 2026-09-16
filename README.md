# Project Eclipse

Local-first AI studio. **Atelier** (Galaxy S24+ APK) talks to a headless engine on **MattsGamingPC**. Spec: `docs/`.

## Phase 0 (now)

Engine + pairing + live resources + jobs + Atelier shell. Image **Make** is honest: it will not fake a picture until a model is installed.

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
| `engine/atelier/` | Phase 0 Atelier UI served by the engine |
| `atelier-android/` | Kotlin Compose APK source |
| `ui_mockup/` | Signed-off visual direction |
| `docs/` | Spec v1.6 + logistics manual |
| `docgen/` | Regenerates the Word docs |

No content filters. Mode-sticky residency is in the orchestrator (swap on mode change only).
