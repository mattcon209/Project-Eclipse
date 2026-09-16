# Eclipse engine (Phase 2)

Headless local backend. Atelier (the APK, and this lab UI) talks to it on the LAN.

Chat: Use a Ready text card, then **Chat → Send**. Tokens stream. Threads persist in `data/chats.json`. Runtime is Ollama on `127.0.0.1:11434` when those models were found on disk, otherwise llama-cpp-python against the GGUF path. No fake replies if neither is up.

```
cd engine
pip install -r requirements.txt
python run.py
```

Binds `0.0.0.0:7740`. Open `http://<pc>:7740` for the Atelier shell (lab). Library → **Search this PC** (HF cache, Ollama, LM Studio, Downloads — files stay on disk) or paste a link. The Android app in `atelier-android/` is the product UI.

Pairing: the engine prints a 6-digit code. The phone (or lab UI) sends it once and stores a token.

No content filters. GPU readout uses `nvidia-smi` (present on MattsGamingPC; absent in some lab boxes).

Optimization boxes (Resource OS, mode-sticky residency, refuse-early, pass-through):

```
python -m pytest tests -v
```
