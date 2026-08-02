"""
utils/file_utils.py
-------------------
Low-level filesystem helpers for the DSA Companion CLI.

This module is intentionally narrow in scope:

* Directory creation   — :func:`ensure_dir`
* Template rendering   — :func:`render_template`
* File writing         — :func:`write_file`
* Timestamp generation — :func:`get_timestamp`

Problem *scanning* and *stats aggregation* are handled by
:mod:`utils.scanner` so that the two concerns stay separate.
All path manipulation uses :mod:`pathlib` exclusively.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
#  Directory helpers
# ─────────────────────────────────────────────────────────────────────────────

def ensure_dir(path: Path) -> Path:
    """Create *path* and any missing parents if it does not already exist.

    This is a thin, expressive wrapper around
    ``Path.mkdir(parents=True, exist_ok=True)`` that returns the path so
    callers can chain it::

        problem_dir = ensure_dir(dsa_root / topic / folder_name)

    Args:
        path: The directory path to create.

    Returns:
        The same ``path``, guaranteed to exist as a directory.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_folder_name(problem_number: str | int, problem_name: str) -> str:
    """Construct a filesystem-safe, zero-padded folder name.

    Format: ``<NN>_<Problem_Name_With_Underscores>``

    The problem number is zero-padded to at least two digits.  If the
    supplied *problem_number* is not a valid integer, it is used verbatim
    and the user is warned.

    Args:
        problem_number: Raw number string or int.
        problem_name:   Raw problem name.

    Returns:
        A sanitised folder name string.

    Examples::

        build_folder_name(1, "Largest Element")  # → "01_Largest_Element"
        build_folder_name(42, "Two Sum")         # → "42_Two_Sum"
    """
    try:
        padded = str(int(problem_number)).zfill(2)
    except (ValueError, TypeError):
        print(
            f"  ⚠️  '{problem_number}' is not a valid integer — "
            "using it verbatim as the folder prefix."
        )
        padded = str(problem_number).strip()

    # Normalise name: replace hyphens/spaces with underscores
    safe_name = "_".join(problem_name.replace("-", " ").split())
    # Remove any special characters that might be problematic in folder names
    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
    return f"{padded}_{safe_name}"


# ─────────────────────────────────────────────────────────────────────────────
#  Template helpers
# ─────────────────────────────────────────────────────────────────────────────

def render_template(template_path: Path, placeholders: dict[str, str]) -> str:
    """Read a template file and substitute ``{{KEY}}`` placeholders.

    Each key in *placeholders* must appear in the template as ``{{KEY}}``.
    Keys that are not present in the template are silently ignored.
    Unmatched ``{{...}}`` tokens in the template are left as-is.

    Args:
        template_path: Path to the source template file.
        placeholders:  Mapping of placeholder names → replacement values.

    Returns:
        The rendered content string with all substitutions applied.

    Raises:
        FileNotFoundError: If *template_path* does not exist.

    Example::

        content = render_template(
            Path("templates/README.md"),
            {"PROBLEM_NAME": "Two Sum", "DIFFICULTY": "Easy"},
        )
    """
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}\n"
            "Ensure the 'templates/' directory is intact inside dsa-tool/."
        )

    content = template_path.read_text(encoding="utf-8")
    for key, value in placeholders.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))
    return content


def build_placeholders(
    problem_name: str,
    platform: str,
    difficulty: str,
    problem_link: str,
    topic: str,
) -> dict[str, str]:
    """Assemble the template placeholder dictionary.

    Args:
        problem_name:  Human-readable problem name.
        platform:      Selected platform string.
        difficulty:    Selected difficulty string.
        problem_link:  Problem URL.
        topic:         Selected topic string.

    Returns:
        A dict mapping template placeholder keys to their values.
    """
    return {
        "PROBLEM_NAME": problem_name,
        "PLATFORM": platform,
        "DIFFICULTY": difficulty,
        "PROBLEM_LINK": problem_link,
        "TOPIC": topic,
        "DATE": date.today().strftime("%Y-%m-%d"),
        "APPROACH": "Write your approach here.",
        "ALGORITHM": "Describe the algorithm step-by-step.",
        "TIME_COMPLEXITY": "O(?)",
        "SPACE_COMPLEXITY": "O(?)",
    }


def write_file(file_path: Path, content: str, *, overwrite: bool = False) -> bool:
    """Write *content* to *file_path*, optionally skipping existing files.

    Parent directories are created automatically if they do not exist.

    Args:
        file_path:  Destination file path.
        content:    Text content to write (UTF-8).
        overwrite:  When ``False`` (default) the file is skipped if it
                    already exists.  When ``True`` the file is replaced.

    Returns:
        ``True`` if the file was written, ``False`` if it was skipped
        because it already existed and *overwrite* is ``False``.
    """
    if file_path.exists() and not overwrite:
        return False
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  Miscellaneous
# ─────────────────────────────────────────────────────────────────────────────

def get_timestamp() -> str:
    """Return the current local date-time as a human-readable string.

    Returns:
        A string formatted as ``YYYY-MM-DD HH:MM:SS``.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
