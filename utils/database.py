"""
utils/database.py
-----------------
Central data-access layer for the DSA Companion CLI.

**No other module should read or write the JSON data files directly.**
All access goes through the functions in this module, which provides:

* **Loading / saving** — ``problems.json``, ``progress.json``,
  ``notes.json``, ``topics.json``.
* **Lookups** — by ID, name, topic, platform, tag, difficulty.
* **Fuzzy search** — case-insensitive substring + token matching with
  optional filters (topic, difficulty, platform, solved, favorite,
  revision_due).
* **Progress tracking** — mark solved / revision / favorite.
* **Notes** — stored separately in ``notes.json``.

Data model
----------
Static data (never modified after import):
    ``data/problems.json``
    ``data/topics.json``

User data (mutated by CLI commands):
    ``data/progress.json``
    ``data/notes.json``
"""

from __future__ import annotations

import json
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import utils.config as cfg


# ─────────────────────────────────────────────────────────────────────────────
#  Paths
# ─────────────────────────────────────────────────────────────────────────────

_DATA_DIR: Path = cfg.BASE_DIR / "data"
_PROBLEMS_PATH: Path = _DATA_DIR / "problems.json"
_PROGRESS_PATH: Path = _DATA_DIR / "progress.json"
_NOTES_PATH: Path = _DATA_DIR / "notes.json"
_TOPICS_PATH: Path = _DATA_DIR / "topics.json"


# ─────────────────────────────────────────────────────────────────────────────
#  Private I/O helpers
# ─────────────────────────────────────────────────────────────────────────────

def _read_json(path: Path, default: Any = None) -> Any:
    """Read and return parsed JSON from *path*.

    Returns *default* (or ``None``) if the file does not exist.

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not path.exists():
        return default if default is not None else None
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, data: Any) -> None:
    """Write *data* as pretty-printed JSON to *path*.

    Creates parent directories if they don't exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Problems  (static data — read-only after import)
# ─────────────────────────────────────────────────────────────────────────────

def load_problems() -> list[dict[str, Any]]:
    """Load all problems from ``data/problems.json``.

    Returns:
        A list of problem dicts, or an empty list if the file is absent.
    """
    return _read_json(_PROBLEMS_PATH, default=[])


def save_problems(problems: list[dict[str, Any]]) -> None:
    """Write the problems list to ``data/problems.json``.

    This should only be called by the importer.  Normal CLI usage
    should never modify the problems file.
    """
    _write_json(_PROBLEMS_PATH, problems)


# ─────────────────────────────────────────────────────────────────────────────
#  Topics  (derived from problems — read-only after import)
# ─────────────────────────────────────────────────────────────────────────────

def load_topics() -> dict[str, dict[str, int]]:
    """Load the topic hierarchy from ``data/topics.json``.

    Returns:
        A nested dict ``{topic: {subtopic: count}}``, or ``{}`` if absent.
    """
    return _read_json(_TOPICS_PATH, default={})


# ─────────────────────────────────────────────────────────────────────────────
#  Progress  (user data)
# ─────────────────────────────────────────────────────────────────────────────

def _default_progress() -> dict[str, Any]:
    """Return a fresh, empty progress structure."""
    return {
        "solved": [],
        "favorites": [],
        "revision1": [],
        "revision2": [],
        "revision3": [],
    }


def load_progress() -> dict[str, Any]:
    """Load user progress from ``data/progress.json``.

    Returns:
        The progress dict, or an initialised default if absent.
    """
    data = _read_json(_PROGRESS_PATH)
    if data is None:
        return _default_progress()
    # Ensure all expected keys exist (forward compatibility)
    default = _default_progress()
    for key in default:
        data.setdefault(key, default[key])
    return data


def save_progress(progress: dict[str, Any]) -> None:
    """Persist user progress to ``data/progress.json``."""
    _write_json(_PROGRESS_PATH, progress)


# ─────────────────────────────────────────────────────────────────────────────
#  Notes  (user data — stored separately)
# ─────────────────────────────────────────────────────────────────────────────

def load_notes() -> dict[str, dict[str, str]]:
    """Load user notes from ``data/notes.json``.

    Returns:
        A dict mapping problem ID → ``{"note": ..., "updated": ...}``,
        or ``{}`` if absent.
    """
    return _read_json(_NOTES_PATH, default={})


def save_notes(notes: dict[str, dict[str, str]]) -> None:
    """Persist user notes to ``data/notes.json``."""
    _write_json(_NOTES_PATH, notes)


# ─────────────────────────────────────────────────────────────────────────────
#  Lookup functions
# ─────────────────────────────────────────────────────────────────────────────

def find_by_id(problem_id: str) -> dict[str, Any] | None:
    """Find a single problem by its original BugAddr ID.

    Args:
        problem_id: The string ID (e.g. ``"srinpttpt"``).

    Returns:
        The matching problem dict, or ``None``.
    """
    for prob in load_problems():
        if prob["id"] == problem_id:
            return prob
    return None


def find_by_name(name: str) -> dict[str, Any] | None:
    """Find a problem by exact name match (case-insensitive).

    Args:
        name: The problem name to match.

    Returns:
        The first matching problem dict, or ``None``.
    """
    name_lower = name.lower()
    for prob in load_problems():
        if prob["name"].lower() == name_lower:
            return prob
    return None


def find_by_topic(topic: str) -> list[dict[str, Any]]:
    """Return all problems belonging to *topic* (case-insensitive).

    Args:
        topic: The topic name to filter by.

    Returns:
        A list of matching problems (may be empty).
    """
    topic_lower = topic.lower()
    return [p for p in load_problems() if p["topic"].lower() == topic_lower]


def find_by_platform(platform: str) -> list[dict[str, Any]]:
    """Return problems that have a non-empty link for *platform*.

    Args:
        platform: One of ``"gfg"``, ``"leetcode"``, ``"codestudio"``,
                  ``"youtube"``, ``"editorial"``, ``"original"``.

    Returns:
        A list of problems with a link on that platform.
    """
    return [
        p for p in load_problems()
        if p.get("platforms", {}).get(platform, "")
    ]


def find_by_tag(tag: str) -> list[dict[str, Any]]:
    """Return problems that include *tag* (case-insensitive).

    Args:
        tag: The tag to search for.

    Returns:
        A list of matching problems.
    """
    tag_lower = tag.lower()
    return [
        p for p in load_problems()
        if any(t.lower() == tag_lower for t in p.get("tags", []))
    ]


def find_solved() -> list[dict[str, Any]]:
    """Return all problems marked as solved.

    Returns:
        A list of problem dicts whose IDs appear in
        ``progress.solved``.
    """
    progress = load_progress()
    solved_ids = set(progress.get("solved", []))
    return [p for p in load_problems() if p["id"] in solved_ids]


def find_unsolved() -> list[dict[str, Any]]:
    """Return all problems NOT marked as solved.

    Returns:
        A list of problem dicts whose IDs do not appear in
        ``progress.solved``.
    """
    progress = load_progress()
    solved_ids = set(progress.get("solved", []))
    return [p for p in load_problems() if p["id"] not in solved_ids]


def find_favorites() -> list[dict[str, Any]]:
    """Return all problems marked as favorites.

    Returns:
        A list of problem dicts whose IDs appear in
        ``progress.favorites``.
    """
    progress = load_progress()
    fav_ids = set(progress.get("favorites", []))
    return [p for p in load_problems() if p["id"] in fav_ids]


def find_revision_due(level: int = 0) -> list[dict[str, Any]]:
    """Return problems marked for revision at *level* (1, 2, or 3).

    If *level* is 0, returns problems in any revision list.

    Args:
        level: The revision tier (0 for all, 1–3 for specific).

    Returns:
        A list of matching problem dicts.
    """
    progress = load_progress()

    if level == 0:
        rev_ids: set[str] = set()
        for key in ("revision1", "revision2", "revision3"):
            rev_ids.update(progress.get(key, []))
    else:
        key = f"revision{level}"
        rev_ids = set(progress.get(key, []))

    return [p for p in load_problems() if p["id"] in rev_ids]


# ─────────────────────────────────────────────────────────────────────────────
#  Search  (fuzzy + filterable)
# ─────────────────────────────────────────────────────────────────────────────

def search(
    query: str = "",
    *,
    topic: str | None = None,
    difficulty: str | None = None,
    platform: str | None = None,
    solved: bool | None = None,
    favorite: bool | None = None,
    revision_due: bool | None = None,
) -> list[dict[str, Any]]:
    """Search problems with fuzzy text matching and optional filters.

    The search is designed for **extensibility** — new filters can be
    added by simply adding parameters and a corresponding filter block.

    Fuzzy matching:
        Case-insensitive substring match on the problem name.  Results
        are ranked by ``difflib.SequenceMatcher`` ratio so that closer
        matches appear first.

    Args:
        query:        Free-text search term (matched against name).
        topic:        Filter by topic (case-insensitive).
        difficulty:   Filter by difficulty (case-insensitive).
        platform:     Filter to problems that have a link on this
                      platform (e.g. ``"leetcode"``).
        solved:       ``True`` = only solved, ``False`` = only unsolved,
                      ``None`` = no filter.
        favorite:     ``True`` = only favorites, ``False`` = only
                      non-favorites, ``None`` = no filter.
        revision_due: ``True`` = only problems in any revision list,
                      ``False`` = only non-revision, ``None`` = no
                      filter.

    Returns:
        A list of matching problems sorted by relevance (best match
        first).  When *query* is empty, results are returned in sheet
        order.
    """
    problems = load_problems()
    progress = load_progress()

    # Pre-compute sets for progress-based filters
    solved_ids = set(progress.get("solved", []))
    fav_ids = set(progress.get("favorites", []))
    rev_ids: set[str] = set()
    for key in ("revision1", "revision2", "revision3"):
        rev_ids.update(progress.get(key, []))

    # ── Apply filters ─────────────────────────────────────────────────────
    candidates = problems

    if topic is not None:
        topic_lower = topic.lower()
        candidates = [p for p in candidates if p["topic"].lower() == topic_lower]

    if difficulty is not None:
        diff_lower = difficulty.lower()
        candidates = [p for p in candidates if p["difficulty"].lower() == diff_lower]

    if platform is not None:
        candidates = [
            p for p in candidates
            if p.get("platforms", {}).get(platform, "")
        ]

    if solved is True:
        candidates = [p for p in candidates if p["id"] in solved_ids]
    elif solved is False:
        candidates = [p for p in candidates if p["id"] not in solved_ids]

    if favorite is True:
        candidates = [p for p in candidates if p["id"] in fav_ids]
    elif favorite is False:
        candidates = [p for p in candidates if p["id"] not in fav_ids]

    if revision_due is True:
        candidates = [p for p in candidates if p["id"] in rev_ids]
    elif revision_due is False:
        candidates = [p for p in candidates if p["id"] not in rev_ids]

    # ── Fuzzy text matching ───────────────────────────────────────────────
    if not query:
        return candidates

    query_lower = query.lower()
    scored: list[tuple[float, dict[str, Any]]] = []

    for prob in candidates:
        name_lower = prob["name"].lower()

        # Fast reject: require at least a substring match
        if query_lower not in name_lower:
            # Also check individual query tokens (for multi-word queries)
            tokens = query_lower.split()
            if not all(tok in name_lower for tok in tokens):
                continue

        # Score by sequence similarity for ranking
        ratio = SequenceMatcher(None, query_lower, name_lower).ratio()
        scored.append((ratio, prob))

    # Sort by descending relevance
    scored.sort(key=lambda x: x[0], reverse=True)
    return [prob for _, prob in scored]


# ─────────────────────────────────────────────────────────────────────────────
#  Mutation helpers  (modify user data only)
# ─────────────────────────────────────────────────────────────────────────────

def mark_solved(problem_id: str) -> bool:
    """Add *problem_id* to the solved list.

    Args:
        problem_id: The problem's original BugAddr ID.

    Returns:
        ``True`` if the ID was newly added, ``False`` if already present.
    """
    progress = load_progress()
    if problem_id in progress["solved"]:
        return False
    progress["solved"].append(problem_id)
    save_progress(progress)
    return True


def mark_unsolved(problem_id: str) -> bool:
    """Remove *problem_id* from the solved list.

    Args:
        problem_id: The problem's original BugAddr ID.

    Returns:
        ``True`` if the ID was removed, ``False`` if it wasn't there.
    """
    progress = load_progress()
    if problem_id not in progress["solved"]:
        return False
    progress["solved"].remove(problem_id)
    save_progress(progress)
    return True


def mark_revision(problem_id: str, level: int) -> bool:
    """Add *problem_id* to the specified revision tier.

    Args:
        problem_id: The problem's original BugAddr ID.
        level:      Revision tier (1, 2, or 3).

    Returns:
        ``True`` if the ID was newly added, ``False`` if already present.

    Raises:
        ValueError: If *level* is not 1, 2, or 3.
    """
    if level not in (1, 2, 3):
        raise ValueError(f"Revision level must be 1, 2, or 3 — got {level}")

    key = f"revision{level}"
    progress = load_progress()
    if problem_id in progress[key]:
        return False
    progress[key].append(problem_id)
    save_progress(progress)
    return True


def mark_favorite(problem_id: str) -> bool:
    """Add *problem_id* to the favorites list.

    Args:
        problem_id: The problem's original BugAddr ID.

    Returns:
        ``True`` if the ID was newly added, ``False`` if already present.
    """
    progress = load_progress()
    if problem_id in progress["favorites"]:
        return False
    progress["favorites"].append(problem_id)
    save_progress(progress)
    return True


def remove_favorite(problem_id: str) -> bool:
    """Remove *problem_id* from the favorites list.

    Args:
        problem_id: The problem's original BugAddr ID.

    Returns:
        ``True`` if the ID was removed, ``False`` if it wasn't there.
    """
    progress = load_progress()
    if problem_id not in progress["favorites"]:
        return False
    progress["favorites"].remove(problem_id)
    save_progress(progress)
    return True


def update_problem(problem_id: str, updates: dict[str, Any]) -> bool:
    """Update fields on a problem in ``problems.json``.

    .. warning::
        This is intended for administrative corrections only.  Normal
        CLI usage should never modify the problems file.

    Args:
        problem_id: The problem's original BugAddr ID.
        updates:    A dict of field names → new values.

    Returns:
        ``True`` if the problem was found and updated, ``False`` otherwise.
    """
    problems = load_problems()
    for prob in problems:
        if prob["id"] == problem_id:
            prob.update(updates)
            save_problems(problems)
            return True
    return False


def get_note(problem_id: str) -> dict[str, str] | None:
    """Get the note for a specific problem.

    Returns:
        Dict with 'note' and 'updated' keys, or None.
    """
    return load_notes().get(problem_id)


def update_note(problem_id: str, text: str) -> None:
    """Update or create a note for a problem, with timestamp."""
    notes = load_notes()
    notes[problem_id] = {
        "note": text,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_notes(notes)


def delete_note(problem_id: str) -> bool:
    """Delete a note for a problem."""
    notes = load_notes()
    if problem_id in notes:
        del notes[problem_id]
        save_notes(notes)
        return True
    return False
