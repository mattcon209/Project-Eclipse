"""Text handler — GGUF via Ollama if it's up, else llama-cpp-python, else honest refuse.

Stub is for tests only. Production never fakes a reply.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Iterator

from eclipse.config import DATA_DIR  # noqa: F401 — keep import side-effects consistent

OLLAMA = os.environ.get("ECLIPSE_OLLAMA", "http://127.0.0.1:11434").rstrip("/")

LADDER_OPTS = {
    "fast": {"num_ctx": 4096, "num_predict": 256, "temperature": 0.8},
    "balanced": {"num_ctx": 8192, "num_predict": 512, "temperature": 0.8},
    "quality": {"num_ctx": 16384, "num_predict": 1024, "temperature": 0.7},
    "max": {"num_ctx": 32768, "num_predict": 2048, "temperature": 0.7},
}


class TextError(RuntimeError):
    pass


class TextEngine:
    def __init__(self) -> None:
        self.loaded_id: str | None = None
        self.loaded_name: str | None = None
        self.impl: str | None = None  # stub | ollama | llama
        self.ollama_model: str | None = None
        self._llama: Any = None
        self._rec: dict[str, Any] | None = None
        self._stub: Callable[..., Iterator[str]] | None = None
        self._stop = False
        self.loads = 0
        self.unloads = 0

    def set_stub(self, fn: Callable[..., Iterator[str]] | None) -> None:
        self._stub = fn
        if fn is not None:
            self.impl = "stub"

    def stop(self) -> None:
        self._stop = True

    def load(self, rec: dict[str, Any]) -> dict[str, Any]:
        rid = rec.get("id")
        if rid and rid == self.loaded_id and self.impl:
            return {"warm": True, "impl": self.impl, "reloaded": False}
        self.unload()
        impl = None
        ollama_model = None
        llama = None
        if self._stub is not None:
            impl = "stub"
        else:
            ollama_model = _resolve_ollama(rec)
            if ollama_model:
                impl = "ollama"
            else:
                llama = _try_llama(rec)
                if llama is not None:
                    impl = "llama"
        if not impl:
            path = rec.get("path") or rec.get("source") or ""
            raise TextError(
                "No text runtime. Start Ollama (the models already on this PC) or install llama-cpp-python. "
                f"GGUF is still on disk{(' at ' + path) if path else ''}."
            )
        self._rec = rec
        self.loaded_id = rid
        self.loaded_name = rec.get("name")
        self.impl = impl
        self.ollama_model = ollama_model
        self._llama = llama
        self.loads += 1
        out: dict[str, Any] = {"warm": False, "impl": impl, "reloaded": True}
        if ollama_model:
            out["ollama_model"] = ollama_model
        return out

    def unload(self) -> None:
        if self.loaded_id or self.impl:
            self.unloads += 1
        if self.impl == "ollama" and self.ollama_model:
            _ollama_unload(self.ollama_model)
        self._llama = None
        self.loaded_id = None
        self.loaded_name = None
        self.impl = None
        self.ollama_model = None
        self._rec = None

    def generate(self, messages: list[dict[str, str]], ladder: str = "balanced") -> Iterator[str]:
        self._stop = False
        opts = LADDER_OPTS.get(ladder) or LADDER_OPTS["balanced"]
        if self._stub is not None:
            yield from self._stub(messages, ladder)
            return
        if self.impl == "ollama" and self.ollama_model:
            yield from _ollama_stream(self.ollama_model, messages, opts, lambda: self._stop)
            return
        if self.impl == "llama" and self._llama is not None:
            yield from _llama_stream(self._llama, messages, opts, lambda: self._stop)
            return
        raise TextError("No text model is loaded. Use a Ready text card in Library.")


ENGINE = TextEngine()


def _ollama_tags() -> list[str]:
    try:
        with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=1.5) as r:
            data = json.loads(r.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return []
    names: list[str] = []
    for m in data.get("models") or []:
        if isinstance(m, dict) and m.get("name"):
            names.append(str(m["name"]))
    return names


def _resolve_ollama(rec: dict[str, Any]) -> str | None:
    tags = _ollama_tags()
    if not tags:
        return None
    candidates = [
        rec.get("ollama_name"),
        rec.get("name"),
        rec.get("source"),
    ]
    want: list[str] = []
    for c in candidates:
        if not c:
            continue
        s = str(c).strip()
        want.append(s)
        if ":" not in s:
            want.append(s + ":latest")
    for w in want:
        if w in tags:
            return w
    # prefix match: gemma3 vs gemma3:12b
    for w in list(want):
        stem = w.split(":")[0]
        for t in tags:
            if t == stem or t.startswith(stem + ":"):
                return t
    path = str(rec.get("path") or "")
    if "ollama" in path.lower() or "sha256-" in path:
        # Ollama is up but this blob's name didn't match — still try the catalog name
        name = rec.get("ollama_name") or rec.get("name")
        if name:
            return str(name)
    return None


def _ollama_unload(model: str) -> None:
    body = json.dumps({"model": model, "keep_alive": 0}).encode()
    req = urllib.request.Request(
        OLLAMA + "/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=8).read()
    except (urllib.error.URLError, TimeoutError, OSError):
        pass


def _ollama_stream(
    model: str,
    messages: list[dict[str, str]],
    opts: dict[str, Any],
    stopped: Callable[[], bool],
) -> Iterator[str]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": -1,
        "options": {
            "num_ctx": opts["num_ctx"],
            "num_predict": opts["num_predict"],
            "temperature": opts["temperature"],
        },
    }
    req = urllib.request.Request(
        OLLAMA + "/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=600)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        raise TextError(f"Ollama refused {model}: {detail or e}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise TextError(f"Ollama is not reachable: {e}") from e
    with resp:
        for raw in resp:
            if stopped():
                break
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            piece = ((data.get("message") or {}).get("content")) or ""
            if piece:
                yield piece
            if data.get("done"):
                break


def _try_llama(rec: dict[str, Any]) -> Any | None:
    path = rec.get("path") or rec.get("source")
    if not path:
        return None
    try:
        from llama_cpp import Llama  # type: ignore
    except Exception:
        return None
    try:
        return Llama(model_path=str(path), n_gpu_layers=-1, n_ctx=8192, verbose=False)
    except Exception:
        return None


def _llama_stream(
    llm: Any,
    messages: list[dict[str, str]],
    opts: dict[str, Any],
    stopped: Callable[[], bool],
) -> Iterator[str]:
    stream = llm.create_chat_completion(
        messages=messages,
        max_tokens=opts["num_predict"],
        temperature=opts["temperature"],
        stream=True,
    )
    for chunk in stream:
        if stopped():
            break
        delta = ((chunk.get("choices") or [{}])[0].get("delta") or {}).get("content") or ""
        if delta:
            yield delta
