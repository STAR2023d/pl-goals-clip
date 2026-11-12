# Source-access verification matrix

Verified 2026-11-11 on this sandbox. Every source used (or considered) for the
match-week goal-clip pipeline was checked **before** the pipeline was built
around it. Blocked sources are recorded inline; the pipeline does **not**
fabricate clips for them.

## Scope

- Topic: Premier League match-week individual-goal clips + edits.
- Example week: Matchweek 10, 2026/27 (played 6-8 Nov 2026).

## Verdict matrix

| # | Source | Role | Access result | Blocked? | Action taken |
|---|--------|------|---------------|----------|--------------|
| 1 | Premier League team/league official sites | Where the user expects clips | Match-summary pages only; no per-goal clips published | Yes | Record as not a clip source; do not fetch clips here |
| 2 | `video.premierleague.com` (PL video platform) | Authoritative goal-clip source | Player → redirects to Microsoft sign-in (auth required) | Yes | Status `auth_required` in `sources.py`; clips remain `pending` |
| 3 | `resources.premierleague.pulselive.com` (file CDN) | Raw .mp4/.m3u8 delivery | `403 Forbidden` without credentials | Yes | Status `403` in `sources.py`; unavailable unattended |
| 4 | `sport.premierleague.com` PL data feed | Goal-event data (scorer, minute, type) | Does not resolve from this sandbox | Yes | Status `unreachable` in `sources.py` |

## Updated verdict (on re-check)

The authoritative source for goal clips — the Premier League video platform
(2) — is the single gating point. Until it is released or an unauthenticated
mirror is supplied, goal clips are `pending` and marked `blocked` in each
per-match manifest (`results/<match_id>/manifest.json`). Data (fixture table,
goal-event schema) is fully built; only the clip-download step is waiting.

## How to unblock

- Authorise access to `video.premierleague.com` (or supply an unauthenticated
  goal-clip mirror), **or**
- Provide a source where individual goal clips are retrievable without
  credentials, then re-point `sources.resolve_goal_clip`.

## Rules honoured

- Verify access before building around a source (done above).
- Never fabricate clip text/content: `goals: []` in manifests until real clips
  arrive; status flagged inline per goal record.
- Package by group: one edited highlights clip per match, not one per goal.
