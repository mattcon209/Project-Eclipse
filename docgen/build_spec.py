#!/usr/bin/env python3
"""Fully Adaptable AI Model Software — Product & Technical Specification v1.1"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from style import (
    ACCENT, GOLD, LIGHT_TEAL, MUTED, NAVY, NEAR_BLACK, SLATE, STEEL,
    TEAL_BORDER, TEAL_LT, WHITE, banner_cell, body, bullet, callout, heading,
    kv_table, mixed, new_doc, setup_page, simple_table, spacer, state_table,
)


def build():
    doc = new_doc()
    setup_page(
        doc,
        "FULLY ADAPTABLE AI MODEL SOFTWARE",
        "Product & Technical Specification  ·  v1.6",
        "INTERNAL  ·  MattsGamingPC  ↔  Galaxy S24+  ·  Local-first",
    )

    banner_cell(
        doc,
        [
            ("PRODUCT & TECHNICAL SPECIFICATION  ·  v1.6", 10, True, False, TEAL_LT, 4, WD_ALIGN_PARAGRAPH.LEFT),
            ("Fully Adaptable AI Model Software", 22, True, False, WHITE, 6, WD_ALIGN_PARAGRAPH.LEFT),
            ("Local-first studio on a phone. Engine on a PC. Text, image, audio, video, training, LoRA — anyone can learn it.", 11, False, True, TEAL_LT, 0, WD_ALIGN_PARAGRAPH.LEFT),
        ],
    )
    spacer(doc, 10)

    kv_table(
        doc,
        [
            ("Working title", "Fully Adaptable AI Model Software  (unnamed product)"),
            ("Document type", "Product requirements + system architecture + environment baseline"),
            ("Server", "MattsGamingPC — Windows workstation, local AI backend"),
            ("Client", "Samsung Galaxy S24+ — custom Android APK (the entire UI)"),
            ("Connectivity", "Offline / local-optimized. Inference never requires WAN."),
            ("Status", "v1.6 — Atelier mockup is the UI; tap-? help cards"),
            ("Companion doc", "Hyper-Optimization Logistics & Function Manual v1.2"),
            ("Date", "15 September 2026"),
            ("Supersedes", "v1.1 (15 Sep 2026), v1.0, and v0.1 environment inventory"),
        ],
        (2.15, 4.85),
        ("Field", "Value"),
    )
    spacer(doc, 8)
    callout(
        doc,
        "GOAL",
        "Bring the difficulty of AI management, training, and accessibility down to an easy, "
        "friendly front-end client that anyone could learn to use. The phone is the studio. "
        "The PC is the engine. The user never has to touch a terminal, a Python env, a cache "
        "folder, or a model card in order to download, run, train, or talk to models.",
        bg=LIGHT_TEAL, title_color=ACCENT, border=TEAL_BORDER,
    )

    # 1
    heading(doc, "1.  Vision and Product Thesis", 1)
    mixed(
        doc,
        [
            ("A custom phone app is the only UI. ", True, False, NEAR_BLACK),
            ("It sends a signal, a message, a prompt, media, or a job to the PC. The PC detects, "
             "downloads, converts, installs, loads, generates, transcribes, speaks, trains, and stores. "
             "The phone shows results, history, libraries, and progress. Nothing important happens in a desktop window.",
             False, False, NEAR_BLACK),
        ],
    )
    heading(doc, "1.1  Design principles", 2)
    bullet(doc, "The APK is the product. The server is headless infrastructure.", bold_lead="Front-end owns UX. ")
    bullet(doc, "Chat, generate, hear, edit, train, and install must work with no public internet once models are on disk.", bold_lead="Local-first. ")
    bullet(doc, "One paste of a Hugging Face, GitHub, or other allowed link is a complete install path.", bold_lead="Link in, model in. ")
    bullet(doc, "A model loads when you enter its generation mode (or pick it). It stays resident across consecutive prompts in that mode. It unloads when you switch models or switch modes — not after every prompt, and not because you paused to look at the last result.", bold_lead="Mode-sticky residency. ")
    bullet(doc, "New model families plug in as handlers. The product is adaptable — not a wrapper around one repo.", bold_lead="Adapters, not a monolith. ")
    bullet(doc, "Quality and speed are product features, not expert flags. The engine picks a ladder (Fast / Balanced / Quality / Max) and hides the rest.", bold_lead="Profiles, not knobs. ")
    bullet(doc, "A person who has never used Hugging Face should generate an image, a voice line, and a chat reply on day one.", bold_lead="Anyone can learn it. ")
    bullet(doc, "No front-end or back-end content filters. The installed model is the only policy. Horror and unfiltered game-dev use are expected.", bold_lead="Unfiltered. ")

    heading(doc, "1.2  Who it is for", 2)
    bullet(doc, "Primary: a single operator (Matt) on MattsGamingPC + Galaxy S24+, on a home/lab LAN. Private. Not a product for other people.")
    bullet(doc, "Job of the software: supplement the operator’s game development, including horror, with local generation, training, and management.")
    bullet(doc, "Skill assumption: none beyond using a phone. Advanced controls exist behind Adjust, never required.")
    bullet(doc, "Not for: multi-tenant SaaS, cloud GPUs as the primary path, store distribution, or a moderated community.")

    heading(doc, "1.3  Success looks like", 2)
    bullet(doc, "Paste a model link on the phone → progress → the model is in the library, Ready.")
    bullet(doc, "Scroll a chat, get a streamed local reply; optionally hear it spoken; optionally talk into the mic.")
    bullet(doc, "Turn on two text models and let them talk; interrupt from the phone.")
    bullet(doc, "Generate an image, edit it, upscale it, turn a photo + prompt into a clip, or a prompt into music — same app.")
    bullet(doc, "Browse LoRAs, train a new one, attach it, without leaving the phone.")
    bullet(doc, "Ask a question about a PDF sitting on the PC. Ask a question about a photo just taken.")
    bullet(doc, "The WAN can be unplugged and none of the above, against installed models, breaks.")

    # 2
    heading(doc, "2.  Environment", 1)
    simple_table(
        doc,
        ["Role", "Name / model", "Platform", "Responsibility"],
        [
            ("Server", "MattsGamingPC", "Windows 64-bit desktop", "Store, detect, convert, install, infer, train, serve the APK"),
            ("Client", "Samsung Galaxy S24+", "Android, custom APK", "Entire UI: library, chats, audio, jobs, LoRA, training, Talk"),
            ("Link", "Local path", "LAN / hotspot / direct", "Offline-optimized. WAN only for optional model download"),
        ],
        [1.2, 1.85, 1.7, 2.25],
    )

    heading(doc, "2.1  Server — MattsGamingPC", 2)
    kv_table(
        doc,
        [
            ("Device name", "MattsGamingPC"),
            ("Processor", "AMD Ryzen 5 9600X — 6 cores / 12 threads, 3.90 GHz base, up to 5.4 GHz, 65 W, Zen 5"),
            ("Memory", "32.0 GB installed (31.1 GB usable) — treat ~24 GB as the working budget after Windows"),
            ("Primary GPU", "NVIDIA GeForce RTX 5060 Ti 16 GB — Blackwell GB206, 4,608 CUDA, 144× 5th-gen Tensor (FP8/FP4), 448 GB/s GDDR7, 180 W"),
            ("Secondary GPU", "AMD Radeon Graphics 486 MB — do not target. Pin every CUDA context to the 5060 Ti."),
            ("Storage", "954 GB total · 648 GB used · ≈306 GB free at inventory — the library ceiling until expanded"),
            ("OS", "64-bit Windows, x64"),
            ("Touch", "10-point touch reported — unused (UI is the phone)"),
            ("Device ID", "AD0B71E8-29A9-4B3B-B909-06BCE3173E6A"),
            ("Product ID", "00325-82177-54438-AAOEM"),
        ],
    )
    body(
        doc,
        "The 5060 Ti is capacity-rich (16 GB) and bandwidth-tight (128-bit bus, 448 GB/s). Hyper-optimization therefore prefers "
        "quantization, fused kernels, Tensor-core dtypes, and fewer bytes moved over “more steps.” Full playbook: companion logistics manual.",
        italic=True, color=SLATE, size=10,
    )

    heading(doc, "2.2  Client — Samsung Galaxy S24+", 2)
    kv_table(
        doc,
        [
            ("Device", "Samsung Galaxy S24+"),
            ("Software", "Custom APK — not a mobile website, not a remote-desktop shell"),
            ("Role", "The only user-facing surface. Hosts 100% of the UI."),
            ("On-device sensors", "Mic, camera, photos — first-class inputs, uploaded over LAN when a job needs them"),
            ("Does not", "Run foundation models on-device. The phone is a controller, mixer, and viewer."),
            ("Delivery", "Sideload / ADB / direct APK. Store listing is out of scope."),
        ],
    )

    heading(doc, "2.3  Hardware budget — product rules", 2)
    callout(
        doc,
        "HARD CONSTRAINTS ON THE REAL MACHINE",
        "16 GB VRAM is the generation/training ceiling. 32 GB system RAM is shared with Windows. ≈306 GB free disk is the "
        "library ceiling. The product must: (1) load one heavy pipeline at a time unless dual-text-chat both fit, "
        "(2) prefer quantized / adapter-friendly formats, (3) queue jobs instead of OOM, (4) show disk, VRAM, time, and "
        "quality-ladder cost before a download or a run, (5) train LoRA rather than full fine-tunes as the default, "
        "(6) treat video and large audio models as queued, memory-tight handlers, (7) convert models at install time "
        "into the fastest local format so runtime is cheap, (8) keep the active generation mode’s model resident "
        "across consecutive prompts — load on mode enter / model switch, not per prompt. These are product rules, not footnotes.",
    )

    # 3
    heading(doc, "3.  Architecture", 1)
    heading(doc, "3.1  Logical layout", 2)
    simple_table(
        doc,
        ["Layer", "Lives on", "What it is"],
        [
            ("Presentation", "S24+ APK", "Screens, gestures, players, logs, forms. No model math."),
            ("Client protocol", "S24+ APK", "Typed messages: prompt, command, job, media, code, cancel, subscribe."),
            ("Gateway", "PC", "Local HTTP/WebSocket bound to LAN/hotspot only."),
            ("Orchestrator", "PC", "Routes messages; owns the queue, VRAM lock, generation-mode leases, quality ladder, estimates."),
            ("Resource OS", "PC", "VRAM/RAM/disk/thermal accounting. The reason jobs don’t collide."),
            ("Handlers", "PC", "One adapter per capability. Stable detect / load / run / unload / cost."),
            ("Model library", "PC disk", "Catalog + files + converted runtimes (GGUF, TRT, FP8). Loaded as needed."),
            ("Job & chat store", "PC disk", "Histories, jobs, artifacts (image, video, audio, LoRA, docs)."),
            ("Media plane", "PC", "ffmpeg + NVENC/NVDEC. Transcode phone-sized previews without stealing the GPU job."),
            ("Acquire", "PC", "HF / GitHub / Civitai / file / NAS. The only component that may use WAN."),
            ("Calibrator", "PC", "First-run and post-driver microbench. Writes real ETAs and “will it fit” tables."),
        ],
        [1.55, 1.35, 4.1],
    )

    heading(doc, "3.2  Front-end / back-end contract", 2)
    body(doc, "The UI is fully front-end. It does not call Python. It sends one of a small set of message kinds.")
    simple_table(
        doc,
        ["Kind", "Sent by UI when…", "Back-end does"],
        [
            ("prompt", "Chat, image, edit, video, audio, talk-turn", "Run handler; stream tokens, audio, or progress"),
            ("command", "Install / load / unload / delete / attach LoRA / pin", "Mutate library or VRAM; ack + events"),
            ("job", "Train, batch, pipeline, multi-model, long audio", "Tracked job with logs, cancel, resume"),
            ("media", "Photo, mask, video, mic clip, PDF, audio file", "Accept LAN upload; bind to the job"),
            ("code", "Advanced snippet / workflow JSON", "Sandboxed handler only — never a raw OS shell"),
            ("subscribe", "Open a chat, player, or job", "Stream log, tokens, PCM, thumbnails, status"),
            ("cancel", "User stops a run", "Abort, free VRAM, mark cancelled"),
        ],
        [1.25, 2.55, 3.2],
    )

    heading(doc, "3.3  As-needed calls and adaptability", 2)
    bullet(doc, "The library is a catalog on disk, not a set of always-warm processes. Nothing loads until a generation mode needs it.")
    bullet(doc, "Once a mode is active, that mode’s selected model stays loaded across every consecutive prompt. Typical use is many images in a row, or many chat turns in a row — not a random walk across handlers. The product is built for that.")
    bullet(doc, "Unload happens on mode switch, on model switch inside a mode, or on the disconnect/sleep caveats in §3.4. Not after every prompt. Not on a short idle timer while the user is still in Image (or Chat, Audio, Video…).")
    bullet(doc, "Dual-model text is the only concurrent-model default (two text weights). Other modes hold one heavy pipeline.")
    bullet(doc, "If a load will not fit, refuse in plain language with a smaller quant / unload / queue suggestion.")
    bullet(doc, "Handlers share one interface: detect, inspect, load, run, unload, estimate_cost. New families do not require APK changes.")
    bullet(doc, "The APK knows modalities and library records, not Python class names.")

    heading(doc, "3.4  Generation modes (residency leases)", 2)
    body(
        doc,
        "A generation mode is a first-class product object, not just a tab. It is the prediction of what the user will do next. "
        "We do not need a separate ML “router model” to guess the next job — the open mode is the guess, and it is almost always right. "
        "Matt in Image mode will make another image. A chat thread will get another prompt. Design for consecutive use of one function.",
    )
    simple_table(
        doc,
        ["Mode", "Selected resident(s)", "Stays loaded until…"],
        [
            ("Chat / Text", "The thread’s text model (or A+B in multi-model)", "Leave Chats, switch the thread’s model, or start dual-model / end it"),
            ("Talk", "Tiny STT + the Talk LLM + streaming TTS (session set)", "Leave Talk"),
            ("Image", "The active T2I / image-gen pipeline + attached LoRAs", "Leave Image, or switch the image model / LoRA stack"),
            ("Edit", "The edit / inpaint pipeline", "Leave Edit, or switch the edit model"),
            ("Video", "The T2V or I2V pipeline last used in Video", "Leave Video, or switch the video model"),
            ("Audio", "The active TTS / music / SFX / enhance handler", "Leave Audio, or switch the audio model"),
            ("Documents", "Embeddings stay in RAM; LLM loads if questions are asked and then sticks", "Leave Documents, or switch the answering model"),
            ("Train", "The training stack for the running or last-configured job", "Leave Train, or the job ends and user leaves"),
        ],
        [1.45, 2.85, 2.7],
    )
    bullet(doc, "Entering a mode loads that mode’s last-selected model (if any) so the first prompt is warm when possible.", bold_lead="Enter → load. ")
    bullet(doc, "Every subsequent generate / chat / speak in that mode is a warm run. Zero load, zero unload.", bold_lead="Stay → reuse. ")
    bullet(doc, "Picking a different model in the same mode unloads the previous heavy weights, loads the new ones, and keeps the new ones for the rest of the mode session.", bold_lead="Switch model → swap. ")
    bullet(doc, "Opening a different generation mode unloads the previous mode’s heavy pipeline, then loads the new mode’s selected model. Shared light pieces (tokenizer, a tiny VAE) may be kept if they actually match.", bold_lead="Switch mode → swap. ")
    bullet(doc, "Looking at Gallery, adjusting a prompt, or waiting 30 seconds on the result screen is not a mode switch. Do not unload.", bold_lead="Pause is not exit. ")
    bullet(doc, "Background convert / TRT build / train-in-queue must not steal the active mode’s lease. They wait, or they run as CPU-only. The user’s current studio wins.", bold_lead="Mode beats background. ")
    bullet(doc, "If the APK disconnects (phone left the LAN) or Windows needs to sleep, a long idle (minutes, not a single prompt gap) may unload. Coming back to the same mode reloads once. This is the only idle-unload, and it exists so the PC can sleep overnight — not so consecutive images pay a load tax.", bold_lead="Disconnect / overnight only. ")
    bullet(doc, "Explicit Pin in Resources still exists for the rare “I will bounce Chat ↔ Image on purpose” session. Normal users should never need it, because the mode already pins for them.", bold_lead="Pin is the exception. ")
    callout(
        doc,
        "CONSECUTIVE USE IS THE PRODUCT",
        "Typical users — including the primary operator — fire the same function over and over. Image, then another image. Chat, then another turn. The engine is not allowed to treat each prompt as a fresh cold start. Load cost is paid on mode entry and on model change. Everything in between is warm.",
        bg=LIGHT_TEAL, title_color=ACCENT, border=TEAL_BORDER,
    )

    # 4
    heading(doc, "4.  Server-Side Software", 1)
    heading(doc, "4.1  Model storage", 2)
    bullet(doc, "One managed library root. Sub-libraries: Text, Image, Video, Audio, Speech, LoRA, Control, Embeddings, Datasets, Documents, Artifacts, Runtimes.")
    bullet(doc, "Each record: id, name, source URL, format, modality, disk bytes, VRAM estimate per ladder, handler, installed time, license, converted runtimes.")
    bullet(doc, "Install-time conversion writes an optimized runtime next to the original when disk allows (GGUF, FP8, TensorRT engine). Runtime path is what “Use” loads.")
    bullet(doc, "Raw files are uniquely foldered. Two repos cannot clobber each other.")

    heading(doc, "4.2  Automated detection, download, installation", 2)
    body(doc, "On install, on scan, and on first run, the backend infers what a thing is. The user is not asked to name architectures they have never heard of.")
    simple_table(
        doc,
        ["Signal", "Likely detection"],
        [
            ("GGUF / GGML", "Text LLM (llama-class) or some multimodal GGUF"),
            ("safetensors + config.json (Transformers)", "Text / VLM / speech checkpoint"),
            ("model_index.json (Diffusers)", "Image or video diffusion pipeline"),
            ("LoRA keys in safetensors / pt", "LoRA — attachable, not a base"),
            ("Encodec / vocos / bigvgan / snac + transformer", "Audio / TTS family"),
            ("Whisper / parakeet / sensevoice / wav2vec", "Speech-to-text"),
            ("CLAP / DAC / MusicGen / Stable Audio tree", "Music / SFX generation"),
            ("embedding / TEI / GTE / nomic config", "Embedding model for RAG"),
            ("ONNX / TensorRT engine", "Already-converted runtime"),
            ("Unknown", "Inbox. Client shows Identify with guesses — never a silent Ready"),
        ],
        [2.7, 4.3],
    )
    body(doc, "Paste path: Hugging Face, GitHub, Civitai (image/LoRA), direct HTTPS file, or a local/NAS folder scan. Probe size → confirm on phone if large → resume-capable download → detect → convert → catalog. Partial files never show as Ready.")
    callout(
        doc,
        "OFFLINE vs. ACQUIRE",
        "Downloading a model is the one intentional online exception. Once files are local, every generate / chat / hear / edit / train / LoRA / RAG path must run with the WAN unplugged. The APK must never block a chat behind a heartbeat.",
        bg=LIGHT_TEAL, title_color=ACCENT, border=TEAL_BORDER,
    )

    heading(doc, "4.3  Back-end handlers", 2)
    body(doc, "Handlers are the only place modality-specific code lives. Hardware notes are defaults for this box, not promises about a model the user has not installed.")
    simple_table(
        doc,
        ["Handler", "In → Out", "This hardware"],
        [
            ("Text generation", "Prompt + log → streamed tokens", "7B–14B Q4/Q5 comfortable; 32B tight; 70B no"),
            ("Vision-language", "Image + question → streamed tokens", "Load VLM instead of text; not concurrent with T2I"),
            ("Text to image", "Prompt + LoRA + size → image", "SD1.5/SDXL native; heavier T2I via quant/offload"),
            ("Image generation", "Recipe / variation / seed → image", "Same studio as T2I"),
            ("Image editing", "Image + prompt + mask → image", "Inpaint / instruct-edit"),
            ("Upscale", "Image/video → larger artifact", "Tiled; never full-frame 4K in one bite"),
            ("Control extract", "Image → depth/canny/pose/seg", "Utilities, small VRAM, cache results"),
            ("ControlNet / IP-Adapter", "Image + prompt + map → image", "Attached to T2I; counted in VRAM estimate"),
            ("Text to video", "Prompt + duration → clip", "Queued, short, reduced res"),
            ("Photo to video", "Photo + prompt → clip", "I2V; same discipline as T2V"),
            ("Video edit / V2V", "Clip + prompt → clip", "Queued; experimental on 16 GB"),
            ("Text to speech", "Text → audio", "Streaming PCM to the phone"),
            ("Speech to text", "Mic/audio → text", "Fast path for Talk mode"),
            ("Speech to speech", "Voice + target profile → audio", "Conversion / conversion+LLM"),
            ("Text to music / SFX", "Prompt → audio", "Queued; length-capped"),
            ("Audio edit / enhance", "Audio + prompt → audio", "Inpaint, denoise, separate stems"),
            ("Train (LoRA)", "Dataset + base + recipe → LoRA", "Default. Full FT often refused"),
            ("Caption / tag", "Images → captions", "Dataset prep for training"),
            ("Embed / RAG", "Docs + query → grounded answer", "Embeddings stay in RAM; LLM as-needed"),
            ("Install / detect / convert", "URL or folder → library record", "HF, GitHub, Civitai, file, NAS"),
        ],
        [1.7, 2.3, 3.0],
    )

    heading(doc, "4.4  Job system and media plane", 2)
    bullet(doc, "Every non-instant action is a job: download, convert, generate, transcribe, train, pipeline, multi-model session.")
    bullet(doc, "One GPU-heavy job at a time by default. Downloads, ffmpeg previews, and embedding ingest may run in parallel on CPU.")
    bullet(doc, "NVENC encodes phone-sized MP4/WebM; CPU/ffmpeg does audio resample and waveform peaks. Do not occupy the 5060 Ti just to make a thumbnail.")
    bullet(doc, "The phone can leave; the job continues. Crash-safe: jobs resume or mark failed, never zombie-lock VRAM.")

    heading(doc, "4.5  What the server does not do", 2)
    bullet(doc, "No required desktop control panel as the product UX. No cloud account. No jobs on the 486 MB iGPU.")
    bullet(doc, "No content classifier, no prompt rewriter, no output blocker, no safety-API call. run() does not inspect the user’s words for allowed topics.")

    # 5
    heading(doc, "5.  Client-Side APK", 1)
    heading(doc, "5.1  UI system", 2)
    bullet(doc, "The APK hosts all screens. The PC does not render UI. Results stream back. Disconnects say so in plain language.")
    bullet(doc, "Primary path on every screen is one obvious thing. Power-user parameters sit behind Adjust.")
    bullet(doc, "No unexplained acronyms on primary buttons. Non-obvious controls get a tap-? card (§18.2).")
    bullet(doc, "Errors: one sentence + a next tap. Tracebacks live under Show log.")
    bullet(doc, "Dark theme, large tap targets, one-handed chat / talk / generate.")

    heading(doc, "5.2  Information architecture", 2)
    simple_table(
        doc,
        ["Screen", "Anyone can…", "Also can…"],
        [
            ("Home", "Engine status, active mode, loaded model, last jobs, resource chips", "One-tap jump back into the last mode (still warm)"),
            ("Chats", "Scroll logged threads, send prompts", "Model pick, persona, multi-model, speak replies"),
            ("Talk", "Hold-to-talk, hear the reply", "Pick voice, interrupt, save transcript to Chats"),
            ("Create", "Image, edit, video, photo→video", "LoRA, ControlNet, upscale, quality ladder"),
            ("Audio", "TTS, music, SFX, enhance, stems", "Clone a voice the user recorded; paste lyrics"),
            ("Library", "Browse by type, tap Use, paste a link", "Delete, inspect, convert, pin, “will it fit”"),
            ("LoRA", "Toggle, strength, attach to a base", "Stack, merge, import via link or train"),
            ("Train", "Dataset + base + Start", "Caption helper, live log, output → LoRA"),
            ("Documents", "Add PDF/notes, ask questions", "Citations back into the file"),
            ("Pipelines", "Run a saved recipe (image then upscale then I2V)", "Build a chain from blocks"),
            ("Jobs", "Watch, cancel, open artifacts", "Retry failed downloads"),
            ("Gallery", "Images, video, audio in one place", "Send into Edit / Photo→Video / Enhance"),
            ("Presets", "Save a look, a voice, a sampler set", "Share as a file on LAN"),
            ("Resources", "VRAM, RAM, disk, GPU temp, ETA", "Pin, unload, quality ladder default"),
            ("Settings", "Pair, paths, HF token", "Advanced: quant, GPU device, sandbox"),
        ],
        [1.45, 2.85, 2.7],
    )

    heading(doc, "5.3  Libraries the client can actually use", 2)
    bullet(doc, "Cards show name, modality, size, loaded or not, ladder-fit badge, one primary action.", bold_lead="Models. ")
    bullet(doc, "Add = paste field (HF / GitHub / Civitai / file). Hero action of the screen.", bold_lead="Acquire. ")
    bullet(doc, "On/off, strength, trigger words, compatible-base badge, stack order.", bold_lead="LoRA. ")
    bullet(doc, "Datasets visible; caption helper; wizard defaults to a 16 GB-safe LoRA recipe.", bold_lead="Training. ")
    bullet(doc, "Voices the user recorded on this phone; never a scrape of celebrity audio.", bold_lead="Voice profiles. ")
    bullet(doc, "PDFs, notes, and folders ingested locally; answers cite chunks.", bold_lead="Documents. ")

    heading(doc, "5.4  Scrollable logged chats", 2)
    bullet(doc, "Persistent threads on the server, cached on device for reading. Infinite scroll, timestamps, model name per turn.")
    bullet(doc, "Inline media: images, waveforms, video posters. Speak-this-message uses TTS without leaving the thread.")
    bullet(doc, "Leaving the screen does not kill generation.")

    heading(doc, "5.5  Optional multi-model chats", 2)
    bullet(doc, "Default remains one model. Dual-model is a toggle: pick A and B, topic, personas, max turns.")
    bullet(doc, "VRAM must fit both (or one offloaded). Refuse before start if not. Log labels A / B / User.")
    bullet(doc, "Text models only. Image/audio/video models are not “speakers.”")

    heading(doc, "5.6  Talk mode", 2)
    body(doc, "Hold-to-talk on the S24+ → audio over LAN → STT → LLM → TTS streamed back as PCM. This is how a non-expert “uses AI” without typing. It is a pipeline of three handlers under one button, with barge-in (interrupt) and the transcript saved into Chats.")

    heading(doc, "5.7  LoRA and training (unchanged in intent, stronger in UX)", 2)
    bullet(doc, "LoRAs are first-class. Incompatible base pairings explain themselves. Training outputs land in the LoRA library automatically.")
    bullet(doc, "Caption / tag handler can build a dataset from a folder of images so training does not start with blank captions.")
    bullet(doc, "Full fine-tunes are not the default and are refused when they will not fit.")

    heading(doc, "5.8  What the APK does so the backend stays fast", 2)
    body(
        doc,
        "The phone never runs a foundation model. It does run cheap, local work that would otherwise burn the 9600X’s six cores, the LAN, or a GPU round-trip — and that finishes before a human would notice. "
        "Rule: if the user can feel it (heat, hitch, extra tap delay), it does not belong on the APK. If the PC would feel it (decode, silence audio, 12 MP HEIC, extra handler load), it does belong on the APK. Full list and measurements: logistics §7.1.",
    )
    bullet(doc, "16 kHz mono mic, on-device VAD (don’t stream silence), echo cancel so TTS isn’t transcribed, barge-in locally.", bold_lead="Talk. ")
    bullet(doc, "Orient, downscale to the model’s native size, WebP/JPEG compress, strip EXIF. Masks as small PNGs. Short clips HW-downscaled before photo-to-video.", bold_lead="Uploads. ")
    bullet(doc, "Build the recipe JSON on the phone. Debounce sliders. Seed++ locally. Empty/too-long prompt caught before a job exists.", bold_lead="Jobs. ")
    bullet(doc, "Cache thumbs, chat logs, tokenizer.json (tiny) for a live context bar. Do not re-download Gallery. Waveform peaks from incoming PCM — don’t ask ffmpeg on the PC to graph audio for the UI.", bold_lead="Cache / UI. ")
    bullet(doc, "On-device OCR (ML Kit) to fill a prompt from a photo. Optional Canny on-device for ControlNet Fast, so Image mode’s GPU lease is not stolen by an extractor.", bold_lead="Tiny vision. ")
    bullet(doc, "Diffusion, LLMs, TTS vocoders, VAE, upscale, depth/pose, training, video encode of long camera rolls, Whisper-class STT.", bold_lead="Never on the phone: ")
    callout(
        doc,
        "PHONE = SCALPEL, NOT A SECOND ENGINE",
        "The S24+ is fast at resampling, compressing, silencing, and drawing. It is the wrong place for another PyTorch. Offload is how we keep MattsGamingPC on generation instead of on chores. If an offload is noticeable on the phone, it is a bug — revert it to the PC.",
        bg=LIGHT_TEAL, title_color=ACCENT, border=TEAL_BORDER,
    )

    # 6
    heading(doc, "6.  Required Capabilities (original brief)", 1)
    body(doc, "These six remain requirements. Each has a handler, a library filter, and a Create-flow. Quality depends on the installed model — the product makes it reachable.")
    simple_table(
        doc,
        ["Capability", "User gives", "User gets", "Entry"],
        [
            ("Text generation", "Chat prompt", "Streamed reply in a logged thread", "Chats / Talk"),
            ("Image generation", "Recipe / style / seed", "New image", "Create → Image"),
            ("Text to image", "Text prompt (+ LoRA)", "New image", "Create → Image"),
            ("Image editing", "Photo + prompt (+ mask)", "Edited image", "Create → Edit"),
            ("Text to video", "Prompt + duration", "Short clip", "Create → Video"),
            ("Photo to video", "Photo + prompt + duration", "Short clip", "Create → Photo→Video"),
        ],
        [1.55, 1.85, 1.85, 1.75],
    )
    body(doc, "T2I and “image generation” share one studio so the user is not taught two words for one place. Cross-cutting: seed + model + LoRAs + ladder stored with every artifact. Originals are never silently overwritten. The product does not filter, classify, or refuse prompts or outputs for content. Horror, gore, and anything else the operator generates for private game development is in-bounds. Built-in model alignment is the model’s problem, not a front-end feature.")

    # 7 NEW
    heading(doc, "7.  Extended Model Types", 1)
    body(doc, "v1.1 adds the families a real studio needs after text and pictures. Each is a handler. None is a cloud API. If the matching model is not installed, the screen says so and offers paste-link — it does not fake a result.")

    heading(doc, "7.1  Audio and speech", 2)
    simple_table(
        doc,
        ["Type", "User gives", "User gets", "Notes"],
        [
            ("Text to speech", "Text, optional voice profile", "Spoken audio, streamable", "Chat speak-button + Audio studio"),
            ("Speech to text", "Mic or file", "Transcript, timestamps", "Talk mode + captions for video"),
            ("Speech to speech", "Recording + target voice", "Converted / translated speech", "User-recorded profiles only"),
            ("Voice profile", "A short reading the user records", "A reusable local voice", "Consented, on-device capture"),
            ("Text to music", "Prompt, duration, mood", "Music bed", "Length-capped; queued"),
            ("Text to SFX / Foley", "Prompt", "Sound effect", "Short clips, Gallery-audio"),
            ("Audio continue / inpaint", "Audio + prompt + region", "Edited audio", "Analog of image inpaint"),
            ("Enhance / denoise", "Messy recording", "Cleaner audio", "Podcast / voice cleanup"),
            ("Stem split", "Mix", "Vocals / drums / other", "Utility for music LoRA data"),
        ],
        [1.6, 1.9, 1.7, 1.8],
    )
    body(doc, "Audio artifacts play in Gallery with a waveform. The phone mic is a first-class input. Sample-rate and loudness are normalized by the media plane so the user never picks 44.1 vs 48.")

    heading(doc, "7.2  Seeing, reading, and documents", 2)
    simple_table(
        doc,
        ["Type", "User gives", "User gets"],
        [
            ("Vision-language (VLM)", "Photo + question", "Grounded answer in a chat"),
            ("Caption / OCR / image-to-text", "Image or folder", "Caption, tags, or extracted text"),
            ("Documents (RAG)", "PDF, notes, folder + question", "Answer with citations, offline"),
            ("Embeddings", "(internal)", "Vectors for search and RAG"),
            ("Translation", "Text or speech", "Text or TTS in the target language"),
        ],
        [2.3, 2.2, 2.5],
    )

    heading(doc, "7.3  Image / video utilities (the difference between a toy and a studio)", 2)
    simple_table(
        doc,
        ["Type", "Why it exists"],
        [
            ("Upscale (image, video)", "Quality ladder Max is mostly “generate then upscale,” not “native 4K in 16 GB.”"),
            ("Frame interpolation", "Make short video less choppy after a low-FPS generate."),
            ("Background remove / segment", "Prep for edit, composite, or training crops."),
            ("Depth / pose / canny / normal", "ControlNet inputs, auto-extracted, cached."),
            ("ControlNet + IP-Adapter", "“Use this sketch / this face / this composition” without prompt luck."),
            ("Video to video / video edit", "Prompt-change an existing clip. Experimental; queued; may refuse."),
            ("3D (experimental)", "Image-to-mesh if a small model fits. Hidden behind Experimental until it does."),
        ],
        [2.3, 4.7],
    )

    heading(doc, "7.4  Tool-using text models", 2)
    body(doc, "A text (or VLM) model may call other handlers through a tiny tool router: generate_image, speak, transcribe, search_docs, upscale. The user sees those calls as labeled steps in the log, can deny a call, and never watches a raw function dump. This is how “write a scene and show me the still and read it aloud” becomes one prompt instead of three screens.")

    heading(doc, "7.5  What we will not ship as features", 2)
    bullet(doc, "On-device foundation inference on the S24+ as the engine.")
    bullet(doc, "Bundled celebrity voice packs. Voice profiles are ones the operator records. This is a default library choice, not a prompt filter.")
    bullet(doc, "Any content filter, now or later. See §8.13.")

    # 8 NEW features
    heading(doc, "8.  Features the Product Needs (beyond the brief)", 1)
    body(doc, "These are not extras for a later fantasy version. They are the difference between “a pile of models with a UI” and software a human will still use in a month. Each is in scope for the product; phases in §15 say when.")

    heading(doc, "8.1  Quality ladders (Fast / Balanced / Quality / Max)", 2)
    body(doc, "One control, four rungs, everywhere generate happens. The engine maps the rung to steps, resolution, quant, distilled vs full, upscale pass, vocoder, and bitrate. The user does not pick a sampler. Details live in the logistics manual. Default: Balanced. Last choice is remembered per modality.")

    heading(doc, "8.2  Pipelines / recipes", 2)
    body(doc, "Saved chains: prompt → image → upscale → photo-to-video; or STT → LLM → TTS; or caption folder → train LoRA → attach → T2I. Built from blocks the user already understands. A pipeline is a job with a progress list.")

    heading(doc, "8.3  “Will it fit?” and live resources", 2)
    bullet(doc, "Every Use / Download / Train shows disk, VRAM, and a calibrated ETA before it starts.")
    bullet(doc, "Home and Resources show VRAM, RAM, disk, GPU temp, loaded model, queue depth.")
    bullet(doc, "First-run calibrator writes actual numbers for this 5060 Ti, not a generic table.")

    heading(doc, "8.4  Smart acquire and convert", 2)
    bullet(doc, "Download only the shards the handler needs. Prefer already-quantized files when the ladder is Fast/Balanced.")
    bullet(doc, "After download, convert once (GGUF / FP8 / TRT) in a background job. Use that runtime forever after.")
    bullet(doc, "Scan existing folders: Hugging Face cache, Comfy, Automatic1111, Ollama, a NAS share.")
    bullet(doc, "Allowed sources: HF, GitHub, Civitai, direct file, local folder. Size-gate before the first byte.")

    heading(doc, "8.5  Presets, prompts, personas, compare", 2)
    bullet(doc, "Prompt library, system-prompt / persona library, per-model defaults, “last 20 prompts.”")
    bullet(doc, "Save a look (LoRAs + ladder + size) as a Preset. Apply in one tap.")
    bullet(doc, "Compare: two images, two answers, or two voices side by side, same seed when it applies.")

    heading(doc, "8.6  Engine reliability", 2)
    bullet(doc, "Watchdog restarts a dead engine. Windows sleep is blocked while a job runs. Sleep may proceed after a long disconnect even if a mode was active — the mode reloads on return.")
    bullet(doc, "Jobs are crash-safe. Generation-mode residency is the default pin (see §3.4). Manual Pin is only for cross-mode hopping.")
    bullet(doc, "Optional Windows auto-start so the phone just works when Matt walks in.")
    bullet(doc, "Local notification on the phone when a long job (train, video, download) finishes.")

    heading(doc, "8.7  Reproducibility, backup, licenses", 2)
    bullet(doc, "Every artifact stores seed, model id, LoRAs, ladder, params, source job.")
    bullet(doc, "Offline model card (parsed README + license) on the library sheet.")
    bullet(doc, "Export / backup: catalog + selected weights + chats to an external drive. Restore is a first-class job.")
    bullet(doc, "Gated HF repos: optional token in Settings, set from the phone, stored on the PC.")

    heading(doc, "8.8  Dataset and LoRA craft", 2)
    bullet(doc, "Captioner, crop/face-focus helper, dedupe, and a “is this enough data?” estimate before train.")
    bullet(doc, "LoRA stack (multiple, ordered) and optional merge (new library item) so runtime stays one file.")
    bullet(doc, "Compatibility matrix: this LoRA × this base = OK / maybe / no.")

    heading(doc, "8.9  LAN media that feels instant", 2)
    bullet(doc, "Thumbnails and waveform peaks first; full media on tap. Phone-sized transcodes, not 40 MB PNG over Wi-Fi.")
    bullet(doc, "Streaming tokens and streaming PCM. Time-to-first-byte is a KPI, not an accident.")

    heading(doc, "8.10  Search, tags, favorites", 2)
    bullet(doc, "Search chats, prompts, and gallery tags. Favorite models and presets sit on Home.")

    heading(doc, "8.11  Handler SDK", 2)
    body(doc, "A documented adapter interface so a new family (a new video backend, a new vocoder) can be dropped in without an APK change. v1 ships the handlers in §4.3; the SDK is how “fully adaptable” stays true after v1.")

    heading(doc, "8.12  Health of the machine (not content)", 2)
    bullet(doc, "Thermal throttle awareness, 90% disk warning, pagefile/OOM guard, “this download is larger than free space.” These protect hardware. They are not content policy.")
    bullet(doc, "Code messages never become PowerShell. URL allowlists for acquire (https to HF/GitHub/Civitai) so a pasted link cannot become an arbitrary fetch. Not a prompt filter.")

    heading(doc, "8.13  No content filters — locked", 2)
    body(doc, "Personal, private, horror-inclusive game-dev studio. No product-level censor, classifier, or refusal of prompts/outputs. Models may have their own alignment; swap the model rather than wrap it. “Refuse” means VRAM/disk only.")

    # 9
    heading(doc, "9.  Connectivity — Offline / Local Optimized", 1)
    bullet(doc, "Gateway binds to LAN/hotspot only. APK default endpoint is local (MattsGamingPC or paired IP).", bold_lead="Local bind. ")
    bullet(doc, "Auth, CDN, crash reporters, license phones must not block use when WAN is down.", bold_lead="No WAN gate. ")
    bullet(doc, "Media designed for LAN. If the phone leaves, the UI fails clearly — no cloud retry loop.", bold_lead="Honest disconnect. ")
    bullet(doc, "Pairing: same Wi-Fi, QR or one-time code, then auto-reconnect. Fallbacks: PC hotspot, phone hotspot, USB debug.", bold_lead="Pair once. ")
    bullet(doc, "HF/GitHub/Civitai need internet on the PC, not necessarily on the phone. Offline PC → install job waits and explains.", bold_lead="Acquire exception. ")

    # 10
    heading(doc, "10.  Data, Privacy, Security", 1)
    bullet(doc, "Weights, chats, datasets, LoRAs, images, video, audio, and documents live on MattsGamingPC unless exported.")
    bullet(doc, "The phone holds UI state, pairing secrets, thumbnails, and a cache of recent logs.")
    bullet(doc, "No cloud sync. No Google/Microsoft login. Pairing = LAN possession + one-time code.")
    bullet(doc, "Device ID and Product ID are asset metadata, never APK secrets.")
    bullet(doc, "Voice profiles are user-recorded. Delete is real delete.")
    bullet(doc, "Gateway on local interfaces only. No UPnP, no auto-tunnel, no ngrok by default.")
    simple_table(
        doc,
        ["Store", "Contents", "Client view"],
        [
            ("Library catalog", "Models, LoRAs, voices, datasets, handlers, runtimes", "Library / LoRA / Audio"),
            ("Chat store", "Threads, turns, tool calls, timestamps", "Chats / Talk transcripts"),
            ("Job store", "Downloads, gens, trains, pipelines, logs", "Jobs"),
            ("Artifact store", "Images, video, audio, exports", "Gallery"),
            ("Document index", "Chunked PDFs, embeddings", "Documents"),
            ("Settings", "Pairing, paths, ladders, token, pin", "Settings / Resources"),
        ],
        [1.7, 2.8, 2.5],
    )

    # 11
    heading(doc, "11.  Key User Flows", 1)
    heading(doc, "11.1  First hour", 2)
    body(doc, "Install APK → engine auto-starts or Start engine → pair on Wi-Fi → Home shows connected → paste a small text-model link → Ready → Chats → type a sentence → reply. Optionally tap Speak. If this needs a README beyond those steps, the UI failed.")
    heading(doc, "11.2  Paste-to-installed", 2)
    body(doc, "Library → Add → paste → size/modality/ladder-fit guess → confirm → job log → convert → Ready → Use. Failures resumable.")
    heading(doc, "11.3  Image → edit → video", 2)
    body(doc, "Create → Image → Gallery → Edit → Photo→Video. Each step a new artifact. No Python repo names.")
    heading(doc, "11.4  Two models talk", 2)
    body(doc, "Chats → Multi-model → A/B → topic → Start. Interrupt / steer / Stop. VRAM check first.")
    heading(doc, "11.5  Train a LoRA", 2)
    body(doc, "Folder or link → optional captioner → New training → default recipe → Start → LoRA card → attach → generate.")
    heading(doc, "11.6  Talk", 2)
    body(doc, "Talk → hold → speak → transcript flashes → voice reply streams. Saved to Chats.")
    heading(doc, "11.7  Ask a PDF", 2)
    body(doc, "Documents → add file (LAN) → ingest job → ask → answer with citations. Works offline after ingest.")
    heading(doc, "11.8  One prompt, three handlers", 2)
    body(doc, "In Chats, with tools on: “Describe this photo, make a still in that style, and read the description.” Log shows see → image → speak as steps.")

    # 12
    heading(doc, "12.  Non-Goals (v1)", 1)
    bullet(doc, "Cloud GPU offload or “if local fails, call a paid API.”")
    bullet(doc, "Play Store listing, MDM, multi-user accounts.")
    bullet(doc, "A required desktop GUI, or cloning every Comfy node in v1.")
    bullet(doc, "Guaranteed 70B dense text, native long 1080p video, or full fine-tunes of large image models on 16 GB.")
    bullet(doc, "Automatic disk expansion. If the library is full, the product says so and stops.")
    bullet(doc, "Making two video or audio models “talk.” Multi-model is a text feature.")
    bullet(doc, "Impersonation packs. Experimental 3D is hidden until it fits.")

    # 13
    heading(doc, "13.  Risks", 1)
    simple_table(
        doc,
        ["Risk", "Why it’s real", "Mitigation"],
        [
            ("Disk cliff", "~306 GB free", "Size-gate; convert only if room; cleanup from phone; warn at 80%"),
            ("16 GB VRAM", "VLM + T2I + video cannot coexist", "Resource OS; one heavy job; ladders; pin/unpin"),
            ("448 GB/s bus", "LLM decode is bandwidth-bound", "Quants, FP8/FP4, fused kernels — see logistics manual"),
            ("6 CPU cores", "ffmpeg + tokenize + Windows", "NVENC for video; cap CPU jobs; don’t CPU-offload diffusion"),
            ("Video / music ambition", "Huge checkpoints", "Queued; short defaults; honest empty states"),
            ("Detection misses", "GitHub repos are messy", "Inbox + handler pick; never silent Ready"),
            ("Gated HF / Civitai auth", "Tokens, rate limits", "Token in Settings; plain “this repo is gated”"),
            ("Windows lifecycle", "Sleep, drivers, CUDA", "Watchdog; block sleep on jobs; pin NVIDIA GPU"),
            ("Unfriendly power", "Samplers, quants, vocoders", "Ladders + tooltips + Adjust drawer"),
            ("Scope", "“Fully adaptable” can mean everything", "Stable handler interface; v1 = listed handlers, not the zoo"),
        ],
        [1.45, 2.35, 3.2],
    )

    # 14
    heading(doc, "14.  Open Questions", 1)
    simple_table(
        doc,
        ["ID", "Question", "Default if unspecified"],
        [
            ("Q-01", "Product / APK display name?", "Working title until named"),
            ("Q-02", "Text backend preference?", "Handler-abstracted; GGUF + one Transformers path"),
            ("Q-03", "Image backend preference?", "Diffusers first; Comfy headless as a later adapter"),
            ("Q-04", "Starter pack of small models?", "Empty library + paste-link; optional later pack"),
            ("Q-05", "Default quality ladder?", "Balanced"),
            ("Q-06", "Engine auto-start on logon?", "Yes, user-level"),
            ("Q-07", "Civitai in v1 acquire?", "Yes, for image/LoRA; HF+GitHub remain primary"),
            ("Q-08", "Talk mode barge-in latency target?", "Under ~500 ms after speech end, calibrated"),
            ("Q-09", "Mask editor?", "Simple brush only in v1"),
            ("Q-10", "Code-message sandbox?", "Disabled until a handler exists; no raw shell"),
            ("Q-11", "3D handler visible?", "Experimental flag, off by default"),
            ("Q-12", "HF / Civitai token UX?", "Optional, stored on PC, set from APK Settings"),
        ],
        [0.85, 2.9, 3.25],
    )

    # 15
    heading(doc, "15.  Delivery Plan", 1)
    body(doc, "The goal is the full product. Phases exist so the engine and the friendliness bar are real before every handler is lit. Each phase is usable alone. The logistics manual’s optimization work starts in Phase 0, not as a late polish.")
    simple_table(
        doc,
        ["Phase", "Ships", "Done when"],
        [
            ("0  Foundation", "Engine, pairing, APK shell, Jobs, Resources, watchdog, calibrator", "Phone shows live status + real VRAM on MattsGamingPC"),
            ("1  Library & acquire", "Storage, detect, paste-install, convert job, scan folders", "Paste a link → Ready card, with size gate"),
            ("2  Text", "LLM handler, logged chats, as-needed load, personas, search", "Offline chat; history survives app kill"),
            ("3  Image", "T2I, image gen, edit, Gallery, LoRA attach, upscale, ControlNet", "Prompt → image → edit → upscale on the phone"),
            ("4  Audio", "TTS, STT, music/SFX, enhance, voice profiles, Gallery audio", "Type a line, hear it; record a voice, use it"),
            ("5  Talk & tools", "Talk mode, multi-model text, tool router", "Hold-to-talk works; two models converse"),
            ("6  Train", "Training library, captioner, LoRA wizard, stack/merge", "A LoRA trained from the APK is usable"),
            ("7  Video", "T2V, photo-to-video, interpolation, queued clips", "A still + prompt becomes a clip"),
            ("8  Documents & pipelines", "RAG, VLM chat, saved recipes", "Ask a PDF; run image→upscale→I2V as one job"),
            ("9  Polish", "Ladders felt, empty states, one-handed pass, backup", "New user completes §11.1 with no instructor"),
        ],
        [1.55, 2.75, 2.7],
    )

    heading(doc, "15.1  Definition of done", 2)
    bullet(doc, "Original six capabilities plus audio/speech, Talk, RAG, upscale, ControlNet, pipelines — all reachable from the APK.")
    bullet(doc, "HF / GitHub / Civitai paste installs without desktop file wrangling.")
    bullet(doc, "Chats logged and scrollable. Multi-model optional. LoRA and training first-class.")
    bullet(doc, "WAN unplugged: chat / generate / hear / train against installed models still works.")
    bullet(doc, "VRAM and disk exhaustion produce refusals a non-expert can act on.")
    bullet(doc, "No happy-path step requires a monitor, keyboard, or terminal on the PC (beyond one-time engine start if auto-start is off).")
    bullet(doc, "Ten images in a row in Image mode cause one load (mode enter), not ten. Same for chat turns in Chat mode.")

    # 16
    heading(doc, "16.  Brief Traceability", 1)
    simple_table(
        doc,
        ["Brief item", "Where it lives"],
        [
            ("Fully adaptable AI model software", "§1, §3.3, §8.11"),
            ("Model storage / handlers / detect-download-install", "§4.1–§4.3"),
            ("Library with as-needed calls", "§3.3, §4.1"),
            ("Front-end calls as specified", "§3.2"),
            ("APK library / scrollable chats / multi-model", "§5.3–§5.5"),
            ("HF or GitHub paste automation", "§4.2, §8.4 (Civitai added)"),
            ("Client LoRA + training library", "§5.7, §8.8"),
            ("UI fully front-end; signals to back-end", "§3.2, §5.1"),
            ("Image / text / T2I / edit / T2V / photo-to-video", "§6"),
            ("Offline / local optimized", "§9"),
            ("Anyone could easily learn it", "§1, §5.1, §11.1, Phase 9"),
            ("Audio and other model types (v1.1)", "§7"),
            ("Features beyond the brief (v1.1)", "§8"),
            ("Generation-mode sticky residency (v1.2)", "§3.4"),
            ("Client-side offload (v1.3)", "§5.8  ·  logistics §7.1"),
            ("No content filters (v1.4)", "§8.13, §4.5, §7.5, §12"),
            ("Visual language + game-dev extras (v1.5)", "§18–§19  ·  ui_mockup/index.html"),
            ("Hyper-optimization", "Companion logistics manual"),
        ],
        [3.4, 3.6],
    )

    heading(doc, "17.  Locked Constraints vs. Open Decisions", 1)
    state_table(
        doc,
        [
            ("Locked", "Server is MattsGamingPC (9600X, 32 GB, 5060 Ti 16 GB / 448 GB/s, ~954 GB disk)."),
            ("Locked", "Client is Galaxy S24+ custom APK — the entire UI lives there."),
            ("Locked", "PC is the engine. Connection is local-first. WAN is only for optional acquire."),
            ("Locked", "Mode-sticky residency: load on mode enter / model switch; consecutive prompts in a mode stay warm. Paste-link install. Scrollable chats. Optional dual-text talk."),
            ("Locked", "LoRA and training are first-class. Original six modalities are requirements."),
            ("Locked", "Audio/speech, Talk, RAG, upscale, ControlNet, pipelines, ladders, calibrator are in-product."),
            ("Locked", "Voice profiles are user-recorded. No impersonation packs."),
            ("Locked", "Friendliness is a requirement. Quality ladders hide expert flags."),
            ("Locked", "No content filters on APK or engine. Unfiltered personal/horror game-dev use. Machine health ≠ moderation."),
            ("Locked", "Atelier mockup (ui_mockup/index.html) IS the front-end. OLED black, copper, canvas-first. Tap-? help cards on non-obvious controls."),
            ("Locked", "Projects + watched export folder + variation grid + same-as-last. Game-dev extras in §19."),
            ("Open", "Consumer product name and visual brand."),
            ("Open", "Exact handler implementations (abstracted; Q-02 / Q-03)."),
            ("Open", "Whether a starter model pack ships."),
            ("Open", "Exact pairing UX (QR vs. code vs. scan) — any novice-finishable local method."),
        ],
    )

    heading(doc, "18.  Visual language — it should look like it belongs to you", 1)
    body(
        doc,
        "This is a private instrument. That is more reason to make it beautiful, not less. "
        "The APK must not look like Automatic1111, a Material You chat app, or a purple neon “AI” dashboard. "
        "It should feel like a title card and a camera: quiet chrome, loud pictures. "
        "The operator signed off on the mockup: ui_mockup/index.html is the front-end. "
        "Working name on the glass: Atelier. If a screen is uglier or busier than that mockup, the screen is not done.",
    )
    heading(doc, "18.1  Locked look", 2)
    bullet(doc, "OLED near-black (#070708). The generated image is the light source. Chrome recedes.", bold_lead="Black. ")
    bullet(doc, "One accent: oxidized copper (#C45C38). Tungsten gold (#C4A574) only for the wordmark. Live/engine = muted sage. No rainbow, no purple glow.", bold_lead="Copper. ")
    bullet(doc, "Georgia (or a bundled Fraunces/Newsreader) for the wordmark and project titles. System UI for chrome. Mono for seed / model / VRAM.", bold_lead="Type. ")
    bullet(doc, "Canvas is 70%+ of Image/Edit/Video. Tabs, ladders, and Make sit in a thin instrument cluster.", bold_lead="Canvas first. ")
    bullet(doc, "Film-stock overlay on the picture: model · lora · seed · ladder. Craft, not mystery.", bold_lead="Stock line. ")
    bullet(doc, "Button copy: Make, Talk, Enhance — not Generate / Submit / Execute.", bold_lead="Short words. ")
    bullet(doc, "Material You / wallpaper tinting off. This palette is the product, including at noon.", bold_lead="No wallpaper theme. ")
    bullet(doc, "One spring, 120 Hz, no bounce-for-fun. Haptic on job complete. Sound off by default.", bold_lead="Motion. ")
    bullet(doc, "Empty states: a ruled frame and one line. No cartoon robot, no confetti.", bold_lead="Empty. ")
    bullet(doc, "Custom icon + splash. Recents thumbnail can show the last still (it’s private).", bold_lead="Icon. ")
    heading(doc, "18.2  Question-mark help (tap to learn)", 2)
    body(
        doc,
        "Every non-obvious control gets a small “?” blip. Tap it, read one short card, dismiss. "
        "This is how a person who has never used Hugging Face learns LoRA, seed, ladder, and tileable without a manual. "
        "The help is part of the look: italic Georgia “?” in a copper-thin circle — not a blue Material tooltip, not a first-run slideshow that blocks Make.",
    )
    bullet(doc, "A 16 px circle, 1 px tungsten/copper ring, italic ?. Sits on the label, never on the canvas.", bold_lead="Looks. ")
    bullet(doc, "Tap → a dark card: title + 2–4 sentences in human language + Got it + Don’t show this one. No links to docs sites.", bold_lead="Tap. ")
    bullet(doc, "One card at a time. Never a modal stack. Never auto-play. First session may softly pulse the ladder ? and the LoRA ? once, then stop.", bold_lead="Quiet. ")
    bullet(doc, "Copy is the product: “A LoRA is a small add-on that teaches this model a style, a place, or a person. Attach it like a filter; strength is how hard it pushes.”", bold_lead="Words. ")
    bullet(doc, "Required blips: ladder, seed, LoRA, pin, Enhance, tileable, cast lock, watched folder, Talk barge-in, VRAM chip, Fast vs Max.", bold_lead="Where. ")
    bullet(doc, "Don’t show this one is remembered per blip, on device. There is no “reset all tutorials” buried five menus deep — it’s in Settings as Reset help cards.", bold_lead="Memory. ")
    bullet(doc, "Help never rewrites a prompt and never blocks Make. If the user never taps ?, the app still works.", bold_lead="Optional. ")

    heading(doc, "19.  Game-development extras (recommended — this is why the studio exists)", 1)
    body(
        doc,
        "The operator will use this to make a game, often horror. These are not generic AI-app features. "
        "They should be in v1 unless they threaten the friendliness bar. Engine-agnostic (Unity / Unreal / Godot): we export files, we do not plugin-lock.",
    )
    simple_table(
        doc,
        ["Feature", "Why", "v1?"],
        [
            ("Projects (e.g. Hollow)", "Gallery, LoRAs, prompts, voices, and export paths don’t mix between games.", "Yes"),
            ("Watched folder on the PC", "Drop PNGs into the Unity/Unreal project from Make. The phone never files things by hand.", "Yes"),
            ("Export recipes", "PNG+alpha, 2K tile, sprite, 48 kHz WAV, loopable bed. One tap, named files: warden_idle_003.png.", "Yes"),
            ("Seamless / tileable toggle", "Materials. Circular padding or dedicated seamless pass. Horror walls are 90% tile.", "Yes"),
            ("Variation grid 2×2 / 3×3", "Consecutive Image-mode use. Same prompt, seeds++. Pick one, Enhance.", "Yes"),
            ("Same as last", "One control that restages model, LoRA, size, ladder, seed-lock.", "Yes"),
            ("Cast / reference lock", "A character bible: face/body stills used as IP-Adapter / ref. The Warden stays the Warden.", "Yes"),
            ("Turnaround pipeline", "Front / side / back from a locked cast still. Recipe, not a prayer.", "Yes if Image is already shipping"),
            ("Prompt chips (authorable)", "User-made chips: 35mm, wet concrete, first-person, fog. Not a public prompt dump.", "Yes"),
            ("Seed lock + filmstrip", "Last N stills under the canvas. Tap to restore that recipe.", "Yes"),
            ("Alpha / sprite extract", "BG-remove into a game-ready cutout. Goes to the watched folder.", "Yes (utility handler)"),
            ("Loopable audio + markers", "SFX one-shots and music beds with a loop point. Game audio, not a song demo.", "With Audio phase"),
            ("Voice lines batch", "Paste a list of NPC lines → same voice profile → numbered WAVs in the project folder.", "With Audio phase"),
            ("Color match / LUT", "Match a still to the game’s grade so concept art doesn’t look from another movie.", "Quality/Max path"),
            ("Normal/height from still", "Cheap utility for materials. Honest about quality. Better than nothing for blockout.", "Optional"),
            ("Pixel / limited palette", "Only if a project needs it. Hidden until then.", "No, unless asked"),
        ],
        [2.0, 3.6, 1.4],
    )
    heading(doc, "19.1  Other recommendations (small, high leverage)", 2)
    bullet(doc, "A 2×2 grid is worth more than another sampler. Build it early in Image phase.")
    bullet(doc, "Home is Resume, not a dashboard of charts. One project, last mode, still warm.")
    bullet(doc, "Keep a paper sketch of the APK in the mockup file. If a new screen needs a legend, it is too busy.")
    bullet(doc, "Do not add a node graph in v1. Pipelines as a short list of blocks is enough.")
    bullet(doc, "Do not add a public model storefront. Paste-link remains the acquire path.")
    bullet(doc, "Do not auto-post anywhere. Export is a folder on MattsGamingPC.")

    heading(doc, "20.  Appendix — Raw Inventory", 1)
    kv_table(
        doc,
        [
            ("Device name", "MattsGamingPC"),
            ("Processor", "AMD Ryzen 5 9600X 6-Core Processor (3.90 GHz)"),
            ("Installed RAM", "32.0 GB (31.1 GB usable)"),
            ("Graphics card", "NVIDIA GeForce RTX 5060 Ti (16 GB)"),
            ("Graphics card (2)", "AMD Radeon(TM) Graphics (486 MB)"),
            ("Storage", "648 GB of 954 GB used"),
            ("Device ID", "AD0B71E8-29A9-4B3B-B909-06BCE3173E6A"),
            ("Product ID", "00325-82177-54438-AAOEM"),
            ("System type", "64-bit operating system, x64-based processor"),
            ("Pen and touch", "Touch support with 10 touch points"),
            ("Client", "Samsung Galaxy S24+ · Custom APK Build"),
            ("Connectivity (original)", "Offline/local optimized connection"),
        ],
        header=("Field", "As originally supplied"),
    )

    spacer(doc, 14)
    banner_cell(
        doc,
        [
            ("END OF SPECIFICATION  ·  v1.6", 11, True, False, WHITE, 4, WD_ALIGN_PARAGRAPH.CENTER),
            ("Companion: Hyper-Optimization Logistics & Function Manual v1.2", 10, False, True, TEAL_LT, 0, WD_ALIGN_PARAGRAPH.CENTER),
        ],
    )

    out = "/home/user/Project_Technical_Specification.docx"
    doc.save(out)
    print("Wrote", out)


if __name__ == "__main__":
    build()
