"""
commands/stats.py
-----------------
Implements the \"Show Stats\" command with **two independent modes**:

1. **Folder Statistics** — scans ``solution.cpp`` files in the
   repository (preserves the original behaviour exactly).
2. **Database Statistics** — reads from ``problems.json`` +
   ``progress.json`` to show solved/unsolved/completion %.

Both modes coexist so that existing folder-based tracking is never lost.
"""

from __future__ import annotations

import utils.config as cfg
from utils.database import load_problems, load_progress
from utils.file_utils import get_timestamp
from utils.scanner import aggregate_stats, scan_problems
from utils.ui import print_header, print_section, progress_bar, prompt_choice


# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

_DIFFICULTY_ICONS: dict[str, str] = {
    "Easy": "🟢",
    "Medium": "🟡",
    "Hard": "🔴",
    "Unknown": "⚪",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Folder Statistics  (original behaviour — preserved exactly)
# ─────────────────────────────────────────────────────────────────────────────

def _render_folder_difficulty(stats: dict, total: int) -> None:
    """Print the difficulty breakdown with progress bars.

    Args:
        stats: The dict returned by :func:`~utils.scanner.aggregate_stats`.
        total: Total number of problems (used to scale bars).
    """
    print_section("🎯  By Difficulty")
    for difficulty, icon in _DIFFICULTY_ICONS.items():
        count = stats["by_difficulty"].get(difficulty, 0)
        bar = progress_bar(count, total)
        print(f"  {icon}  {difficulty:<8}  {bar}  {count:>3}")


def _render_folder_topics(stats: dict, total: int) -> None:
    """Print the topic breakdown with progress bars, sorted by count.

    Args:
        stats: The dict returned by :func:`~utils.scanner.aggregate_stats`.
        total: Total number of problems (used to scale bars).
    """
    print_section("📂  By Topic")

    by_topic: dict[str, int] = stats["by_topic"]
    if not by_topic:
        print("  No topics found.")
        return

    sorted_topics = sorted(by_topic.items(), key=lambda x: x[1], reverse=True)
    col_width = max(len(topic) for topic, _ in sorted_topics)

    for topic, count in sorted_topics:
        bar = progress_bar(count, total)
        print(f"  📁  {topic:<{col_width}}  {bar}  {count:>3}")


def _run_folder_stats() -> None:
    """Display folder-based statistics (original behaviour)."""
    _, dsa_root = cfg.load()

    print_header("📊  Folder Statistics Dashboard")
    print(f"  Repository : {dsa_root}")
    print(f"  Generated  : {get_timestamp()}")

    problems = scan_problems(dsa_root)
    stats = aggregate_stats(problems)
    total: int = stats["total"]

    print_section("🏆  Overall Progress")
    print(f"  Total Problems Solved: {total}")

    if total == 0:
        print("\n  ℹ️  No problems found yet — go solve some! 💪\n")
        return

    _render_folder_difficulty(stats, total)
    _render_folder_topics(stats, total)

    print(f"\n  {'═' * 48}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Database Statistics  (new — reads from problems.json + progress.json)
# ─────────────────────────────────────────────────────────────────────────────

def _run_database_stats() -> None:
    """Display database-driven statistics from the imported A2Z sheet."""
    print_header("📊  Database Statistics Dashboard")
    print(f"  Generated  : {get_timestamp()}")

    problems = load_problems()
    if not problems:
        print("\n  ℹ️  No problems imported yet.")
        print("     Run the importer first (Menu → Import Problems).\n")
        return

    progress = load_progress()
    solved_ids = set(progress.get("solved", []))

    total = len(problems)
    solved_count = sum(1 for p in problems if p["id"] in solved_ids)
    unsolved_count = total - solved_count
    completion_pct = (solved_count / total * 100) if total else 0.0

    # ── Overall ───────────────────────────────────────────────────────────
    print_section("🏆  Overall Progress")
    bar = progress_bar(solved_count, total, width=30)
    print(f"  Total Problems : {total}")
    print(f"  Solved         : {solved_count}")
    print(f"  Unsolved       : {unsolved_count}")
    print(f"  Completion     : {bar}  {completion_pct:.1f}%")

    # ── By Difficulty ─────────────────────────────────────────────────────
    print_section("🎯  By Difficulty")
    by_diff: dict[str, dict[str, int]] = {}
    for prob in problems:
        diff = prob.get("difficulty", "Unknown")
        by_diff.setdefault(diff, {"total": 0, "solved": 0})
        by_diff[diff]["total"] += 1
        if prob["id"] in solved_ids:
            by_diff[diff]["solved"] += 1

    for diff in ("Easy", "Medium", "Hard", "Unknown"):
        if diff not in by_diff:
            continue
        d = by_diff[diff]
        icon = _DIFFICULTY_ICONS.get(diff, "⚪")
        bar = progress_bar(d["solved"], d["total"])
        pct = (d["solved"] / d["total"] * 100) if d["total"] else 0.0
        print(
            f"  {icon}  {diff:<8}  {bar}  "
            f"{d['solved']:>3}/{d['total']:<3}  ({pct:.0f}%)"
        )

    # ── By Topic ──────────────────────────────────────────────────────────
    print_section("📂  By Topic")
    by_topic: dict[str, dict[str, int]] = {}
    for prob in problems:
        topic = prob.get("topic", "Other")
        by_topic.setdefault(topic, {"total": 0, "solved": 0})
        by_topic[topic]["total"] += 1
        if prob["id"] in solved_ids:
            by_topic[topic]["solved"] += 1

    sorted_topics = sorted(by_topic.items(), key=lambda x: x[1]["total"], reverse=True)
    if sorted_topics:
        col_width = max(len(t) for t, _ in sorted_topics)
        for topic, d in sorted_topics:
            bar = progress_bar(d["solved"], d["total"])
            pct = (d["solved"] / d["total"] * 100) if d["total"] else 0.0
            print(
                f"  📁  {topic:<{col_width}}  {bar}  "
                f"{d['solved']:>3}/{d['total']:<3}  ({pct:.0f}%)"
            )

    print(f"\n  {'═' * 48}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def run() -> None:
    """Display a terminal statistics dashboard.

    Offers the user a choice between the original folder-based scan
    and the new database-driven statistics.
    """
    mode = prompt_choice(
        "Select Statistics Mode:",
        ["Folder Statistics (scan solution files)", "Database Statistics (A2Z sheet)"],
    )

    if mode.startswith("Folder"):
        _run_folder_stats()
    else:
        _run_database_stats()
