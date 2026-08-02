"""
commands/create_problem.py
--------------------------
Implements the "Create Problem" command.

Workflow
--------
1. Load configuration via :mod:`utils.config`.
2. Collect problem metadata interactively from the user.
3. Derive the target folder path inside the DSA repository.
4. Render ``README.md`` and ``solution.cpp`` from templates.
5. Write the files, reporting the outcome for each.
"""

from __future__ import annotations

import utils.config as cfg
from utils.file_utils import (
    build_folder_name,
    build_placeholders,
    ensure_dir,
    render_template,
    write_file,
)
from utils.ui import print_header, prompt_choice, prompt_text


# ─────────────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────────────

_TEMPLATES_DIR: Path = cfg.BASE_DIR / "templates"

# Default placeholder text that the user fills in manually after creation.
_DEFAULT_APPROACH = "Write your approach here."
_DEFAULT_ALGORITHM = "Describe the algorithm step-by-step."
_DEFAULT_COMPLEXITY = "O(?)"


def _validate_url(url: str) -> bool:
    """Check that *url* looks like a valid HTTP(S) link.

    This is a lightweight sanity check, not a full RFC-3986 parser.

    Args:
        url: The URL string entered by the user.

    Returns:
        ``True`` if the URL starts with ``http://`` or ``https://``,
        ``False`` otherwise.
    """
    return url.startswith(("http://", "https://"))


# ─────────────────────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def run() -> None:
    """Interactively scaffold a new problem folder inside the DSA repository.

    Called by ``main.py`` when the user selects option 1 from the menu.
    Handles the complete workflow: input → directory creation → file
    generation.  An overwrite guard prevents accidental data loss when the
    problem folder already exists.
    """
    config, dsa_root = cfg.load()

    print_header("📂  Create New Problem")

    # ── Collect inputs ────────────────────────────────────────────────────────
    topic = prompt_choice("Select Topic:", config["topics"])
    problem_number = prompt_text("Problem Number (e.g. 1, 2, 42)")
    problem_name = prompt_text("Problem Name (e.g. Largest Element)")
    platform = prompt_choice("Select Platform:", config["platforms"])
    difficulty = prompt_choice("Select Difficulty:", config["difficulties"])

    problem_link = prompt_text("Problem Link (URL)")
    if not _validate_url(problem_link):
        print(
            "  ⚠️  The URL doesn't look valid (expected http:// or https://).\n"
            "     Continuing anyway — you can update it in README.md later."
        )

    # ── Resolve target directory ──────────────────────────────────────────────
    folder_name = build_folder_name(problem_number, problem_name)
    problem_dir = dsa_root / topic / folder_name

    # ── Overwrite guard ───────────────────────────────────────────────────────
    overwrite = False
    if problem_dir.is_dir():
        print(f"\n  ⚠️  This folder already exists:\n     {problem_dir}")
        answer = input("  Overwrite existing files? [y/N]: ").strip().lower()
        if answer != "y":
            print("  ↩️  Aborted — no files were changed.\n")
            return
        overwrite = True

    # ── Create directory ──────────────────────────────────────────────────────
    ensure_dir(problem_dir)
    print(f"\n  ✅  Directory ready: {problem_dir}")

    # ── Render and write files ────────────────────────────────────────────────
    placeholders = build_placeholders(
        problem_name, platform, difficulty, problem_link, topic
    )

    _files = [
        ("README.md", "📄  README.md"),
        ("solution.cpp", "💻  solution.cpp"),
    ]

    for template_name, label in _files:
        content = render_template(_TEMPLATES_DIR / template_name, placeholders)
        dest = problem_dir / template_name
        if write_file(dest, content, overwrite=overwrite):
            print(f"  {label} created.")
        else:
            print(f"  ⏭️  {template_name} already exists — skipped.")

    print(f"\n  🎉  Problem scaffold ready at:\n     {problem_dir}\n")
