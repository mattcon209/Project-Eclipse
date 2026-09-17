# Eclipse engine (Phase 3)

Headless local backend. Atelier talks to it on the LAN.

Chat: Use a Ready text card, then **Chat → Send**. Tokens stream. Threads persist in `data/chats.json`. Runtime is Ollama on `127.0.0.1:11434` when those models were found on disk, otherwise llama-cpp-python against the GGUF path. No fake replies if neither is up.

Image: Use a Ready T2I card, then **Image → Make**. ComfyUI on `127.0.0.1:8188` runs the graph. AIO checkpoints load as one file. UNET-only Qwen Edit checkpoints take MODEL from the ckpt and CLIP/VAE from `models/vae` + `models/text_encoders`. Nothing is faked if CLIP/VAE are missing.

```
cd engine
pip install -r requirements.txt
python run.py
```

Binds `0.0.0.0:7740`. Open `http://<pc>:7740` for the Atelier shell (lab). Library → **Search this PC** (HF cache, Ollama, LM Studio, ComfyUI including `extra_model_paths.yaml`, Downloads — files stay on disk) or paste a link.

Pairing: the engine prints a 6-digit code. The phone (or lab UI) sends it once and stores a token.

No content filters. GPU readout uses `nvidia-smi` (present on MattsGamingPC; absent in some lab boxes).

```
python -m pytest tests -v
```
