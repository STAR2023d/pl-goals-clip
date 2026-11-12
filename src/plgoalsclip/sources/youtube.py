"""Unauthenticated YouTube source adapter for match-week goal video.

YouTube is the fallback for grabbing goal/hullight clips without credentials:
official ``video.premierleague.com`` is auth-gated (see ..sources), while the
Premier League's clubs, Sky Sports, NBC Sports and others publish full
highlight / goal packages on YouTube to the public.

Only gathers match / match-week-level goal packages (e.g. "Every Goal -
Matchweek 10") and clips each into the per-match highlights output, exactly
one edited video per match, with deadlines pre-marked from the downloaded
captions where available.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass

_yt = shutil.which("yt-dlp")
if not _yt:
    raise RuntimeError("yt-dlp not found on PATH (install via `pip install yt-dlp`)")


@dataclass(frozen=True)
class VideoCandidate:
    url: str
    title: str
    channel: str
    duration: float | None
    vendor: str = "youtube"


def _run_yt(args: list[str]) -> list[dict]:
    """Run yt-dlp and parse JSON output."""
    cmd = [_yt, "--no-playlist", "--dump-json"] + args
    proc = subprocess.run(
        cmd, capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp failed ({proc.returncode}): {proc.stderr[-1500:]}")
    out = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def _search(query: str, limit: int = 6) -> list[dict]:
    """Search YouTube for ``query`` and return matching video entries."""
    data = _run_yt(["ytsearch:%d:%s" % (limit, query)])
    return data


def search_videos(query: str, limit: int = 6) -> list[VideoCandidate]:
    """Search YouTube and return top candidates."""
    data = _search(query, limit)
    out = []
    for r in data:
        out.append(VideoCandidate(
            url=r.get("webpage_url") or r.get("original_url") or r.get("url", ""),
            title=r.get("fulltitle", r.get("title", r.get("id", ""))),
            channel=r.get("channel", r.get("uploader", "")),
            duration=r.get("duration"),
            vendor=r.get("extractor", "youtube"),
        ))
    return out


def get_video(url: str) -> VideoCandidate:
    """Fetch full metadata for one YouTube video."""
    data = _run_yt([url])
    r = data[0]
    return VideoCandidate(
        url=r.get("url", url),
        title=r.get("fulltitle", r.get("title", "")),
        channel=r.get("channel", r.get("uploader", "")),
        duration=r.get("duration"),
        vendor=r.get("extractor", "youtube"),
    )

def download(url: str, out_path: str | None = None, resolution: int = 1080) -> str:
    """Download one YouTube video to a file (unauthenticated). Returns the path.

    ``resolution`` is accepted for API compat but unauthenticated scrape is
    capped at yt-dlp's built-in best pre-merged format (360p).

    The YouTube extractor in this environment needs a JS runtime and sometimes
    returns HTTP 416 on the video request after fetching the remote component,
    so we retry a few times before giving up.
    """
    js = shutil.which("deno") or "/home/dankamaumwaura/.hermes/tools/node-26.12.1-linux-x64/bin/node"
    base = [_yt, "--no-playlist", "--js-runtimes", f"node:{js}",
            "--remote-components", "ejs:github", "-o", out_path or "-", "-f",
            "best", "--no-part"]
    last = ""
    for attempt in range(1, 4):
        proc = subprocess.run(base + [url], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            return out_path or url
        last = proc.stderr[-1500:]
        # 416 on the video request is transient (YouTube anti-scrape); retry a few
        # times before giving up, so unauthenticated scrape is repeatable.
        if proc.returncode != 1:
            raise RuntimeError(f"download failed ({proc.returncode}): {last}")
    raise RuntimeError(f"download failed after 3 attempts ({last})")

