"""Official Premier League source adapter.

Access status verified 2026-11-11 on this machine:

* Premier League team/league sites publish match-summary pages only -- no
  per-goal clips are published there.
* ``video.premierleague.com`` player -> redirects to a Microsoft sign-in,
  i.e. the stream is gated behind an account.
* ``resources.premierleague.pulselive.com`` (the .mp4/.m3u8 file CDN) ->
  ``403 Forbidden`` without credentials.
* PL data feed host ``sport.premierleague.com`` does not resolve from this
  sandbox.

Because of that, the raw goal clips must be supplied (or the platform
released) before step 3 of the pipeline can download real footage.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .match import GoalEvent, Match

SOURCE_STATUS = {
    "official_team_sites": {
        "claims_to": "official club/team match pages",
        "status": "no goal clips (summary pages only)",
        "provides": "match summaries, lineups",
        "note": "team sites do not publish per-goal clips",
    },
    "pl_video_platform": {
        "claims_to": "official Premier League video platform",
        "status": "requires authentication (MSFT sign-in / 403 on CDN)",
        "provides": "match highlights, per-match goals video",
        "workaround": "none unattended",
    },
    "pl_data_feed": {
        "claims_to": "PL match-event data (scorers, minutes)",
        "status": "does not resolve from this sandbox",
        "provides": "goal events",
        "workaround": "fetch in an environment where DNS resolves",
    },
}


@dataclass(frozen=True)
class ClipSource:
    """What is backing a goal clip; filled in by the adapter."""

    name: str
    url: str
    status: str
    note: str = ""


def fixture_sources(week: int = 10, season: str = "2026-27") -> Iterable[ClipSource]:
    """Return the official sources relevant to this match week (metadata only)."""
    yield ClipSource(
        "pl_best_goals_page", "https://www.premierleague.com/en/video/",
        "auth-required", "MW10 best-goals hub",
    )
    yield ClipSource(
        "pl_match_platform", "https://video.premierleague.com",
        "auth-required", "per-match goals HLS/mp4",
    )


def resolve_goal_clip(match_id: str, minute: int) -> ClipSource:
    """Resolve a clip reference for a goal at ``minute``.

    Current state: every goal currently resolves to a *pending* source until
    official access is available. Do not fabricate clip URLs here.
    """
    return ClipSource(
        name="pending_official_source",
        url="",
        status="awaiting_official_access",
        note=(
            "PL video platform requires auth; team sites publish no goal clips. "
            "Provide an unauthenticated goal-clip source to unblock."
        ),
    )


def fetch_goal_events(match: Match, _week: int = 10) -> list[GoalEvent]:
    """Placeholder source adapter for goal events.

    In a fully unblocked build this would hit the official PL data feed and
    return real scorer/minute/type data. Here it returns the schema ready
    for that call; the fixture file carries no goal data yet by design.
    """
    return match.goals
