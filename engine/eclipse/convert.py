"""Convert rent test. Convert is an optimizer, not a Ready gate."""

from __future__ import annotations

MIN_FREE_AFTER = 40 * 1024**3
MAX_ENGINE_RATIO = 1.6


def rent_test(
    *,
    size_bytes: int,
    free_bytes: int,
    cuts_fit: bool = False,
    eta_cut: float = 0.0,
    engine_ratio: float = 1.0,
) -> tuple[bool, str]:
    """Return (should_convert, reason)."""
    if size_bytes <= 0:
        return False, "Size unknown — convert waits."
    if free_bytes - int(size_bytes * max(engine_ratio, 1.0)) < MIN_FREE_AFTER:
        return False, "Skip convert — keep disk headroom (≥40 GB after)."
    if engine_ratio > MAX_ENGINE_RATIO:
        return False, "Engine file would be too big versus the original."
    if cuts_fit:
        return True, "Convert pays rent — changes a ladder from won’t-fit to fits."
    if eta_cut >= 0.20:
        return True, "Convert pays rent — ETA drop ≥ 20%."
    return False, "Eager is enough — convert can wait."
