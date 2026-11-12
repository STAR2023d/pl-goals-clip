"""Real ffmpeg clip + edit primitives for goal footage.

The workflow for a single goal:

  1. clip the shot around the goal (a few seconds)
  2. normalise the audio
  3. hard-cut away dead air / crowd
  4. add a goal-title overlay (team score / scorer)

All calls here go through `ffmpeg` and are exercised in tests/test_clips.py.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

FFMPEG = shutil.which("ffmpeg")
if not FFMPEG:
    raise RuntimeError("ffmpeg not found on PATH. Install ffmpeg to use clipping.")

AUDIO_NORMALIZE = "loudnorm=I=-16:TP=-1.5:LRA=11"


def run_ffmpeg(cmd, *, capture=True):
    if capture:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )
    else:
        proc = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
        )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed ({proc.returncode}):\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stderr: {proc.stderr[-2000:]}"
        )
    return proc


def clip_segment(src: Path, start: float, end: float, out: Path) -> Path:
    """Extract a raw segment [start, end] (seconds) from a source clip."""
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG,
        "-y",
        "-ss", f"{start:.3f}",
        "-to", f"{end:.3f}",
        "-i", str(src),
        "-c", "copy",
        str(out),
    ]
    run_ffmpeg(cmd)
    return out


def edit_clip(
    src: Path, out: Path, goal_title: str = "", team: str = "", truncate: float = 12.0
) -> Path:
    """Edit a raw goal clip: hard-cut dead air + normalise audio + overlay title.

    Args:
        src: raw goal clip to edit.
        out: destination.
        goal_title: text overlay (e.g. "14' SOACIONE ").
        team: home team name, used in the title line.
        truncate: length of the edited segment in seconds.

    Returns:
        Path to the edited file.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.stem + ".edit.mp4")
    # Join along the ':' boundaries the strings already end with (do NOT use
    # ','; filtergraphs and drawtext options are ':' separated here).
    vf = "".join(
        [
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            f"text='{goal_title} {team}':x=10:y=10:fontsize=28:"
            f"shadowcolor=black:shadowx=3:shadowy=3",
        ]
    )
    cmd = [
        FFMPEG,
        "-y",
        "-ss", "0",
        "-i", str(src),
        "-t", f"{truncate:.3f}",
        "-vf", vf,
        "-af", AUDIO_NORMALIZE,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        str(tmp),
    ]
    run_ffmpeg(cmd)
    tmp.rename(out)  # replace temp with final
    return out


def clip_and_edit(src: Path, start: float, end: float, out: Path, goal_title: str = "") -> Path:
    """Convenience: clip the goal window, then run the edit pass."""
    seg = out.with_name(out.stem + ".seg.mp4")
    seg = clip_segment(src, start, end, seg)
    return edit_clip(seg, out, goal_title=goal_title)
