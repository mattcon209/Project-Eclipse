"""SD / SDXL LoRA train. Run with ComfyUI's Python when possible. Never writes a fake adapter."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

IMG_SUFFIX = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--steps", type=int, default=800)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--res", type=int, default=512)
    ap.add_argument("--kohya", default="")
    args = ap.parse_args()
    base = Path(args.base)
    data = Path(args.data)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pics = [p for p in data.iterdir() if p.is_file() and p.suffix.lower() in IMG_SUFFIX]
    print(f"dataset {len(pics)} stills · base {base.name} · steps {args.steps} · rank {args.rank}", flush=True)
    if not pics:
        print("No pictures in the dataset folder. Nothing was faked.", flush=True)
        return 2
    if not base.is_file() and not (base / "model_index.json").is_file():
        print("Base checkpoint is missing. Nothing was faked.", flush=True)
        return 2
    if args.kohya:
        return _kohya(args, dest)
    return _diffusers(args, dest, pics)


def _kohya(args: argparse.Namespace, dest: Path) -> int:
    import os
    import subprocess

    print(f"kohya {args.kohya}", flush=True)
    # sd-scripts wants a folder-of-folders with repeats_name
    work = dest.parent / "kohya-data"
    tagged = work / f"1_{dest.stem}"
    tagged.mkdir(parents=True, exist_ok=True)
    data = Path(args.data)
    for p in data.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_SUFFIX:
            link = tagged / p.name
            if not link.exists():
                try:
                    os.link(p, link)
                except OSError:
                    import shutil

                    shutil.copy2(p, link)
            cap = p.with_suffix(".txt")
            txt = tagged / (p.stem + ".txt")
            if cap.is_file():
                txt.write_bytes(cap.read_bytes())
            elif not txt.is_file():
                txt.write_text(p.stem.replace("_", " ").replace("-", " "), encoding="utf-8")
    cmd = [
        sys.executable,
        str(args.kohya),
        "--pretrained_model_name_or_path",
        str(args.base),
        "--train_data_dir",
        str(work),
        "--output_dir",
        str(dest.parent),
        "--output_name",
        dest.stem,
        "--resolution",
        str(args.res),
        "--network_dim",
        str(args.rank),
        "--learning_rate",
        str(args.lr),
        "--max_train_steps",
        str(args.steps),
        "--save_model_as",
        "safetensors",
        "--network_module",
        "networks.lora",
        "--train_batch_size",
        "1",
        "--mixed_precision",
        "fp16",
        "--optimizer_type",
        "AdamW8bit",
        "--cache_latents",
        "--xformers",
    ]
    print("starting kohya", flush=True)
    r = subprocess.run(cmd)
    written = dest if dest.is_file() else dest.parent / f"{dest.stem}.safetensors"
    if r.returncode == 0 and written.is_file() and written != dest:
        written.replace(dest)
    return r.returncode


def _diffusers(args: argparse.Namespace, dest: Path, pics: list[Path]) -> int:
    try:
        import torch
        from diffusers import StableDiffusionPipeline
        from peft import LoraConfig, get_peft_model
        from torch.utils.data import DataLoader, Dataset
        from torchvision import transforms
        from PIL import Image
    except Exception as e:
        print(
            "Need diffusers + peft + torchvision on this Python (ComfyUI venv), "
            "or kohya_ss/sd-scripts. Nothing was faked. "
            + str(e)[:200],
            flush=True,
        )
        return 2

    class Pics(Dataset):
        def __init__(self) -> None:
            self.items = pics
            self.tf = transforms.Compose(
                [
                    transforms.Resize(args.res, interpolation=transforms.InterpolationMode.BILINEAR),
                    transforms.CenterCrop(args.res),
                    transforms.ToTensor(),
                    transforms.Normalize([0.5], [0.5]),
                ]
            )

        def __len__(self) -> int:
            return len(self.items)

        def __getitem__(self, i: int):
            p = self.items[i]
            im = Image.open(p).convert("RGB")
            cap = p.with_suffix(".txt")
            text = cap.read_text(encoding="utf-8", errors="replace").strip() if cap.is_file() else p.stem.replace("_", " ")
            return self.tf(im), text

    print("loading pipeline (diffusers)", flush=True)
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    pipe = StableDiffusionPipeline.from_single_file(str(args.base), torch_dtype=dtype, local_files_only=True)
    pipe.to("cuda" if torch.cuda.is_available() else "cpu")
    unet = pipe.unet
    cfg = LoraConfig(r=args.rank, lora_alpha=args.rank, target_modules=["to_k", "to_q", "to_v", "to_out.0"])
    unet = get_peft_model(unet, cfg)
    unet.train()
    opt = torch.optim.AdamW([p for p in unet.parameters() if p.requires_grad], lr=args.lr)
    loader = DataLoader(Pics(), batch_size=1, shuffle=True)
    steps = 0
    while steps < args.steps:
        for pixels, texts in loader:
            if steps >= args.steps:
                break
            pixels = pixels.to(pipe.device, dtype=dtype)
            tokens = pipe.tokenizer(
                list(texts),
                padding="max_length",
                max_length=pipe.tokenizer.model_max_length,
                truncation=True,
                return_tensors="pt",
            ).input_ids.to(pipe.device)
            with torch.no_grad():
                latents = pipe.vae.encode(pixels).latent_dist.sample() * pipe.vae.config.scaling_factor
                enc = pipe.text_encoder(tokens)[0]
            noise = torch.randn_like(latents)
            t = torch.randint(0, pipe.scheduler.config.num_train_timesteps, (latents.shape[0],), device=pipe.device)
            noisy = pipe.scheduler.add_noise(latents, noise, t)
            pred = unet(noisy, t, encoder_hidden_states=enc).sample
            loss = torch.nn.functional.mse_loss(pred.float(), noise.float())
            loss.backward()
            opt.step()
            opt.zero_grad()
            steps += 1
            if steps == 1 or steps % 25 == 0 or steps == args.steps:
                print(f"step {steps}/{args.steps} loss {float(loss):.4f}", flush=True)
    _save_peft(unet, dest)
    print(f"wrote {dest}", flush=True)
    return 0 if dest.is_file() else 2


def _save_peft(unet, dest: Path) -> None:
    tensors = {}
    for name, param in unet.named_parameters():
        if "lora" not in name.lower() or not param.requires_grad:
            continue
        key = name.replace(".", "_")
        tensors[key] = param.detach().float().cpu()
    if not tensors:
        raise SystemExit("No LoRA tensors on the UNet. Nothing was faked.")
    try:
        from safetensors.torch import save_file

        save_file(tensors, str(dest))
        return
    except Exception:
        pass
    # minimal safetensors writer (F32)
    pieces = []
    header = {}
    offset = 0
    for k, t in tensors.items():
        raw = t.contiguous().numpy().astype("float32").tobytes()
        header[k] = {"dtype": "F32", "shape": list(t.shape), "data_offsets": [offset, offset + len(raw)]}
        pieces.append(raw)
        offset += len(raw)
    blob = json.dumps(header).encode("utf-8")
    dest.write_bytes(struct.pack("<Q", len(blob)) + blob + b"".join(pieces))


if __name__ == "__main__":
    raise SystemExit(main())
