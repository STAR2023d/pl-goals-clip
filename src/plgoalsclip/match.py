"""Data models for a Premier League match and its individual goal events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class GoalEvent:
    """A single scored goal (or negated event) in a match."""

    match_id: str
    minute: int
    scorer: str
    outcome: str  # goal | og | disallowed | missed_pen | off_target | ...
    event_type: str = "open_play"  # open_play | penalty | header | ft | own_goal | ...
    minute_note: Optional[str] = None  # e.g. "96+1", "disallowed"
    clip_ref: Optional[str] = None  # source pointer (set by sources adapter)
    clip_path: Optional[str] = None  # resolved raw clip on disk

    @property
    def display(self) -> str:
        note = f"+{self.minute_note}" if self.minute_note else str(self.minute)
        return f"{note:>4}   {self.scorer:<20} {self.outcome:<14} [{self.event_type}]"


@dataclass
class Match:
    """One completed Premier League match for the week."""

    id: str
    home: str
    away: str
    date: str
    kickoff_utc: str
    venue: str
    score: str
    status: str = "completed"
    goals: list[GoalEvent] = field(default_factory=list)

    @property
    def home_goals(self) -> list[GoalEvent]:
        return [g for g in self.goals if g.event_type != "own_goal"]  # goals that count

    @property
    def away_goals(self) -> list[GoalEvent]:
        return [g for g in self.goals if g.event_type == "own_goal"]

    @property
    def lineups(self) -> str:
        return f"{self.home} {self.score} {self.away}  ({self.date})"
