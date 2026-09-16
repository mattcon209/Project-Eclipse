"""Optimization-first checklist. Every box must pass."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eclipse.pass_through import unchanged
from eclipse.resource_os import (
    DISK_REFUSE_PCT,
    HEADROOM_MB,
    LONG_DISCONNECT_SEC,
    USABLE_VRAM_MB,
    ModelCard,
    ResourceOS,
)

SDXL = ModelCard("sdxl", "image", vram_balanced_mb=7000, size_bytes=7_000_000_000)
TINY = ModelCard("tiny", "text", vram_balanced_mb=2000, size_bytes=1_000_000_000)
HUGE = ModelCard("huge", "video", vram_balanced_mb=20000, size_bytes=40_000_000_000)


def os_fresh() -> ResourceOS:
    r = ResourceOS()
    r.register(SDXL)
    r.register(TINY)
    r.register(HUGE)
    r.disk_free_bytes = 300 * 1024**3
    r.disk_used_pct = 68.0
    return r


# --- BOX-01 Resource OS: mode lease, consecutive warm, swap on mode/model ---


def test_box01_mode_enter_loads_once():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    assert r.reloads == 1
    assert r.mode == "image"
    assert r.model_id == "sdxl"


def test_box01_consecutive_prompts_do_not_reload():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    for _ in range(10):
        out = r.run("wet concrete corridor")
        assert out.warm
        assert out.reloaded is False
        assert out.refused is False
        assert out.first_byte_event == "first_byte"
    assert r.reloads == 1
    assert r.prompts_in_mode == 10
    assert r.kpis()["reloads_count"] == 1


def test_box01_pause_is_not_exit():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    r.run("one")
    r.enter_mode("image", "sdxl")  # still looking at the result
    r.run("two")
    assert r.reloads == 1
    assert r.last_action == "run-warm"


def test_box01_mode_switch_unloads():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    r.enter_mode("chat", "tiny")
    assert r.unloads == 1
    assert r.reloads == 2
    assert r.mode == "chat"
    assert r.model_id == "tiny"


def test_box01_model_switch_reloads_once():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    r.switch_model("tiny")
    assert r.reloads == 2
    assert r.unloads == 1
    r.run("x")
    r.run("y")
    assert r.reloads == 2


# --- BOX-02 first byte before done ---


def test_box02_first_byte_precedes_success():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    out = r.run("fog")
    assert out.first_byte_event == "first_byte"
    assert out.queued is False
    assert out.refused is False


# --- BOX-03 size-gate acquire ---


def test_box03_refuse_when_download_bigger_than_free():
    r = os_fresh()
    r.disk_free_bytes = 1_000
    ok, reason = r.can_acquire(10_000)
    assert ok is False
    assert "disk" in reason.lower()


def test_box03_refuse_at_92_percent():
    r = os_fresh()
    r.disk_used_pct = DISK_REFUSE_PCT
    ok, reason = r.can_acquire(100)
    assert ok is False


def test_box03_allow_when_there_is_room():
    r = os_fresh()
    ok, reason = r.can_acquire(1_000_000)
    assert ok is True
    assert reason is None


# --- BOX-04 will-it-fit / refuse-early (hardware only) ---


def test_box04_huge_model_refuses_before_run():
    r = os_fresh()
    r.enter_mode("video", "huge")
    est = r.estimate("huge", "balanced")
    assert est.fits is False
    assert str(USABLE_VRAM_MB) in (est.reason or "")
    out = r.run("long clip")
    assert out.refused is True
    assert "not allowed" not in (out.refuse_reason or "").lower()
    assert "content" not in (out.refuse_reason or "").lower()


def test_box04_sdxl_balanced_fits():
    r = os_fresh()
    est = r.estimate("sdxl", "balanced")
    assert est.fits is True
    assert est.vram_mb <= USABLE_VRAM_MB
    assert HEADROOM_MB == 1536


def test_box04_max_may_refuse_when_over_headroom():
    r = os_fresh()
    r.register(ModelCard("tight", "image", vram_balanced_mb=14000, size_bytes=1))
    est = r.estimate("tight", "max")  # 14000 * 1.15 > usable
    assert est.fits is False


# --- BOX-05 ladders exist and change estimates ---


def test_box05_fast_uses_less_vram_than_quality():
    r = os_fresh()
    f = r.estimate("sdxl", "fast")
    q = r.estimate("sdxl", "quality")
    assert f.vram_mb < q.vram_mb


# --- BOX-06 one heavy job ---


def test_box06_second_heavy_job_queues():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    assert r.begin_heavy("job-a") is True
    out = r.run("another", job_id="job-b")
    assert out.queued is True
    assert out.reloaded is False
    r.end_heavy("job-a")
    out2 = r.run("another", job_id="job-b")
    assert out2.queued is False


# --- BOX-07 no content filter ---


def test_box07_prompt_pass_through_horror():
    text = "gore, first-person horror, wet concrete, a body in the doorway, unfiltered"
    assert unchanged(text) is text or unchanged(text) == text
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    out = r.run(text)
    assert out.prompt == text
    assert out.refused is False


def test_box07_empty_and_unicode_unchanged():
    assert unchanged("") == ""
    assert unchanged("走廊 · 钨丝灯") == "走廊 · 钨丝灯"


# --- BOX-08 long disconnect is the only idle unload ---


def test_box08_short_disconnect_keeps_lease():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    r.disconnect(at=0)
    r.tick(now=60)
    assert r.model_id == "sdxl"
    assert r.mode == "image"


def test_box08_long_disconnect_unloads():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    r.disconnect(at=0)
    r.tick(now=LONG_DISCONNECT_SEC)
    assert r.model_id is None
    assert r.mode is None
    assert r.last_action == "long-disconnect-unload"


# --- BOX-09 make without model refuses honestly (no fake artifact) ---


def test_box09_no_model_no_fake_picture():
    r = os_fresh()
    r.enter_mode("image", None)
    out = r.run("a hallway")
    assert out.refused is True
    assert "model" in (out.refuse_reason or "").lower()


# --- BOX-10 KPI: reloads = 1 per mode enter + 1 per model switch ---


def test_box10_reload_kpi_for_an_image_session():
    r = os_fresh()
    r.enter_mode("image", "sdxl")
    for i in range(7):
        r.run(f"still {i}")
    assert r.kpis()["reloads_count"] == 1
    r.switch_model("tiny")
    r.run("x")
    assert r.kpis()["reloads_count"] == 2
