# pl-goals-clip

A repeatable pipeline that **collects individual Premier League goals for a match week, clips each one, and edits it** — then packages things **match-by-match (not one clip per goal)**.

## Where the goal clips come from

This is the important part. Premier League **club/team official websites do not publish individual goal clips** — their match pages are match-summary pages. The official, authoritative source for goal clips is the Premier League's own video platform (`video.premierleague.com`) and its matching goal-hightlight pages.

⚠️ **Source access status (verified here, 2026-11-11)** — I tested the official sources before writing this:

| Source | Access result |
|---|---|
| Official PL team/league sites | Match summaries only — no per-goal clips |
| `video.premierleague.com` player | Redirects to a Microsoft sign-in; **requires auth** |
| `resources.premierleague.pulselive.com` (file CDN) | `403 Forbidden` without credentials |
| PL data feed (`sport.premierleague.com`) | Does not resolve from this sandbox |

So I can **stand up the whole pipeline and the MW10 fixture table** (real, official data), but the raw goal clips require authenticated/unblocked PL access. The `sources.py` module surfaces that status explicitly instead of pretending to have the clips.

## The pipeline (per match week)

1. **Fixtures** — pull the official league match list for the week.
2. **Goal events** — for each match, ingest every goal with minute, scorer and type (from the official PL platform).
3. **Clip each goal** — extract a short window around the goal.
4. **Edit** — normalise audio, hard-cut the rest, add a score/goal title overlay.
5. **Package** — emit **one edited highlights clip per match** (with each goal cut to length and labelled), not a separate short video per goal, plus a per-club aggregated view.

## Example: Matchweek 10, 2026/27

The real fixture table is in `data/mw10_2026-27_fixtures.json` (10 matches, 30+ goals).

Run the demo:

```bash
pip install -e ".[dev]"
python -m plgoalsclip.cli build mw10
```

This builds the MW10 dataset and confirms the fixture stage end-to-end. The clip/editing stage is wired to `sources.py`, which will need the official PL video credentials (see `plgoalsclip/sources.py`), or an alternative unauthenticated goal-clip source you can supply.

## Project layout

```
data/                     # curated datasets (gitignored, except examples)
plgoalsclip/
  config.py      # settings + MW10 fixture loader
  match.py       # Match model
  goal_event.py  # GoalEvent model
  sources.py     # official PL source adapter (access status)
  clips.py       # ffmpeg clip + edit (real, tested)
  pipeline.py    # end-to-end orchestration
  cli.py         # CLI entry point
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```
