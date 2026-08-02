"""
main.py
-------
Entry point for the DSA Companion CLI.

Run with::

    python main.py

This module is intentionally thin — it owns only the top-level event loop
and menu rendering.  All business logic lives in the ``commands/`` package
and all UI primitives live in ``utils/ui.py``.

Menu
----
1. Create Problem  — scaffold a new problem folder with README + solution.cpp
2. Update README   — regenerate the top-level README.md index
3. Show Stats      — display folder or database statistics
4. Import Problems — import from local cache or fetch if missing
5. Refresh Problem Database — force re-download from Striver A2Z Sheet
6. Validate Database — run validation suite on problems.json
7. Search Problems — fuzzy search through the imported database
8. Exit            — quit the tool
"""

from __future__ import annotations

from typing import Callable

from commands.create_problem import run as create_problem
from commands.search import run as search_problems
from commands.stats import run as show_stats
from commands.update_readme import run as update_readme


# ─────────────────────────────────────────────────────────────────────────────
#  Lazy imports for new commands (avoid import errors if data/ absent)
# ─────────────────────────────────────────────────────────────────────────────

def _import_problems() -> None:
    """Run the BugAddr importer (from cache if available) followed by validation."""
    from importers.bugaddr import run_import
    from importers.validate import validate

    run_import(force_refresh=False)
    validate()


def _refresh_problems() -> None:
    """Force re-download of the BugAddr importer followed by validation."""
    from importers.bugaddr import run_import
    from importers.validate import validate

    run_import(force_refresh=True)
    validate()


def _validate_problems() -> None:
    """Run validation checks on the imported database."""
    from importers.validate import validate
    validate()





# ─────────────────────────────────────────────────────────────────────────────
#  UI constants
# ─────────────────────────────────────────────────────────────────────────────

_BANNER = r"""
  ██████╗ ███████╗ █████╗     ████████╗ ██████╗  ██████╗ ██╗
  ██╔══██╗██╔════╝██╔══██╗       ██╔══╝██╔═══██╗██╔═══██╗██║
  ██║  ██║███████╗███████║       ██║   ██║   ██║██║   ██║██║
  ██║  ██║╚════██║██╔══██║       ██║   ██║   ██║██║   ██║██║
  ██████╔╝███████║██║  ██║       ██║   ╚██████╔╝╚██████╔╝███████╗
  ╚═════╝ ╚══════╝╚═╝  ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
"""

_MENU = """
  ╔══════════════════════════════════════╗
  ║           MAIN MENU                 ║
  ╠══════════════════════════════════════╣
  ║  1.  📂  Create Problem             ║
  ║  2.  📝  Update README              ║
  ║  3.  📊  Show Stats                 ║
  ║  4.  📥  Import Problems            ║
  ║  5.  🔄  Refresh Problem Database   ║
  ║  6.  ✅  Validate Database          ║
  ║  7.  🔎  Search Problems            ║
  ║  8.  🚪  Exit                       ║
  ╚══════════════════════════════════════╝
"""

_EXIT_CHOICE = "8"

# Maps menu choice strings to their command callables.
_ACTIONS: dict[str, Callable[[], None]] = {
    "1": create_problem,
    "2": update_readme,
    "3": show_stats,
    "4": _import_problems,
    "5": _refresh_problems,
    "6": _validate_problems,
    "7": search_problems,
}


# ─────────────────────────────────────────────────────────────────────────────
#  Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _print_banner() -> None:
    """Print the ASCII art banner and tagline on startup."""
    print(_BANNER)
    print("  Your personal DSA problem manager".center(66))
    print()


def _get_choice() -> str:
    """Render the main menu and return the user's raw input string.

    Returns:
        The stripped input string (not yet validated).
    """
    print(_MENU)
    return input(f"  ➤  Enter your choice (1-{_EXIT_CHOICE}): ").strip()


# ─────────────────────────────────────────────────────────────────────────────
#  Main loop
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Run the DSA Companion CLI event loop.

    Displays the menu repeatedly until the user selects Exit.
    Each command is wrapped in a try/except so that an unexpected error
    in one command returns the user to the menu rather than crashing the
    tool.  Ctrl-C inside a command also returns gracefully to the menu.
    """
    _print_banner()

    while True:
        choice = _get_choice()

        if choice in _ACTIONS:
            try:
                _ACTIONS[choice]()
            except KeyboardInterrupt:
                print("\n\n  ↩️  Returning to main menu...\n")
            except Exception as exc:  # noqa: BLE001
                print(f"\n  ❌  An unexpected error occurred: {exc}\n")

        elif choice == _EXIT_CHOICE:
            print("\n  👋  Goodbye! Keep grinding! 💪\n")
            break

        else:
            print(f"\n  ⚠️  Invalid choice — please enter 1-{_EXIT_CHOICE}.\n")


if __name__ == "__main__":
    main()
