"""YouTube (and other video sources) for the goal-clip pipeline."""

# Status of each source, mutated by the pipeline as clips are gathered.
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
    "youtube": {
        "claims_to": "YouTube channel uploads (Sky Sports, NBC, clubs, etc.)",
        "status": "unavailable",
        "provides": "match-week goal packages / full matches",
        "workaround": "authenticate or supply clips via an API key",
    },
}
