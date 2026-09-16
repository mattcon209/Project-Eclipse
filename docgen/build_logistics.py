#!/usr/bin/env python3
"""Hyper-Optimization Logistics & Function Manual v1.0"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from style import (
    ACCENT, GOLD, LIGHT_TEAL, NEAR_BLACK, SLATE, STEEL, TEAL_BORDER,
    TEAL_LT, WHITE, banner_cell, body, bullet, callout, heading, kv_table,
    mixed, new_doc, setup_page, simple_table, spacer,
)


def build():
    doc = new_doc()
    setup_page(
        doc,
        "HYPER-OPTIMIZATION  ·  LOGISTICS & FUNCTION",
        "Highest quality, fast, on MattsGamingPC  ·  v1.2",
        "INTERNAL  ·  Companion to Product Spec v1.2  ·  Local-first",
    )

    banner_cell(
        doc,
        [
            ("LOGISTICS & FUNCTION MANUAL  ·  v1.2", 10, True, False, TEAL_LT, 4, WD_ALIGN_PARAGRAPH.LEFT),
            ("Hyper-Optimize for Quality, Speed, Efficiency", 20, True, False, WHITE, 6, WD_ALIGN_PARAGRAPH.LEFT),
            ("How the engine spends 16 GB, 448 GB/s, 6 cores, and 32 GB RAM so the phone feels instant and the output still looks and sounds expensive.", 11, False, True, TEAL_LT, 0, WD_ALIGN_PARAGRAPH.LEFT),
        ],
    )
    spacer(doc, 10)

    kv_table(
        doc,
        [
            ("Document type", "Logistics (resource flow, order of operations) + function (what each subsystem does under load)"),
            ("Objective", "Highest possible quality × fastest time-to-result × lowest waste, on this exact PC"),
            ("Target machine", "MattsGamingPC — Ryzen 5 9600X, 32 GB RAM, RTX 5060 Ti 16 GB, ~306 GB free"),
            ("Client", "Galaxy S24+ APK over LAN — time-to-first-byte on the phone is the speed KPI"),
            ("Companion", "Product & Technical Specification v1.3"),
            ("Date", "15 September 2026"),
            ("Status", "v1.2 — mode-sticky residency + APK offload of cheap chores"),
        ],
        (2.15, 4.85),
        ("Field", "Value"),
    )
    spacer(doc, 8)
    callout(
        doc,
        "THE RULE IN ONE SENTENCE",
        "Do the expensive thinking once (install, convert, calibrate, mode enter). Consecutive prompts in the open generation mode stay warm — no load, no unload. Never make the user pick a sampler, and never make them pin a model just to generate a second image.",
        bg=LIGHT_TEAL, title_color=ACCENT, border=TEAL_BORDER,
    )

    # 1
    heading(doc, "1.  What “Hyper-Optimize” Means Here", 1)
    body(doc, "This is not a list of random flags. It is a resource operating system for one box. Three scores are always in tension; the product must win all three often enough that a novice never has to choose.")
    simple_table(
        doc,
        ["Score", "What the human feels", "What we actually measure"],
        [
            ("Quality", "It looks / sounds / reads right", "Prompt adherence, detail, temporal stability, WER, MOS-like A/B, no VAE mush, no metallic TTS"),
            ("Speed", "The phone answered now", "Time-to-first-token / first-preview / first-PCM; time-to-done; LAN TTFB"),
            ("Efficiency", "It didn’t melt, fill, or crash", "Peak VRAM, bytes moved, disk writes, joules per artifact, reload count, failed jobs"),
        ],
        [1.4, 2.4, 3.2],
    )
    heading(doc, "1.1  The only machine that matters", 2)
    simple_table(
        doc,
        ["Resource", "Fact", "What it implies"],
        [
            ("VRAM", "16 GB GDDR7", "One heavy pipeline. Dual-text only if both fit. Headroom target: leave ~1.5 GB free."),
            ("Bandwidth", "448 GB/s on a 128-bit bus", "LLM decode and video DiT are memory-bound. Quantization and fused kernels beat “more CUDA.”"),
            ("Tensors", "144× 5th-gen (FP8 / FP4)", "Prefer FP8/FP4/TensorRT paths where quality holds. FP32 is a bug."),
            ("Board power", "180 W", "Keep the GPU busy, not the CPU. 180 W is plenty if kernels are dense."),
            ("CPU", "9600X 6C/12T, 3.9–5.4 GHz, 65 W", "Gateway + tokenize + ffmpeg + downloads. Never CPU-offload a UNet."),
            ("RAM", "32 GB (31.1 usable)", "Windows + engine + mmap. Working budget ≈ 24 GB. Do not page during video."),
            ("Disk", "≈306 GB free", "Convert only if it pays rent. Sparse HF downloads. Previews, not raw dumps, to the phone."),
            ("LAN", "Home Wi-Fi to S24+", "Thumbnails first. Stream tokens and PCM. Transcode for the phone."),
        ],
        [1.3, 2.2, 3.5],
    )
    body(
        doc,
        "Cite the silicon, not a vibe: RTX 5060 Ti 16 GB is Blackwell GB206, 4,608 CUDA cores, 16 GB GDDR7 at 28 Gbps, 448 GB/s, 180 W. "
        "Ryzen 5 9600X is 6 cores / 12 threads, 38 MB cache, DDR5, 65 W. Optimization that ignores the 128-bit bus will look busy and still feel slow.",
        italic=True, color=SLATE, size=10,
    )

    heading(doc, "1.2  Philosophy — seven laws", 2)
    bullet(doc, "A model is converted once, at install, into the fastest format this GPU likes. Runtime never “figured out dtype” from scratch.", bold_lead="1. Pay once. ")
    bullet(doc, "Bytes across the 128-bit bus are the scarce resource. If a trick doesn’t cut bytes or kernel launches, it is not an optimization.", bold_lead="2. Bandwidth first. ")
    bullet(doc, "The GPU does math. The CPU does I/O, decode, and protocol. Crossing that line is how 6-core boxes die.", bold_lead="3. Right processor. ")
    bullet(doc, "Show something in <300 ms (skeleton, first token, TAESD preview, waveform grow). Finish in the background.", bold_lead="4. First byte is the product. ")
    bullet(doc, "Fast / Balanced / Quality / Max are four recipes, not four UIs. Hidden parameters live in the recipe.", bold_lead="5. Ladders, not knobs. ")
    bullet(doc, "The open generation mode is the lease. Consecutive prompts in that mode never pay load/unload. Swap only on model change or mode change. Pin is a rare override, not the normal way to stay warm.", bold_lead="6. Residency follows the mode. ")
    bullet(doc, "If it won’t fit, refuse before heat. A clean no is faster than an OOM.", bold_lead="7. Refuse early. ")

    # 2
    heading(doc, "2.  Quality Ladders — the User-Facing Function", 1)
    body(doc, "One control, four rungs, every generate surface. Remembered per modality. Default Balanced. The APK never asks for CFG, sampler name, or quant. Those are function of the rung + the model’s recipe file.")

    simple_table(
        doc,
        ["Rung", "Intent", "Typical mapping (engine, not user)"],
        [
            ("Fast", "Interactive. Sketch, talk, try.", "Distilled / LCM / Turbo / Hyper; 4–8 steps; native or 768; TAESD preview; Q4/FP8; short audio; 512² video frames; skip refiner"),
            ("Balanced", "Daily driver. Default.", "Model’s native recipe; 20–28 steps or native distilled; Q5/FP8; 1024-class SDXL; 8–12 s audio; 16–24 video frames"),
            ("Quality", "Keep this.", "Full model not turbo; more steps only if it pays; better VAE; Q8/FP16 if VRAM allows; 2× tiled upscale; higher TTS vocoder; 24–32 frames"),
            ("Max", "Queued. One shot.", "Full precision the card can hold; refiner or second pass; 4× tiled upscale; film/grain optional; longest allowed audio/video; never concurrent"),
        ],
        [1.25, 1.7, 4.05],
    )
    callout(
        doc,
        "QUALITY IS NOT “MORE STEPS”",
        "On a 16 GB, 448 GB/s card, 50 steps of a wrong resolution with a muddy VAE loses to 12 steps of the right native size, a decent VAE, and a tiled 2× upscale. Max is a two-pass pipeline (generate at native → upscale / refine), not a suicide batch size. Fast exists so the user iterates; Quality/Max exist so they commit. The engine should offer “Enhance this Fast result” which reruns the same seed on Quality — that single function is worth more than any hidden sampler list.",
    )

    heading(doc, "2.1  Enhance-this (the speed/quality bridge)", 2)
    body(doc, "Every Fast artifact has an Enhance action. Same seed, same prompt, same LoRAs, next rung. This is how we get both: people draft at Fast, keep at Quality, without retyping. Store the full recipe on the artifact so Enhance is deterministic.")

    # 3
    heading(doc, "3.  The Resource OS — Logistics Core", 1)
    body(doc, "The orchestrator is a tiny operating system. Handlers ask it for VRAM, it grants a lease. No handler allocates “and hope.”")

    heading(doc, "3.1  Accounts", 2)
    simple_table(
        doc,
        ["Account", "Unit", "Policy"],
        [
            ("VRAM", "MB, measured not claimed", "Lease per generation mode. Headroom 1.5 GB. OOM is a bug in the estimator."),
            ("RAM", "MB", "mmap weights; cap caches; refuse if predicted commit > 24 GB."),
            ("Disk", "bytes free", "Size-gate downloads and conversions. Warn at 80%, refuse at 92%."),
            ("GPU lock", "one heavy, N light", "Heavy = UNet/DiT/LLM generate/train. Light = embed, ffmpeg, download, STT-small."),
            ("CPU", "threads", "Reserve 2 for gateway+OS. ffmpeg transcode niceness lower than STT."),
            ("LAN", "in-flight bytes", "Thumbnails before originals. One full-media fetch at a time per client."),
            ("Thermal", "GPU temp / throttle", "If throttling, drop to Fast kernels (no new Max jobs) and tell the phone."),
            ("Sleep", "Windows", "Inhibit while a job is running. After a long APK disconnect, unload the mode lease and allow sleep."),
        ],
        [1.3, 1.8, 3.9],
    )

    heading(doc, "3.2  Load / unload / pin logistics — mode-sticky residency", 2)
    body(doc, "Typical use is one function consecutively. The open generation mode is the lease. Do not load or unload per prompt.")
    bullet(doc, "Paid on mode enter and on model switch, not per prompt.", bold_lead="Cold load: ")
    bullet(doc, "already resident. Skip. This is the common path.", bold_lead="Warm run: ")
    bullet(doc, "zero load/unload for consecutive generate/chat/speak. Looking at the result is not an exit.", bold_lead="Stay in mode: ")
    bullet(doc, "swap heavy weights, keep the new ones for the rest of the mode session.", bold_lead="Switch model: ")
    bullet(doc, "unload previous mode’s heavy pipeline, load the new mode’s selected model.", bold_lead="Switch mode: ")
    bullet(doc, "background GPU convert/TRT waits. The current studio wins.", bold_lead="Mode beats background: ")
    bullet(doc, "drop P-state between prompts; weights may stay in VRAM. Residency ≠ 180 W.", bold_lead="Power vs. residency: ")
    bullet(doc, "only after long APK disconnect (~12 min) or overnight sleep. Return = one reload.", bold_lead="The only idle unload: ")
    bullet(doc, "manual Pin is for rare Chat↔Image hopping. If Image mode needs Pin to be fast, residency is broken.", bold_lead="Pin is the exception: ")
    bullet(doc, "never two heavy pipelines half-loaded. Count LoRAs and ControlNets in the Image-mode lease.", bold_lead="No half-states: ")

    heading(doc, "3.3  Queue logistics", 2)
    bullet(doc, "One heavy GPU job. FIFO with priority: interactive (Talk, chat token, Fast preview) > user-started generate in the active mode > Enhance > train > convert > download-postprocess.")
    bullet(doc, "A Talk turn may preempt a queued Max image, never a running one, unless the user cancels. Entering Talk is a mode switch, so Image unloads then — that is explicit, not a surprise eviction mid-canvas.")
    bullet(doc, "Downloads use CPU/NIC only. They never take the GPU lock. Convert jobs take the GPU lock only for TRT build / FP8 cast, and only when no generation mode is holding a lease (or the user left).")
    bullet(doc, "Pipeline jobs that stay inside one mode (image → upscale) keep the mode lease the whole time. Pipelines that cross modes (image → photo-to-video) are an explicit mode sequence: Image lease, then Video lease.")
    bullet(doc, "Do not release VRAM between consecutive prompts in the same mode. There is no “between.” The mode is still open.")

    heading(doc, "3.4  “Will it fit?” function", 2)
    body(doc, "Before every Use / Download / Train / Pipeline, compute: disk_need, vram_need[ladder], eta_sec[ladder], conflicts (what must unload). Show it. The estimator uses the calibrator tables, not blog numbers. If fit is false, propose: smaller quant, Fast instead of Max, unload X, or queue.")

    # 4
    heading(doc, "4.  Function Map — What Each Subsystem Does", 1)
    simple_table(
        doc,
        ["Function", "When", "Optimized behavior"],
        [
            ("calibrate()", "First run, after driver change", "Microbench: copy GB/s, FP16/FP8 GEMM, a 7B Q4 tok/s, a 1024 SDXL step time, NVENC fps. Writes tables."),
            ("acquire()", "Paste / scan", "HEAD/API size; sparse files; resume; checksum; never mark Ready."),
            ("detect()", "After files land", "Architecture sniff; Inbox if unknown."),
            ("convert()", "After detect, if it pays", "To GGUF / FP8 / TRT / ONNX. Skip if disk_need > rent (see §6)."),
            ("catalog()", "After convert", "Record + estimates per ladder + license snippet."),
            ("estimate()", "Any Use", "VRAM/RAM/disk/ETA from calibrator × model recipe."),
            ("lease_vram()", "Mode enter / model switch", "Grant a mode lease, not a per-prompt lease. Refuse if it cannot fit."),
            ("load()", "On lease grant", "Runtime file only, not the raw HF dump, unless no runtime exists. Skipped on warm prompts."),
            ("warm()", "Once per process/model", "CUDA graphs / cudnn benchmark / dummy step. Paid once."),
            ("run_*()", "Generate", "Ladder recipe. Stream first byte. Write artifact + recipe."),
            ("preview()", "Fast image / video", "TAESD / low-res latent decode to the phone immediately."),
            ("enhance()", "User tap", "Replay recipe one rung up, same seed."),
            ("transcode()", "After artifact", "CPU/NVENC phone proxy. Original stays on disk."),
            ("stream()", "Always", "WS events: token, pcm, thumb, log, progress, eta."),
            ("unload()", "Mode switch / model switch / long disconnect", "Free heavy block. Not after every prompt. Not after a short pause in the same mode."),
            ("caption() / embed()", "Dataset / RAG", "CPU default while a generation mode holds VRAM; GPU batch only when no mode lease."),
            ("train_lora()", "User job", "Latent cache, 8-bit adam, checkpointing, resume."),
            ("watchdog()", "Always", "Restart engine; release leases on crash; inhibit sleep."),
        ],
        [1.55, 1.7, 3.75],
    )

    # 5
    heading(doc, "5.  Lifetime Logistics — Order of Operations", 1)
    heading(doc, "5.1  Install path (pay once)", 2)
    body(doc, "1. Paste URL.  2. Probe size + gated?  3. Phone confirms if large.  4. Download sparse / resume.  5. Detect.  6. Decide convert (rent test).  7. Convert as a job with log.  8. Micro-probe: one forward at Fast to measure real VRAM.  9. Write catalog estimates.  10. Ready.  The user may Use a raw checkpoint at Balanced if convert is still running — convert is an optimizer, not a gate, unless the raw form cannot run.")

    heading(doc, "5.2  Convert rent test", 2)
    body(doc, "Convert if (a) it cuts VRAM or bytes-moved enough to change a ladder from “won’t fit” to “fits,” or (b) it cuts ETA ≥ 20%, and (c) engine file size < 1.6× original unless the original will be deleted, and (d) free disk after convert ≥ 40 GB. TensorRT engines are resolution-specific: build for the model’s native size only, not a zoo of engines. If disk is tight, keep GGUF/FP8 and skip TRT.")

    heading(doc, "5.3  Runtime path (pay on mode enter — keep consecutive runs tiny)", 2)
    body(doc, "Mode enter / model switch:  1. estimate() for the selected model.  2. Show will-it-fit if needed.  3. lease_vram for this mode (unload the previous mode).  4. load runtime.  5. warm once.  Then every prompt in that mode:  6. enqueue.  7. run with ladder (already resident).  8. stream first byte.  9. write artifact + recipe.  10. transcode proxy on NVENC/CPU.  11. do not release the mode lease.  12. drop GPU clocks until the next prompt, but leave weights in VRAM.")

    heading(doc, "5.4  Idle path", 2)
    bullet(doc, "If the APK is still connected and a generation mode is open: do not unload. Drop clocks. Keep the engine process alive (CUDA context create is expensive). Keep the mode’s weights in VRAM.")
    bullet(doc, "Background allowed only if it does not need that VRAM: embedding ingest, proxy transcode, dataset caption on CPU, downloads. GPU convert/TRT waits until the mode lease is gone.")
    bullet(doc, "If the APK has been disconnected for the long idle (default ~12 min): unload heavy, allow Windows sleep. Next connect to the same mode reloads once.")
    bullet(doc, "Downloads continue either way. They never need the GPU.")

    heading(doc, "5.5  Crash path", 2)
    bullet(doc, "Watchdog notices dead worker. Leases zeroed. Job marked failed with last log lines. VRAM is free because the process died — do not “try to recover the CUDA context.” Start clean.")
    bullet(doc, "Downloads resume. TRT builds resume from scratch (engines are not appendable). Training resumes from last ckpt on disk.")

    # 6
    heading(doc, "6.  Per-Modality Playbooks", 1)
    body(doc, "Each playbook is the function of that handler under the laws in §1.2. Numbers are starting recipes for this 5060 Ti; the calibrator overwrites them.")

    heading(doc, "6.1  Text generation (bandwidth-bound)", 2)
    bullet(doc, "Prefer GGUF Q4_K_M / Q5_K_M on CUDA. Q8 only on Quality/Max and only ≤13B. FP16 13B+ will spend the bus and the VRAM.", bold_lead="Format. ")
    bullet(doc, "Flash-attention / CUDA graphs on. mmap the GGUF from NVMe; do not copy the whole file into RAM.", bold_lead="Kernels. ")
    bullet(doc, "KV cache Q8 or Q4. This is the difference between a 32k context that fits and one that does not.", bold_lead="KV. ")
    bullet(doc, "If a tiny draft model is already on disk and VRAM remains, speculative decoding on Fast/Balanced. Skip on Max if it hurts quality.", bold_lead="Speculative. ")
    bullet(doc, "Stream every token. Time-to-first-token target: <200 ms warm, <2.5 s cold 7B-Q4.", bold_lead="Stream. ")
    bullet(doc, "Context: Fast 4k, Balanced 8k, Quality 16k, Max 32k if KV fits — never silently drop the system prompt.", bold_lead="Context. ")
    bullet(doc, "70B dense: refuse. MoE with few active experts: estimate from calibrator, usually still no.", bold_lead="Refuse. ")

    heading(doc, "6.2  Vision-language", 2)
    bullet(doc, "Treat as a heavy text model plus a vision tower. Not concurrent with T2I. Images resized to the model’s native (e.g. 336/448/768) before GPU, on CPU.")
    bullet(doc, "Multiple images in one turn: cap at a small N; extra go to RAG-style captions instead of blowing the context.")

    heading(doc, "6.3  Text-to-image / image generation", 2)
    bullet(doc, "Generate at the model’s native resolution (SD1.5 512, SDXL 1024, etc.). Never 1536 native on this card as default.", bold_lead="Native size. ")
    bullet(doc, "Fast = distilled (LCM/Turbo/Hyper/SDXL-Lightning) 4–8 steps. Balanced = native recipe. Quality = native + better VAE + 2× tiled upscale. Max = Quality + refiner or 4× tiled.", bold_lead="Ladders. ")
    bullet(doc, "TAESD or tiny-VAE preview to the phone at step 1–2 so Create feels alive. Full VAE at the end.", bold_lead="Preview. ")
    bullet(doc, "FP16/BF16 default; FP8 UNet when quality delta is in the noise (calibrator A/B). TensorRT engine at native size if convert rent test passes.", bold_lead="Dtype. ")
    bullet(doc, "Tiled VAE always for ≥1024. Attention slicing only if the lease is tight — it costs speed.", bold_lead="Memory tricks. ")
    bullet(doc, "LoRA: one or two at Fast (dynamic). Quality/Max may merge LoRAs into a temporary runtime for speed if the same stack is reused.", bold_lead="LoRA. ")
    bullet(doc, "ControlNet/IP-Adapter counted in VRAM. Extractors (canny/depth/pose) run first, cached by image hash, often a small separate model — don’t keep them loaded with the UNet if Fast is the rung.", bold_lead="Control. ")
    bullet(doc, "Batch size 1 default. Batch 2+ only if estimate says it is faster and still fits — on 16 GB it often isn’t.", bold_lead="Batch. ")

    heading(doc, "6.4  Image editing", 2)
    bullet(doc, "Inpaint at the crop around the mask plus margin, then composite — do not re-denoise the whole 1024 if the mask is a face.")
    bullet(doc, "Edit is its own generation mode. Leaving Image for Edit unloads the T2I UNet and loads the edit pipeline; consecutive edits then stay warm. Upscale inside Edit keeps the Edit lease.")

    heading(doc, "6.5  Upscale", 2)
    bullet(doc, "This is how Max quality is actually achieved. Tile with overlap, GPU one tile at a time, CPU composites. Never full-frame 4K in VRAM.")
    bullet(doc, "Pick 2× for Quality, 4× for Max. Fast does not upscale unless the user taps Enhance.")
    bullet(doc, "Video upscale = same tiler per frame + optional interpolation; treat as a long job with a preview first frame.")

    heading(doc, "6.6  Video (T2V, photo-to-video, V2V)", 2)
    bullet(doc, "Always queued. Defaults: Fast 12–16 frames at 384–512; Balanced 24 frames at 512–640; Quality 32 frames then interpolate; Max = Quality + upscale. Duration caps are product law.")
    bullet(doc, "Cache transformer blocks / TeaCache-style skipping when quality delta is acceptable (Fast/Balanced). Disable on Max if it ghosts.")
    bullet(doc, "Encode with NVENC (H.264/HEVC) on the media plane while tiles finish. Do not leave raw PNG sequences as the phone artifact.")
    bullet(doc, "Will-not-fit is the default for “1080p 4 seconds, full model.” The empty state offers Fast clip or “install a distilled I2V.”")
    bullet(doc, "Never concurrent with any other heavy job. Unload everything else first.")

    heading(doc, "6.7  Speech (TTS, STT, Talk)", 2)
    bullet(doc, "STT: a small/fast model always, because Talk is interactive. Quality/Max can re-transcribe with a larger model after, asynchronously, and patch the log.", bold_lead="STT. ")
    bullet(doc, "TTS: stream PCM in 100–200 ms chunks. Load a Fast vocoder for Talk; Quality may swap vocoder for a slower high-MOS one on longform.", bold_lead="TTS. ")
    bullet(doc, "Talk pipeline: mic → opus/pcm over LAN → STT → LLM → TTS. Talk is a generation mode: STT+LLM+TTS stay resident for the whole Talk session (tiny STT if VRAM is tight). Leaving Talk unloads them. Consecutive turns never reload.", bold_lead="Talk residency. ")
    bullet(doc, "Barge-in: cancel TTS playback immediately on new VAD. Don’t wait for the sentence.", bold_lead="Barge-in. ")
    bullet(doc, "Voice profiles: extract speaker embedding once at record time; runtime is embedding + base TTS, not a 2 GB clone model per person.", bold_lead="Voices. ")

    heading(doc, "6.8  Music / SFX / audio edit", 2)
    bullet(doc, "Queued, length-capped (Fast 8 s, Balanced 15 s, Quality 30 s, Max 60 s or model max, whichever smaller).")
    bullet(doc, "Denoise/stems are utilities: small models, can run as light jobs. Don’t keep MusicGen loaded to denoise a podcast.")
    bullet(doc, "Normalize loudness (EBU R128-ish) in ffmpeg so Gallery playback isn’t a surprise.")

    heading(doc, "6.9  RAG / documents", 2)
    bullet(doc, "Ingest on CPU+small embed model; embeddings live in RAM/disk (sqlite / faiss-lite), not VRAM.")
    bullet(doc, "Query: embed on CPU or a tiny GPU model that does not evict the LLM if the LLM is pinned. Retrieve k chunks, then one LLM call.")
    bullet(doc, "Don’t fine-tune an LLM to “know” a PDF. RAG is the efficient function.")

    heading(doc, "6.10  Training (LoRA)", 2)
    bullet(doc, "Default recipe for 16 GB: rank 8–16, 8-bit optimizer, gradient checkpointing, batch 1–2, cached latents on disk for images, mixed precision.")
    bullet(doc, "Cache latents/captions once. The second epoch should not re-run the VAE.")
    bullet(doc, "Live log throttled (every N steps) so the phone isn’t drowning. Cancel writes a usable last ckpt.")
    bullet(doc, "Schedule train as lowest GPU priority. A Talk session waiting 200 ms is more important than step 412.")
    bullet(doc, "Refuse full fine-tunes of SDXL/LLM that the estimator says will spill. Offer LoRA in the same breath.")

    heading(doc, "6.11  Tool router", 2)
    bullet(doc, "Serialize tool calls. Each call is a child job with its own lease. Don’t leave the LLM and the UNet loaded together unless both still fit after the call graph is known.")
    bullet(doc, "Show steps on the phone. The user can deny a tool. Denial is faster than a 20-step image they didn’t want.")

    # 7
    heading(doc, "7.  Client & LAN Logistics", 1)
    body(doc, "Speed the user feels is APK speed, not GPU occupancy. A 30-step image that appears at step 2 as a preview beats a 10-step image that appears at the end as a 12 MB PNG.")
    bullet(doc, "Protocol: WebSocket for events, HTTP range for media. Local only.")
    bullet(doc, "First packet: job id + eta + skeleton. Then tokens / PCM / 64–96 px thumbs. Original on tap.")
    bullet(doc, "Image proxies: 1280-wide WebP/AVIF. Video: 720p H.264 High@phone. Audio: AAC 128–192 or streamed PCM for Talk.")
    bullet(doc, "Originals stay lossless-enough on the PC (PNG/WebP-lossless / WAV / high-CRF). Never replace the original with the proxy.")
    bullet(doc, "Mic: send 16 kHz mono for STT (what the model wants), not 48 kHz stereo from the S24+.")
    bullet(doc, "Camera/photos: downscale on device to the handler’s native before upload when the job is Fast. Quality/Max may request the full file.")
    bullet(doc, "Reconnect: subscribe(job_id / chat_id) replays missed events. Do not restart the GPU job because Wi-Fi hiccuped.")
    bullet(doc, "One-handed: Talk and send are reachable; ladders are a segment control, not a nested picker.")

    heading(doc, "7.1  Client offload — make the backend faster without making the phone slower", 2)
    body(
        doc,
        "The S24+ is a Snapdragon-class 12 GB phone. It is excellent at resampling, compressing, silencing, and drawing, and the wrong place for a second PyTorch. "
        "Offload is allowed only when all three are true: (1) it finishes before the user would notice (< ~30 ms for UI-path, < ~150 ms for a photo prepare), "
        "(2) it cuts PC CPU, GPU, or LAN, (3) it does not heat the phone or drain it in a session. If an offload is felt, it is a bug — send the work back to MattsGamingPC.",
    )
    simple_table(
        doc,
        ["Offload", "Phone cost", "Backend / LAN save"],
        [
            ("Mic → 16 kHz mono + AEC", "Instant, HW path", "PC doesn’t resample 48 kHz stereo or fight echo"),
            ("On-device VAD (Silero-class)", "Tiny NPU/CPU, ms", "Don’t stream silence; STT job never starts on dead air"),
            ("Barge-in locally", "Instant", "Cancel TTS playback without a round trip; STT doesn’t hear the bot"),
            ("EXIF orient + strip", "Instant", "9600X doesn’t rotate 12 MP HEICs; models get upright pixels"),
            ("Downscale to model native + WebP/JPEG", "ISP/GPU, usually <100 ms", "LAN shrinks 10×; PC skips decode of 4000px camera stills"),
            ("Mask as small PNG (not a second full image)", "Brush already local", "Inpaint crop is smaller; less upload"),
            ("Short clip HW-downscale before I2V", "HW encoder, short only", "Don’t ship 4K60 camera roll across Wi-Fi for a 3 s clip"),
            ("Recipe JSON built on device", "Instant", "Backend run() is pure; no chatty round trips for seed/slider"),
            ("Debounce sliders; seed++ locally", "Instant", "One job, not forty"),
            ("Prompt empty / too-long check", "char/4 or cached tokenizer.json", "No rejected jobs, no tokenizer round trip for a red bar"),
            ("Cache thumbs, chats, last media", "Disk on phone", "Gallery scroll hits LAN once"),
            ("Waveform from incoming PCM", "Cheap CPU as audio streams", "ffmpeg on the PC is not graphing UI chrome"),
            ("Markdown / lightbox / crop UI", "UI thread", "PC never renders pixels for humans"),
            ("OCR (ML Kit) “text from photo”", "Fast on 8 Gen 3", "Fills a prompt without a VLM job"),
            ("Canny on-device for ControlNet Fast", "CPU ms on a still", "Image-mode GPU lease is not stolen by an extractor"),
            ("Upload content-hash", "Instant", "Skip re-send of the same photo"),
        ],
        [2.55, 1.85, 2.6],
    )
    heading(doc, "7.2  Never offload to the APK", 3)
    bullet(doc, "Foundation inference: LLM, diffusion UNet, VAE, neural TTS vocoder, music DiT, Whisper-class STT, depth/pose/SAM, upscalers, training, TRT/GGUF convert.")
    bullet(doc, "Long camera-roll video transcode. A 2-minute 4K export will heat the phone and feel slow. Send a user-trimmed short clip, or let the PC take the file on LAN while the UI stays live (progress, not a frozen gallery).")
    bullet(doc, "A second “on-device AI” stack that duplicates the engine. Dual STT (phone draft + PC STT) is complexity without a speed win; tiny STT already lives on the PC for Talk.")
    heading(doc, "7.3  Why this is a 9600X win, not a gimmick", 3)
    body(
        doc,
        "The bottleneck on MattsGamingPC is not “the phone is idle.” It is 6 CPU threads, a 128-bit GPU bus, and Wi-Fi. Every 12 MP HEIC decode, every 48 kHz stereo resample, every silence-padded STT, every ffmpeg waveform, every canny extractor that unloads or contends with Image mode, is stolen generation. "
        "The APK already has to touch those pixels and that mic. Doing the chore at the source is free; doing it again on the PC is waste. Measure: Talk LAN bytes with/without VAD; Image upload bytes with/without native downscale; PC CPU% during a 10-image session. If those curves don’t drop, the offload isn’t actually on.",
    )
    callout(
        doc,
        "MODE-STICKY + CLIENT CHORES",
        "Image mode keeps the UNet warm. The APK keeps the UNet from also doing housework. Consecutive images should be: phone already has a native-sized JPEG ready, recipe already built, one prompt message, warm run, first preview back. No HEIC, no silence, no extractor, no reload.",
        bg=LIGHT_TEAL, title_color=ACCENT, border=TEAL_BORDER,
    )

    # 8
    heading(doc, "8.  Windows / NVIDIA / CUDA Logistics", 1)
    body(doc, "The engine assumes it owns the GPU. These are machine functions we set once in Phase 0 and document in Settings → Power as “Apply recommended.”")
    simple_table(
        doc,
        ["Lever", "Setting", "Why"],
        [
            ("GPU", "NVIDIA as the only CUDA device; CUDA_VISIBLE_DEVICES=that UUID", "iGPU must never see a kernel"),
            ("Power", "Max performance while a kernel runs; drop P-state between prompts even if weights stay resident", "Residency is free-ish; 180 W the whole Image session is not"),
            ("HAGS", "On, unless calibrator shows a regression", "Usually helps copy overlap"),
            ("Sleep", "Sleep inhibited during jobs/pin; disk sleep OK", "CUDA + sleep = zombie"),
            ("Plan", "High Performance / Ultimate while engine active", "9600X boost stays up for tokenize/ffmpeg"),
            ("Defender", "Exclude library root + runtime dir", "Realtime scan of 10 GB GGUF is a fake disk cliff"),
            ("Pagefile", "Managed, ≥ 32 GB on the fast drive", "mmap + commit spikes during convert"),
            ("Game Mode", "Off for the engine process", "Windows will otherwise starve background CUDA"),
            ("Clocks", "No user overclock required", "180 W card; stability > 3%"),
            ("Drivers", "Game-ready or studio, pinned; recalibrate on change", "TRT engines are driver-bound — rebuild after upgrade"),
            ("NVENC", "Used for proxies, not for diffusion", "Free the CUDA cores from encode"),
            ("Process", "Engine as a user service / startup", "Phone just works; watchdog parent"),
        ],
        [1.3, 2.9, 2.8],
    )
    callout(
        doc,
        "DO NOT",
        "Do not CPU-offload UNets (“sequential CPU offload”) as a default — 6 cores and DDR5 will turn a 4-second image into a minute. Offload is a last-chance Quality path that the UI must label Slow, not a silent fallback. Do not enable every xformers/sage/triton flag at once; the calibrator picks a winner per handler. Do not build five TensorRT resolutions. Do not store HF home on a spinning disk or in Documents.",
    )

    # 9
    heading(doc, "9.  Disk & Acquire Logistics", 1)
    bullet(doc, "Library on the fastest NVMe. Runtimes subdir next to weights. Artifacts on the same drive unless the user points elsewhere.")
    bullet(doc, "HF: allow_patterns for the handler (safetensors not *.bin; one quant not five). Resume. hf_transfer if it still wins in 2026.")
    bullet(doc, "GitHub: releases assets over git clone when a release exists. No recursive submodule surprises without confirm.")
    bullet(doc, "Civitai: image/LoRA only; still size-gate; store the version id so updates are explicit jobs, not silent overwrites.")
    bullet(doc, "Dedup: same SHA is one blob, many catalog cards if needed. Don’t store SDXL twice because two UIs named it twice.")
    bullet(doc, "Garbage: failed jobs’ temp dirs, old TRT after driver change, unused Fast quants if Quality quant exists and disk < 60 GB free — all cleanable from the phone.")
    bullet(doc, "Convert artifacts that lose: if TRT is slower than eager in calibrator, delete the engine, keep eager, record the miss so we don’t rebuild forever.")

    # 10
    heading(doc, "10.  Calibration & Measurement", 1)
    heading(doc, "10.1  First-run calibrator", 2)
    body(doc, "A 2–4 minute job the phone can watch. Writes /library/calibration.json used by estimate(). Re-runs on driver change or a “Recalibrate” button.")
    simple_table(
        doc,
        ["Probe", "Records"],
        [
            ("Device inventory", "CUDA name, VRAM, driver, CPU cores, RAM, disk free, NVENC present"),
            ("Copy", "Host↔device GB/s, disk sequential MB/s"),
            ("GEMM", "FP16 / FP8 / FP4 if exposed, TFLOP-ish, to pick dtype"),
            ("LLM", "7B-Q4 tok/s prefill+decode at 2k context if a tiny model is present; else synthetic"),
            ("Diffusion step", "SDXL-class 1024 step time if present; else synthetic conv stack"),
            ("NVENC", "1080p encode fps"),
            ("Thermal", "Temp after 60 s load — for throttle policy"),
        ],
        [2.0, 5.0],
    )
    heading(doc, "10.2  Per-model micro-probe", 2)
    body(doc, "On first Ready, one Fast forward. Record real_vram_mb, real_ms_first, real_ms_done. This overwrites the generic table for that model. Without this, “will it fit?” lies.")
    heading(doc, "10.3  KPIs the engine logs (and Resources can show)", 2)
    bullet(doc, "ttft_ms, ttdone_ms, preview_ms, pcm_chunk_ms")
    bullet(doc, "vram_peak_mb, ram_commit_mb, bytes_moved_est, reloads_count")
    bullet(doc, "job_fail_oom, job_fail_disk, throttle_events")
    bullet(doc, "These are how we know Fast is actually fast. If Fast ttdone ≈ Quality ttdone, the distilled path is broken.")
    bullet(doc, "reloads_count per Image-mode session should be 1 (mode enter) plus 1 per model switch. If it equals the number of prompts, residency is broken.")

    # 11
    heading(doc, "11.  Highest-Quality Path (when the user picks Max or Enhance)", 1)
    body(doc, "Quality is a pipeline, not a bigger slider. This is the function of Max on this card:")
    simple_table(
        doc,
        ["Modality", "Max pipeline on the 5060 Ti"],
        [
            ("Text", "Best fitting quant that does not spill (often Q5/Q8 7–13B); full context that still fits; no draft model if it changes answers; don’t up the temperature."),
            ("Image", "Native res, full (non-turbo) weights, correct VAE, right LoRA strength, then tiled 2×/4× upscale. Optional refiner if it fits after unload of UNet. Face/structure restore only if the user enabled the utility."),
            ("Edit", "Crop-around-mask inpaint at native, composite, then upscale the whole."),
            ("Video", "Short native generate → interpolate → tiled upscale. Never native 1080p DiT."),
            ("TTS", "Larger acoustic model + better vocoder, offline (not Talk). Normalize."),
            ("Music", "Model max that fits, then ffmpeg limiter. No fake extra minutes."),
            ("RAG", "More retrieved chunks + Quality LLM, still one call."),
        ],
        [1.3, 5.7],
    )
    body(doc, "If Max will not fit, the UI offers Quality automatically with one sentence why. It does not silently drop to Fast.")

    # 12
    heading(doc, "12.  Fastest Path (when the user is iterating)", 1)
    bullet(doc, "Being in a generation mode is enough. Image mode keeps the image pipeline warm for image #2, #3, #N. No extra Pin. No per-prompt load.")
    bullet(doc, "Distilled image, tiny STT, streaming TTS, Q4 LLM, TAESD preview, 1280 WebP proxy.")
    bullet(doc, "Skip TRT if eager is already < the LAN round-trip. Skip LoRA merge on every image; merge once if the same stack will be used for the whole Image-mode session.")
    bullet(doc, "Reuse prompt embeddings if the prompt text hasn’t changed and only the seed has — consecutive variations are the Image-mode bread and butter.")
    bullet(doc, "Enhance is the off-ramp to quality so Fast doesn’t have to be good enough to keep. Enhance stays in Image mode, so the Quality weights swap once, then consecutive Enhances (if any) stay warm too.")
    bullet(doc, "The expensive moment is entering Image mode (or switching checkpoint). After that, the phone should feel like the model was always on.")

    # 13
    heading(doc, "13.  Implementation Order — Biggest Wins First", 1)
    body(doc, "Do not implement optimizations alphabetically. Do them in this order so Phase 2 already feels like a product.")
    simple_table(
        doc,
        ["#", "Work", "Why it is first"],
        [
            ("1", "Resource OS: mode leases, one heavy job, refuse-early, unload only on mode/model switch", "Without this, nothing else is safe — and consecutive use stays warm"),
            ("2", "Mode-enter load of a converted runtime + stream-first-byte on every warm prompt", "The product’s speed"),
            ("3", "Size-gate + sparse acquire + disk account", "306 GB free is a cliff"),
            ("4", "Calibrator + per-model micro-probe + will-it-fit", "Stops lying to the user"),
            ("5", "Quality ladders + Enhance-this + recipe-on-artifact", "Quality and speed become one UX"),
            ("6", "Pin NVIDIA, sleep inhibit, Defender exclude, watchdog", "Windows otherwise steals the win"),
            ("7", "TAESD/preview + phone proxies + WS events", "Felt speed on the S24+"),
            ("8", "Q4/Q5 GGUF + KV quant + CUDA graphs for text", "Bandwidth law"),
            ("9", "Distilled image Fast path + tiled VAE + tiled upscale", "Image quality without 50 steps"),
            ("10", "Talk as a generation mode (tiny STT + session LLM + streaming TTS, sticky until Leave Talk)", "The “anyone can use it” moment"),
            ("11", "Latent-cache LoRA train + 8-bit opt", "Training that finishes overnight, not never"),
            ("12", "FP8/TRT convert with rent test", "Real, but after eager is correct"),
            ("13", "Speculative decoding, TeaCache, LoRA merge cache", "Only if KPIs say Fast is still slow"),
            ("14", "Everything else", "Diminishing returns; don’t block phases"),
        ],
        [0.6, 3.5, 2.9],
    )

    # 14
    heading(doc, "14.  Anti-Patterns", 1)
    bullet(doc, "Loading “just in case” across modes. Do not keep Video loaded while the user is in Image. Do keep Image loaded while the user is in Image, including the pause after a result.")
    bullet(doc, "Unloading after every prompt, or after a 90-second stare at the last picture. That is the opposite of consecutive-use.")
    bullet(doc, "Keeping Hugging Face + Comfy + Ollama + this engine all resident. This product owns the GPU.")
    bullet(doc, "Shipping a desktop Gradio “for debugging” that becomes the real UI.")
    bullet(doc, "Default CPU offload, default 50 steps, default 1536², default batch 4.")
    bullet(doc, "Building TRT for every resolution and every LoRA combo.")
    bullet(doc, "Downloading every quant of a model “for later.”")
    bullet(doc, "Sending 40 MB PNG over Wi-Fi as the first view.")
    bullet(doc, "Re-tokenizing the full chat every turn without a prefix cache.")
    bullet(doc, "Training without latent cache.")
    bullet(doc, "Letting Windows sleep with a CUDA context open.")
    bullet(doc, "Pretending FP4 is lossless. Calibrate; use it on Fast; be careful on Max.")
    bullet(doc, "A settings page with 80 flags. If it isn’t a ladder or a path, it doesn’t belong on the phone. Pin is an advanced override, not a required ritual.")
    bullet(doc, "A content filter, safety API, prompt rewriter, or “blur NSFW” toggle. This studio is unfiltered. Don’t add it as a hidden default either.")

    # 15
    heading(doc, "15.  Logistics Checklists", 1)
    heading(doc, "15.1  Phase 0 machine checklist", 2)
    bullet(doc, "CUDA sees only the 5060 Ti. iGPU hidden.")
    bullet(doc, "Engine starts on login. Watchdog parent alive.")
    bullet(doc, "Library root on NVMe, Defender excluded, pagefile sane.")
    bullet(doc, "Sleep inhibited on job. Clocks up only while kernels run; mode lease may still hold VRAM.")
    bullet(doc, "Calibrator has written a file. Resources on the phone shows real VRAM.")
    heading(doc, "15.2  Every new model checklist", 2)
    bullet(doc, "Sparse download. Detect. Convert only if rent test passes.")
    bullet(doc, "Micro-probe Fast forward. Catalog estimates filled.")
    bullet(doc, "License snippet on the card. Ready only when a run actually worked.")
    heading(doc, "15.3  Every generate checklist (engine, silent)", 2)
    bullet(doc, "If same mode and same model: run → stream first byte → artifact+recipe → proxy. Do not lease, load, warm, or unload.")
    bullet(doc, "If mode enter or model switch: estimate → mode-lease → load runtime → warm once → then the warm path above.")
    heading(doc, "15.4  Quality audit (human, occasional)", 2)
    bullet(doc, "Same prompt Fast vs Quality vs Enhance: Quality must look better; Fast must be first by a lot; Enhance must match Quality.")
    bullet(doc, "Talk turn feels like a conversation, not a form submit.")
    bullet(doc, "Disk after a week of use is still livable; if not, garbage collection is failing.")

    # 16
    heading(doc, "16.  Mapping Back to the Spec", 1)
    simple_table(
        doc,
        ["Spec need", "Logistics answer"],
        [
            ("Anyone can learn it", "Ladders + Enhance + refuse-early (VRAM/disk only) + no sampler names"),
            ("Unfiltered studio", "No content policy in the engine. Refuse = won’t fit, never “not allowed.”"),
            ("Mode-sticky residency", "Load on mode enter / model switch; consecutive prompts stay warm; no per-prompt unload"),
            ("Paste-link install", "Sparse acquire, convert rent test, micro-probe, then Ready"),
            ("Offline / local", "All of this runs with WAN down; acquire is the exception"),
            ("16 GB / 306 GB / 6 cores", "One heavy job, tiled everything, NVENC proxies, no CPU UNet"),
            ("Audio + Talk", "Tiny STT, streaming TTS, session residency, barge-in"),
            ("Highest quality", "Native generate + tiled upscale + correct VAE/vocoder, not more steps"),
            ("Fast and efficient", "Pay once at install, first-byte at runtime, bandwidth-aware quants, APK chores"),
            ("APK offload", "VAD/AEC, native-size uploads, cache, OCR, on-device Canny Fast; never a second engine"),
        ],
        [2.4, 4.6],
    )

    spacer(doc, 14)
    banner_cell(
        doc,
        [
            ("END OF MANUAL  ·  v1.2", 11, True, False, WHITE, 4, WD_ALIGN_PARAGRAPH.CENTER),
            ("Pay once at install.  Stay warm in the open mode.  Phone does chores.  Stream the first byte.", 10, False, True, TEAL_LT, 0, WD_ALIGN_PARAGRAPH.CENTER),
        ],
    )

    out = "/home/user/Hyper_Optimization_Logistics.docx"
    doc.save(out)
    print("Wrote", out)


if __name__ == "__main__":
    build()
