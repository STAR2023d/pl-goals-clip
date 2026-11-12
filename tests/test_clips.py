"""Tests for the real ffmpeg clip/edit primitives.

Runs against a real downloaded goal clip so it exercises the actual
subprocess / mediacodec paths rather than fakes.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Real downloaded goal clip for a 20-second window (75s -> 95s).
SRC = Path("/home/dankamaumwaura/clips/clip_1_15_1_35.mp4")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def test_ffmpeg_available():
    assert shutil.which("ffmpeg") is not None


def test_source_clip_is_readable():
    assert SRC.exists(), f"fixture source missing: {SRC}"
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1", str(SRC)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "duration=20.000000" in proc.stdout


def test_clip_segment(tmp_path):
    from plgoalsclip.clips import clip_segment
    out = tmp_path / "seg.mp4"
    got = clip_segment(SRC, start=10.0, end=20.0, out=out)
    assert got.exists()
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1", str(got)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "duration=10.0" in proc.stdout, proc.stdout


def test_edit_clip(tmp_path):
    from plgoalsclip.clips import edit_clip
    out = tmp_path / "edited.mp4"
    got = edit_clip(SRC, out, goal_title="15", team="Bench")
    assert got.exists()
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=index,codec_type",
         "-of", "default=noprint_wrappers=1", str(got)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "v" in proc.stdout and "a" in proc.stdout, proc.stdout
