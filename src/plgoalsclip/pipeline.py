"""End-to-end pipeline: fixtures -> goals -> clips -> per-match outputs."""

from __future__ import annotations

import json
import pathlib
from typing import Iterable

from . import config, sources
from .match import GoalEvent, Match

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
