"""Minimal CLI for the pipeline."""

from __future__ import annotations

import argparse
import json
import sys

from . import config, pipeline, sources


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="plgc", description="Premier League match-week goal clip & edit pipeline",
    )
    sub = p.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="build a match-week dataset")
    p_build.add_argument("week", nargs="?", default=10, type=int, help="match week number")
    p_build.add_argument("--season", default="2026-27", help="season (default 2026-27)")

    sub.add_parser("render", help="render per-match outputs")

    p_yt = sub.add_parser("youtube", help="gather unauthenticated YouTube clips for a match week and edit them")
    p_yt.add_argument("week", nargs="?", default=10, type=int)

    sub.add_parser("status", help="show source access status")
    return p


def _print_table(matches):
    print(f"{'MATCH':<24} {'DATE':<11} {'KICK':<7} {'HOME':>16} {'AWAY':>16} {'SCORE'}")
    print("-" * 90)
    for m in matches:
        print(f"{m.id:<24} {m.date:<11} {m.kickoff_utc:<7} {m.home:>16} {m.away:>16} {m.score}")


def cmd_build(args):
    matches = pipeline.build_week(args.week, args.season)
    print(f"Matchweek {args.week} ({args.season}) fixtures loaded: {len(matches)} matches")
    _print_table(matches)
    print("\nSource access status:")
    for name, st in sources.SOURCE_STATUS.items():
        print(f"  - {name:<26} {st['claims_to']:<24} -> {st['status']}")
    return 0


def cmd_render(args):
    matches = pipeline.build_week(args.week)
    pipeline.ingest_goals(matches, args.week)
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    n_goals = 0
    for m in matches:
        pipeline.render_match_goals(m, config.RESULTS_DIR)
        n_goals += len(m.goals)
    print(f"Matchweek {args.week} rendered: {len(matches)} matches, {n_goals} goal records",
          f"(clips pending official access — see results/<match_id>/manifest.json)")
    return 0


def cmd_youtube(args):
    """Gather unauthenticated YouTube clips for a match week and edit them."""
    matches = pipeline.build_week(args.week)
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    plan = pipeline.render_with_videos(matches, config.RESULTS_DIR)
    for entry in plan:
        status = entry["source"].get("status", "pending")
        print(f"  {entry['match'].id:<24} {entry['match'].home:<16} -> {status:<11} {entry['highlights_clip']}")
    print(f"Matchweek {args.week} youtube render done: {len(plan)} matches")
    return 0


def cmd_status(_args):
    for name, st in sources.SOURCE_STATUS.items():
        print(f"{name:<26}: {st['claims_to']:<24} | {st.get('status', 'n/a')}")
    return 0


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        code = getattr(sys.modules[__name__], f"cmd_{args.command}")(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
