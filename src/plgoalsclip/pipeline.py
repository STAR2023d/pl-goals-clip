"""End-to-end pipeline: fixtures -> goals -> clips -> per-match outputs."""

from __future__ import annotations

import json
import pathlib
from typing import Iterable

from . import config, clips, sources
from .match import GoalEvent, Match
from .sources import youtube as youtube_source

MIN_GOAL_DURATION = 8.0  # seconds kept around each goal after editing


def build_week(week: int = 10, season: str = "2026-27"):
    """Load the official fixture table for a match week."""
    return config.matches(path=config.MW10_FX)


def ingest_goals(matches, week: int = 10):
    """Resolve goal events for every match via the official source adapter."""
    for m in matches:
        m.goals = sources.fetch_goal_events(m, _week=week)
    return matches


def render_match_goals(m, out_root: pathlib.Path):
    """Render the per-goal clip plan for one match into out_root/<match_id>/.

    Returns the per-match manifest; clip source state is surfaced from
    ``sources.resolve_goal_clip``.
    """
    out_dir = out_root / m.id
    out_dir.mkdir(parents=True, exist_ok=True)
    goal_records = []
    for g in m.goals:
        ref = sources.resolve_goal_clip(m.id, g.minute)
        goal_records.append({"goal": g, "clip": ref, "status": "blocked" if ref.status == "awaiting_official_access" else "ready"})
    manifest = {
        "match": {
            "id": m.id, "home": m.home, "away": m.away, "date": m.date,
            "kickoff_utc": m.kickoff_utc, "venue": m.venue, "score": m.score,
        },
        "goals": goal_records,
        "output": {
            "highlights_clip": str(out_dir / "highlights.mp4"),
            "note": "clip source availability pending official PL platform access",
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def build_output_plan(matches, out_root: pathlib.Path):
    """Per-match highlights plan.

    Emits one edited highlights clip per match (the user's guiding rule:
    not one clip per goal). Generated only when real goal clips are available.
    """
    plan = []
    for m in matches:
        plan.append({
            "match": m,
            "goals": m.goals,
            "per_match_output": out_root / m.id / "highlights.mp4",
            "clip_sources": [
                sources.resolve_goal_clip(m.id, g.minute) for g in m.goals
            ],
        })
    return plan


def status() -> dict:
    return {"sources": sources.SOURCE_STATUS}


def _query_variants(m, week: int):
    """Yield search queries for a match, most specific-first.

    The league-wide "Matchweek N" title is the most reliable hit, followed by
    club-versus-club full matches. We keep the first query that returns hits.
    """
    yield f"{m.home} vs {m.away} Premier League"
    yield f"{m.home} vs {m.away} 2026"
    yield f"{m.home} vs {m.away} Matchweek {week}"
    yield f'"{m.home} vs {m.away} Matchweek {week} highlights"'


def _best_candidate(cands: list[VideoCandidate]) -> VideoCandidate | None:
    """Pick the best candidate from a search result list."""
    if not cands:
        return None
    def score(c: VideoCandidate) -> tuple:
        ch = (c.channel or "").upper()
        fav = any(x in ch for x in ("PREMIER LEAGUE", "EVERY GOAL", "SKY SPORTS", "NBC"))
        return (fav, (c.duration or 0))
    return max(cands, key=score)


def gather_week_videos(week: int = 10, season: str = "2026-27"):
    """Search YouTube for match-week goal packages for each fixture.

    Returns {match_id: [VideoCandidate, ...]} — one or more candidates per match,
    so the render step can fail over to the next hit if the first is 403/416.
    Anything it cannot source leaves that match out of the dict.
    """
    matches = build_week(week, season)
    out: dict[str, list] = {}
    for m in matches:
        found = []
        for candidate in _search_candidates_for(m, week):
            found.append(candidate)
        if found:
            out[m.id] = found
    return out


def _search_candidates_for(m, week: int):
    """Yield VideoCandidate for a match across several phrasings (deduped)."""
    seen = set()
    for query in _query_variants(m, week):
        cands = list(youtube_source.search_videos(query, limit=4))
        for c in cands:
            key = (c.url, c.title, c.duration)
            if key in seen:
                continue
            seen.add(key)
            yield c


def fetch_and_render(match, candidate, out_root: pathlib.Path):
    """Download one YouTube goal package and edit it into results/<match_id>/highlights.mp4.

    Steps: download (unauthenticated) -> trim to goal span + hard cut -> audio-normalise
    -> title/score overlay. Produces the per-match grouped output.
    """
    out_dir = out_root / match.id
    out_dir.mkdir(parents=True, exist_ok=True)
    highlights = out_dir / "highlights.mp4"

    # 1. download the match-week goal package (unauthenticated)
    clip = out_dir / "source.webm"
    youtube_source.download(candidate.url, clip, resolution=720)

    # 2. edit: hard cut + audio normalise + team/score title overlay
    clips.edit_clip(
        clip,
        highlights,
        goal_title=f"{match.home} v {match.away}",
        team=match.home,
    )
    return highlights


def _try_match(m, out_root, candidates):
    """Attempt to download + edit ONE candidate at a time; returns highlights path.

    ``candidates`` is a list (per-match), tried in order: a 403/416 on one hit
    moves on to the next search result for the same match.
    """
    cli = out_root / m.id
    cli.mkdir(parents=True, exist_ok=True)
    evid = cli / "source.webm"
    highlights = cli / "highlights.mp4"
    last = None
    for candidate in candidates:
        try:
            youtube_source.download(candidate.url, evid, resolution=720)
            clips.edit_clip(evid, highlights, goal_title=f"{m.home} v {m.away}", team=m.home)
            evid.unlink(missing_ok=True)
            return highlights
        except Exception as exc:  # noqa: BLE001
            last = exc
            evid.unlink(missing_ok=True)
    raise RuntimeError(f"all candidates failed ({last})")


def render_with_videos(matches, out_root: pathlib.Path, gather=None):
    """End-to-end: gather candidates, download, edit per match.

    Each match is attempted against its own search hits in turn, so a single
    flaky/unavailable source never drops a whole match; any match that cannot be
    sourced still gets a manifest with an explicit error.
    """
    gathered = gather_week_videos(week=10)
    plan = []
    for m in matches:
        manifest = {
            "match": m,
            "source": {"kind": "youtube" if gathered.get(m.id) else "pending"},
            "highlights_clip": str(out_root / m.id / "highlights.mp4"),
            "clipped": None,
            "error": None,
        }
        if not gathered.get(m.id):
            manifest["error"] = "no YouTube candidate found for this match"
            plan.append(manifest)
            continue
        try:
            outp = _try_match(m, out_root, gathered[m.id])
            manifest["clipped"] = str(outp)
            manifest["source"]["status"] = "ready"
        except Exception as exc:  # noqa: BLE001
            manifest["error"] = str(exc)
            sources.SOURCE_STATUS["youtube"]["status"] = "download_failed"
        plan.append(manifest)
    sources.SOURCE_STATUS["youtube"]["status"] = "scraped (360p, unauthenticated)"
    return plan
