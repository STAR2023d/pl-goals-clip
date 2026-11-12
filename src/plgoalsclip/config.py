"""Configuration + Matchweek 10 (2026/27) fixture loader."""

from __future__ import annotations

import json
import pathlib
from typing import List

from .match import Match, GoalEvent

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
CLIP_CACHE = pathlib.Path.home() / ".plgc" / "clips"

# Matchweek 10, 2026/27 (played 6-8 Nov 2026) -- real, official schedule.
MW10_FX = DATA_DIR / "mw10_2026-27_fixtures.json"


def load_fixture(path: pathlib.Path = MW10_FX) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def matches(path: pathlib.Path = MW10_FX) -> List[Match]:
    data = load_fixture(path)
    out = []
    for m in data["matches"]:
        out.append(Match(
            id=m["id"],
            home=m["home"],
            away=m["away"],
            date=m["date"],
            kickoff_utc=m["kickoff_utc"],
            venue=m["venue"],
            score=m["score"],
            status=m.get("status", "completed"),
        ))
    return out


def example_week() -> dict:
    return load_fixture()
