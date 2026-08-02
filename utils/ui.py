"""
utils/ui.py
-----------
Shared terminal UI helpers for the DSA Companion CLI.

All interactive prompts and display primitives live here so that every
command module can use them without duplicating code.

Public API
----------
- print_header(title)              Display a boxed section title.
- prompt_choice(prompt, choices)   Numbered menu → returns chosen value.
- prompt_text(prompt, required)    Text input with optional empty-check.
- progress_bar(count, total, width) Unicode block progress bar string.
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
#  Display helpers
# ─────────────────────────────────────────────────────────────────────────────

_SEPARATOR_WIDTH = 50


def print_header(title: str) -> None:
    """Print a visually distinct section header with a title.

    Example output::

        ══════════════════════════════════════════════════
          📂  Create New Problem
        ══════════════════════════════════════════════════

    Args:
        title: The section title to display (emoji + text).
    """
    border = "═" * _SEPARATOR_WIDTH
    print(f"\n{border}")
    print(f"  {title}")
    print(border)


def print_section(title: str) -> None:
    """Print a lighter sub-section divider inside a command's output.

    Example output::

        ──────────────────────────────────────────────
          🎯  By Difficulty
        ──────────────────────────────────────────────

    Args:
        title: The sub-section title.
    """
    divider = "─" * (_SEPARATOR_WIDTH - 2)
    print(f"\n  {divider}")
    print(f"  {title}")
    print(f"  {divider}")


def progress_bar(count: int, total: int, width: int = 20) -> str:
    """Render a Unicode block progress bar.

    Args:
        count: The current value.
        total: The maximum value (represents 100 %).
        width: The total bar width in characters (default 20).

    Returns:
        A string such as ``[████████░░░░░░░░░░░░]``.

    Example::

        progress_bar(3, 10, width=10)
        # → '[███░░░░░░░]'
    """
    filled = 0 if total == 0 else round((count / total) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ─────────────────────────────────────────────────────────────────────────────
#  Interactive prompt helpers
# ─────────────────────────────────────────────────────────────────────────────

def prompt_choice(prompt: str, choices: list[str]) -> str:
    """Display a numbered menu and return the user's selected value.

    Keeps asking until the user enters a valid integer in range.

    Args:
        prompt:  The question displayed above the numbered list.
        choices: The list of options to present.

    Returns:
        The string value of the selected option.

    Raises:
        ValueError: If ``choices`` is empty.

    Example::

        platform = prompt_choice("Select Platform:", ["LeetCode", "Codeforces"])
    """
    if not choices:
        raise ValueError("prompt_choice: choices list must not be empty.")

    print(f"\n{prompt}")
    for idx, item in enumerate(choices, start=1):
        print(f"  {idx}. {item}")

    while True:
        raw = input("  Enter number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print(f"  ⚠️  Please enter a number between 1 and {len(choices)}.")


def prompt_text(prompt: str, *, required: bool = True) -> str:
    """Read a text value from stdin with an optional non-empty guard.

    Args:
        prompt:   The prompt string shown before the cursor.
        required: When ``True`` (default), re-prompts if the user submits
                  an empty string.

    Returns:
        The stripped, non-empty string (or empty string if not required).

    Example::

        name = prompt_text("Problem Name (e.g. Two Sum)")
    """
    while True:
        value = input(f"  {prompt}: ").strip()
        if value or not required:
            return value
        print("  ⚠️  This field is required. Please enter a value.")
