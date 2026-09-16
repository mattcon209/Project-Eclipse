# Eclipse engine (Phase 0)

Headless local backend. Atelier (the APK, and this lab UI) talks to it on the LAN.

```
cd engine
pip install -r requirements.txt
python run.py
```

Binds `0.0.0.0:7740`. Open `http://<pc>:7740` for the Phase 0 Atelier shell (lab). The Android app in `atelier-android/` is the product UI.

Pairing: the engine prints a 6-digit code. The phone (or lab UI) sends it once and stores a token.

No content filters. GPU readout uses `nvidia-smi` (present on MattsGamingPC; absent in some lab boxes).
