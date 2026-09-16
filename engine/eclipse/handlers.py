"""Handler SDK — stable adapter surface.

New model families plug in here. The APK never learns Python class names.
Phase 1 ships sniff/detect. load/run arrive with the modality phases.
"""

from __future__ import annotations

from typing import Any, Protocol


class Handler(Protocol):
    name: str
    modalities: tuple[str, ...]

    def sniff(self, path: str) -> dict[str, Any] | None:
        """Return a detect record or None if this folder/file is not ours."""

    def estimate_cost(self, path: str, ladder: str) -> dict[str, Any]:
        ...

    def load(self, path: str) -> None:
        ...

    def run(self, prompt: str, **kwargs: Any) -> Any:
        ...

    def unload(self) -> None:
        ...
