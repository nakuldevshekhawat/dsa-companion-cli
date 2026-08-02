"""
utils/scanner.py
----------------
Single source of truth for discovering and parsing problems in the DSA
repository.

Previously, ``file_utils.count_problems`` and
``update_readme._scan_problems`` performed nearly identical directory
walks with subtly different outputs.  This module replaces both with a
single typed scanner so every consumer sees consistent data.

Public API
----------
- ProblemEntry   Typed dataclass representing one discovered problem.
- scan_problems  Walk the repo and return all problems grouped by topic.
- aggregate_stats Compute summary counts from a scan result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProblemEntry:
    """Represents a single discovered problem in the DSA repository.

    Attributes:
        number:     Zero-padded problem number string (e.g. ``"01"``).
        name:       Human-readable problem name (e.g. ``"Largest Element"``).
        topic:      Topic directory name (e.g. ``"Arrays"``).
        platform:   Platform string parsed from README, or ``"—"`` if absent.
        difficulty: Difficulty string parsed from README, or ``"—"`` if absent.
        link:       Problem URL parsed from README, or ``"—"`` if absent.
        rel_path:   POSIX path of the problem folder relative to ``dsa_root``.
        number_int: Numeric value of ``number`` used for correct integer sort.
    """

    number: str
    name: str
    topic: str
    platform: str
    difficulty: str
    link: str
    rel_path: str
    number_int: int = field(init=False)

    def __post_init__(self) -> None:
        # Pre-compute int for sorting so callers don't need to cast
        try:
            self.number_int = int(self.number)
        except ValueError:
            self.number_int = 0


# ─────────────────────────────────────────────────────────────────────────────
#  Private parsing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_folder_name(folder: str) -> tuple[str, str]:
    """Split a folder name into a (number, name) pair.

    Expected format: ``NN_Problem_Name_With_Underscores``.

    Args:
        folder: The raw directory name string.

    Returns:
        A ``(number_str, human_name)`` tuple.  Falls back to
        ``("?", folder)`` if the format is unexpected.

    Examples::

        _parse_folder_name("01_Largest_Element")
        # → ("01", "Largest Element")

        _parse_folder_name("unexpected")
        # → ("?", "unexpected")
    """
    parts = folder.split("_", 1)
    if len(parts) == 2 and parts[0].isdigit():
        return parts[0], parts[1].replace("_", " ")
    return "?", folder


def _parse_readme_metadata(readme_path: Path) -> dict[str, str]:
    """Extract platform, difficulty, and link from a problem's README.md.

    Looks for Markdown table rows matching the pattern::

        | **Key** | Value |

    The link is extracted from a Markdown hyperlink inside the ``**Link**``
    row.

    Args:
        readme_path: Absolute path to the problem's ``README.md``.

    Returns:
        A dict with keys ``"platform"``, ``"difficulty"``, ``"link"``.
        Each defaults to ``"—"`` when the field cannot be parsed.
    """
    meta: dict[str, str] = {"platform": "—", "difficulty": "—", "link": "—"}

    if not readme_path.exists():
        return meta

    for raw_line in readme_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if "**Platform**" in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 2:
                meta["platform"] = cells[-1]

        elif "**Difficulty**" in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 2:
                meta["difficulty"] = cells[-1]

        elif "**Link**" in line:
            match = re.search(r"\[.*?\]\((.*?)\)", line)
            if match:
                meta["link"] = match.group(1)

    return meta


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def scan_problems(dsa_root: Path) -> dict[str, list[ProblemEntry]]:
    """Walk the DSA repository and return all discovered problems by topic.

    A problem folder is identified by the presence of a ``solution.cpp``
    file.  The topic is the immediate parent directory of the problem
    folder.  Problems placed directly under ``dsa_root`` (depth < 2) are
    silently skipped.

    Results within each topic are sorted by ``ProblemEntry.number_int``
    (integer sort, not lexicographic) so that problem 10 always follows 9.

    Args:
        dsa_root: Absolute path to the DSA repository root.

    Returns:
        A ``dict`` mapping topic name → sorted list of :class:`ProblemEntry`.
        Returns an empty dict when no problems are found.

    Example::

        problems = scan_problems(Path("/Users/me/DSA"))
        for topic, entries in problems.items():
            print(topic, len(entries))
    """
    result: dict[str, list[ProblemEntry]] = {}

    for solution_file in dsa_root.rglob("solution.cpp"):
        if "dsa-tool" in solution_file.parts:
            continue
        problem_dir = solution_file.parent
        topic_dir = problem_dir.parent

        # Skip problems with no topic directory (directly under repo root)
        if topic_dir == dsa_root:
            continue

        topic = topic_dir.name
        number, name = _parse_folder_name(problem_dir.name)
        meta = _parse_readme_metadata(problem_dir / "README.md")

        entry = ProblemEntry(
            number=number,
            name=name,
            topic=topic,
            platform=meta["platform"],
            difficulty=meta["difficulty"],
            link=meta["link"],
            rel_path=problem_dir.relative_to(dsa_root).as_posix(),
        )
        result.setdefault(topic, []).append(entry)

    # Sort each topic's problems by integer problem number
    for entries in result.values():
        entries.sort(key=lambda e: e.number_int)

    return result


def aggregate_stats(
    problems: dict[str, list[ProblemEntry]],
) -> dict[str, object]:
    """Compute summary counts from the output of :func:`scan_problems`.

    Args:
        problems: The ``dict[topic, list[ProblemEntry]]`` returned by
                  :func:`scan_problems`.

    Returns:
        A dict with the following structure::

            {
                "total": int,
                "by_topic": {topic_name: count, ...},
                "by_difficulty": {
                    "Easy": int, "Medium": int,
                    "Hard": int, "Unknown": int,
                },
            }
    """
    by_topic: dict[str, int] = {}
    by_difficulty: dict[str, int] = {"Easy": 0, "Medium": 0, "Hard": 0, "Unknown": 0}
    total = 0

    for topic, entries in problems.items():
        by_topic[topic] = len(entries)
        total += len(entries)
        for entry in entries:
            if entry.difficulty in by_difficulty:
                by_difficulty[entry.difficulty] += 1
            else:
                by_difficulty["Unknown"] += 1

    return {"total": total, "by_topic": by_topic, "by_difficulty": by_difficulty}
