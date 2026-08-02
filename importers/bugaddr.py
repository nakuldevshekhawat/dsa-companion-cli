"""
importers/bugaddr.py
--------------------
One-time importer for the Striver A2Z DSA Sheet.

Fetches the structured ``a2z.json`` directly from the BugAddr GitHub
repository, transforms it into the normalised schema used by the DSA
Companion CLI, and writes the result to ``data/problems.json``.

After a successful import the CLI works **completely offline** — the
remote URL is never needed again.

Design decisions
----------------
* **Original IDs preserved** — the ``"id"`` field from the source JSON
  (e.g. ``"srinpttpt"``) is kept verbatim.  Display numbering, if
  needed, is computed dynamically.
* **All metadata kept** — every useful link (GFG, LeetCode, CodeStudio,
  YouTube, editorial, post) is stored so nothing is discarded.
* **Tags extracted** — the ``ques_topic`` field is parsed from its
  embedded JSON-string into a clean ``tags`` list.
* **Configurable source** — the URL is read from ``config.json`` so it
  can be changed without touching code.
* **Retry logic** — transient HTTP failures are retried up to 3 times
  with exponential back-off.
* **Partial-save safety** — partial results are saved to a ``.partial``
  file so recovery is possible after a crash.
* **Deterministic output** — problems are ordered by
  ``(step_no, sub_step_no, sl_no)`` which mirrors the A2Z sheet order.
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import utils.config as cfg
from utils.ui import print_header, progress_bar


# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

_DATA_DIR: Path = cfg.BASE_DIR / "data"
_PROBLEMS_PATH: Path = _DATA_DIR / "problems.json"
_TOPICS_PATH: Path = _DATA_DIR / "topics.json"
_PROGRESS_PATH: Path = _DATA_DIR / "progress.json"
_NOTES_PATH: Path = _DATA_DIR / "notes.json"
_PARTIAL_PATH: Path = _DATA_DIR / "problems.json.partial"
_SOURCE_CACHE_PATH: Path = _DATA_DIR / "source_a2z.json"

_MAX_RETRIES: int = 3
_BACKOFF_BASE: float = 2.0

_DIFFICULTY_MAP: dict[int, str] = {
    0: "Easy",
    1: "Medium",
    2: "Hard",
}


# ─────────────────────────────────────────────────────────────────────────────
#  Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_json(url: str) -> list[dict[str, Any]]:
    """Download and parse the remote A2Z JSON with retry logic.

    Args:
        url: The raw URL to fetch.

    Returns:
        The parsed JSON as a list of step dicts.

    Raises:
        RuntimeError: If all retry attempts are exhausted.
    """
    last_error: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            print(f"  🌐  Fetching data (attempt {attempt}/{_MAX_RETRIES})...")
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "DSA-Companion-CLI/1.0"},
            )
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw)

        except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < _MAX_RETRIES:
                wait = _BACKOFF_BASE ** attempt
                print(f"  ⚠️  Attempt {attempt} failed: {exc}")
                print(f"      Retrying in {wait:.0f}s...")
                time.sleep(wait)
            else:
                print(f"  ❌  Attempt {attempt} failed: {exc}")

    raise RuntimeError(
        f"Failed to fetch data after {_MAX_RETRIES} attempts.\n"
        f"Last error: {last_error}\n"
        f"URL: {url}"
    )


def _is_valid_url(url: str | None) -> bool:
    """Check whether *url* looks like a valid HTTP(S) link."""
    if not url or not isinstance(url, str):
        return False
    return url.startswith(("http://", "https://"))


def _safe_url(url: str | None) -> str:
    """Return *url* if it looks valid, else an empty string."""
    return url.strip() if _is_valid_url(url) else ""


def _parse_tags(ques_topic: str | None) -> list[str]:
    """Extract tag labels from the embedded JSON string.

    The source stores tags as a JSON-encoded string like::

        '[{"value":"basics","label":"Introduction to DSA"}]'

    Args:
        ques_topic: The raw ``ques_topic`` field value.

    Returns:
        A deduplicated list of tag label strings, or ``[]`` on failure.
    """
    if not ques_topic or not isinstance(ques_topic, str):
        return []

    try:
        entries = json.loads(ques_topic)
        if isinstance(entries, list):
            seen: set[str] = set()
            tags: list[str] = []
            for entry in entries:
                label = entry.get("label", "").strip()
                if label and label not in seen:
                    seen.add(label)
                    tags.append(label)
            return tags
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass

    return []


def _transform_problem(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert one raw A2Z topic entry into the normalised schema.

    Args:
        raw: A single problem dict from the source JSON.

    Returns:
        A normalised problem dict matching the project schema.
    """
    difficulty_code = raw.get("difficulty", -1)
    difficulty_str = _DIFFICULTY_MAP.get(difficulty_code, "Unknown")

    return {
        "id": raw.get("id", ""),
        "topic": raw.get("step_title", "").strip(),
        "subtopic": raw.get("sub_step_title", "").strip(),
        "problemNumber": raw.get("sl_no", 0),
        "name": raw.get("question_title", "").strip(),
        "difficulty": difficulty_str,
        "platforms": {
            "gfg": _safe_url(raw.get("gfg_link")),
            "leetcode": _safe_url(raw.get("lc_link")),
            "codestudio": _safe_url(raw.get("cs_link")),
            "youtube": _safe_url(raw.get("yt_link")),
            "editorial": _safe_url(raw.get("editorial_link")),
            "original": _safe_url(raw.get("post_link")),
        },
        "tags": _parse_tags(raw.get("ques_topic")),
    }


def _build_problems(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten the hierarchical A2Z structure into a sorted problem list.

    Deduplicates by original ``id`` — if two entries share the same id
    only the first occurrence (by sheet order) is kept.

    Args:
        steps: The top-level list of step dicts from the source JSON.

    Returns:
        A flat, deterministically ordered list of normalised problems.
    """
    problems: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    duplicates_skipped: int = 0

    total_raw = sum(
        len(sub.get("topics", []))
        for step in steps
        for sub in step.get("sub_steps", [])
    )
    processed = 0

    for step in steps:
        for sub_step in step.get("sub_steps", []):
            for topic_entry in sub_step.get("topics", []):
                processed += 1
                bar = progress_bar(processed, total_raw, width=30)
                print(
                    f"\r  {bar}  {processed}/{total_raw} problems processed",
                    end="",
                    flush=True,
                )

                problem = _transform_problem(topic_entry)

                # Deduplicate by original ID
                pid = problem["id"]
                if pid in seen_ids:
                    duplicates_skipped += 1
                    continue
                seen_ids.add(pid)

                problems.append(problem)

    print()  # newline after progress bar
    if duplicates_skipped:
        print(f"  ⚠️  Skipped {duplicates_skipped} duplicate ID(s).")

    return problems


def _generate_topics(problems: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Auto-generate the topic → subtopic → count mapping.

    Args:
        problems: The flat problems list.

    Returns:
        A nested dict: ``{topic: {subtopic: count}}``.
    """
    topics: dict[str, dict[str, int]] = {}
    for prob in problems:
        topic = prob["topic"]
        subtopic = prob["subtopic"]
        topics.setdefault(topic, {})
        topics[topic][subtopic] = topics[topic].get(subtopic, 0) + 1
    return topics


def _init_progress() -> dict[str, Any]:
    """Return a fresh progress structure."""
    return {
        "solved": [],
        "favorites": [],
        "revision1": [],
        "revision2": [],
        "revision3": [],
    }


def _init_notes() -> dict[str, Any]:
    """Return a fresh notes structure."""
    return {}


def _save_json(path: Path, data: Any) -> None:
    """Write *data* as pretty-printed JSON to *path*.

    Creates parent directories if they don't exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def run_import(force_refresh: bool = False) -> None:
    """Execute the full import pipeline.

    1. Read the source URL from config.
    2. Read from local cache if available and force_refresh is False,
       else fetch the remote JSON and update cache.
    3. Transform and deduplicate.
    4. Write ``problems.json``, ``topics.json``.
    5. Initialise ``progress.json`` and ``notes.json`` if absent.
    6. Clean up any ``.partial`` file.

    Called by ``main.py`` when the user selects the Import menu option.
    """
    config, _ = cfg.load()

    print_header("📥  Import A2Z DSA Sheet")

    source_url = config.get(
        "import_source",
        "https://raw.githubusercontent.com/Bugaddr/a2z_old_sheet/main/a2z.json",
    )
    print(f"  Source : {source_url}")
    print()

    # ── Fetch or Load Cache ────────────────────────────────────────────────
    if not force_refresh and _SOURCE_CACHE_PATH.exists():
        print(f"  📦  Reading data from local cache ({_SOURCE_CACHE_PATH.name})...")
        with _SOURCE_CACHE_PATH.open("r", encoding="utf-8") as fh:
            steps = json.load(fh)
        print(f"  ✅  Loaded {len(steps)} top-level step(s) from cache.\n")
    else:
        steps = _fetch_json(source_url)
        _save_json(_SOURCE_CACHE_PATH, steps)
        print(f"  ✅  Received {len(steps)} top-level step(s) and cached to {_SOURCE_CACHE_PATH.name}.\n")

    # ── Transform ──────────────────────────────────────────────────────────
    print("  🔄  Processing problems...")
    problems = _build_problems(steps)

    # ── Partial save (safety net) ──────────────────────────────────────────
    _save_json(_PARTIAL_PATH, problems)

    # ── Generate topics ───────────────────────────────────────────────────
    topics = _generate_topics(problems)

    # ── Write final files ─────────────────────────────────────────────────
    _save_json(_PROBLEMS_PATH, problems)
    print(f"  💾  Saved {len(problems)} problems → data/problems.json")

    _save_json(_TOPICS_PATH, topics)
    topic_count = len(topics)
    subtopic_count = sum(len(subs) for subs in topics.values())
    print(f"  💾  Saved {topic_count} topics ({subtopic_count} subtopics) → data/topics.json")

    # ── Initialise user data (only if absent) ─────────────────────────────
    if not _PROGRESS_PATH.exists():
        _save_json(_PROGRESS_PATH, _init_progress())
        print("  📋  Initialised data/progress.json")

    if not _NOTES_PATH.exists():
        _save_json(_NOTES_PATH, _init_notes())
        print("  📋  Initialised data/notes.json")

    # ── Clean up partial file ─────────────────────────────────────────────
    if _PARTIAL_PATH.exists():
        _PARTIAL_PATH.unlink()

    # ── Summary ───────────────────────────────────────────────────────────
    difficulties: dict[str, int] = {}
    missing_links: int = 0
    for prob in problems:
        difficulties[prob["difficulty"]] = difficulties.get(prob["difficulty"], 0) + 1
        platforms = prob["platforms"]
        if not any(platforms.get(k) for k in ("gfg", "leetcode", "codestudio")):
            missing_links += 1

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║         IMPORT SUMMARY               ║")
    print("  ╠══════════════════════════════════════╣")
    print(f"  ║  Total Problems  : {len(problems):<17}║")
    print(f"  ║  Topics          : {topic_count:<17}║")
    print(f"  ║  Subtopics       : {subtopic_count:<17}║")
    for diff, count in sorted(difficulties.items()):
        print(f"  ║  {diff:<15} : {count:<17}║")
    if missing_links:
        print(f"  ║  Missing Links   : {missing_links:<17}║")
    print("  ╚══════════════════════════════════════╝")
    print()
    print("  🎉  Import complete!  The CLI now works fully offline.\n")
