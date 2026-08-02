"""
importers/validate.py
---------------------
Post-import validation for ``data/problems.json``.

Checks for data-quality issues that could break downstream consumers
(CLI commands, statistics, search, future React frontend).

Validation rules
~~~~~~~~~~~~~~~~
1. Duplicate IDs
2. Duplicate problem names (within the same topic)
3. Missing topics or subtopics
4. Missing difficulty
5. Missing practice links (GFG / LeetCode / CodeStudio all empty)
6. Invalid URL format
7. Empty problem names

Each issue is categorised as either an **error** (data integrity) or a
**warning** (cosmetic / completeness).  The report is printed to
stdout with colour-coded summaries.
"""

from __future__ import annotations

import json
from pathlib import Path

import utils.config as cfg
from utils.ui import print_header


# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

_PROBLEMS_PATH: Path = cfg.BASE_DIR / "data" / "problems.json"

_PRACTICE_PLATFORMS = ("gfg", "leetcode", "codestudio")
_ALL_PLATFORMS = ("gfg", "leetcode", "codestudio", "youtube", "editorial", "original")


# ─────────────────────────────────────────────────────────────────────────────
#  Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _is_valid_url(url: str) -> bool:
    """Return ``True`` if *url* looks like a valid HTTP(S) link."""
    return bool(url) and url.startswith(("http://", "https://"))


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def validate() -> bool:
    """Run all validation checks on ``data/problems.json``.

    Prints a formatted report to stdout.

    Returns:
        ``True`` if no errors were found (warnings are acceptable),
        ``False`` if there are hard errors.
    """
    print_header("🔍  Validate problems.json")

    if not _PROBLEMS_PATH.exists():
        print("  ❌  data/problems.json not found.")
        print("     Run the importer first (Menu → Import Problems).\n")
        return False

    with _PROBLEMS_PATH.open("r", encoding="utf-8") as fh:
        problems: list[dict] = json.load(fh)

    errors: list[str] = []
    warnings: list[str] = []

    # ── 1. Duplicate IDs ──────────────────────────────────────────────────
    seen_ids: dict[str, int] = {}
    for idx, prob in enumerate(problems):
        pid = prob.get("id", "")
        if pid in seen_ids:
            errors.append(
                f"Duplicate ID '{pid}' at index {idx} "
                f"(first seen at index {seen_ids[pid]})"
            )
        else:
            seen_ids[pid] = idx

    # ── 2. Duplicate names (within same topic+subtopic) ───────────────────
    name_keys: dict[str, int] = {}
    for idx, prob in enumerate(problems):
        key = f"{prob.get('topic', '')}|{prob.get('subtopic', '')}|{prob.get('name', '')}"
        if key in name_keys:
            warnings.append(
                f"Duplicate name '{prob.get('name', '')}' in "
                f"'{prob.get('topic', '')}/{prob.get('subtopic', '')}' "
                f"at index {idx} (first at {name_keys[key]})"
            )
        else:
            name_keys[key] = idx

    # ── 3–7. Per-problem checks ───────────────────────────────────────────
    for idx, prob in enumerate(problems):
        pid = prob.get("id", f"index-{idx}")

        # 3. Missing topic / subtopic
        if not prob.get("topic", "").strip():
            errors.append(f"[{pid}] Missing topic")
        if not prob.get("subtopic", "").strip():
            errors.append(f"[{pid}] Missing subtopic")

        # 4. Missing difficulty
        if not prob.get("difficulty", "").strip():
            warnings.append(f"[{pid}] Missing difficulty")

        # 5. Missing all practice links
        platforms = prob.get("platforms", {})
        has_practice_link = any(
            platforms.get(p, "") for p in _PRACTICE_PLATFORMS
        )
        if not has_practice_link:
            warnings.append(
                f"[{pid}] '{prob.get('name', '?')}' — "
                f"no GFG / LeetCode / CodeStudio link"
            )

        # 6. Invalid URLs
        for plat in _ALL_PLATFORMS:
            url = platforms.get(plat, "")
            if url and not _is_valid_url(url):
                errors.append(
                    f"[{pid}] Invalid URL for {plat}: '{url}'"
                )

        # 7. Empty name
        if not prob.get("name", "").strip():
            errors.append(f"[{pid}] Empty problem name")

    # ── Report ────────────────────────────────────────────────────────────
    print(f"\n  Validated {len(problems)} problem(s).\n")

    if errors:
        print(f"  ❌  ERRORS ({len(errors)}):")
        for err in errors:
            print(f"     • {err}")
        print()

    if warnings:
        print(f"  ⚠️  WARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"     • {warn}")
        print()

    if not errors and not warnings:
        print("  ✅  No issues found — data looks clean!\n")
    elif not errors:
        print("  ✅  No hard errors — only cosmetic warnings above.\n")
    else:
        print("  ❌  Validation failed — please review the errors above.\n")

    return len(errors) == 0
