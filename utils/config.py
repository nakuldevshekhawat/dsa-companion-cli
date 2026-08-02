"""
utils/config.py
---------------
Centralised configuration loader for the DSA Companion CLI.

Design decisions
----------------
* All internal path constants are module-private (prefixed with ``_``).
* The DSA repository root is resolved **once** at import time and cached
  in ``_dsa_root``.  Repeated calls to :func:`load` or :func:`get_dsa_root`
  are therefore free after the first.
* :func:`load` is the single canonical entry point for command modules.
  It returns a ``(config_dict, dsa_root)`` pair so callers have everything
  they need in one call.

Layout assumption
-----------------
::

    DSA/            ← repository root  (one level above this tool)
    └── dsa-tool/   ← tool root / BASE_DIR
        └── utils/
            └── config.py  (this file)
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
#  Module-private path constants
#  (utils/ → dsa-tool/ → DSA/)
# ─────────────────────────────────────────────────────────────────────────────

_UTILS_DIR: Path = Path(__file__).resolve().parent   # .../dsa-tool/utils/
BASE_DIR: Path = _UTILS_DIR.parent                   # .../dsa-tool/
_CONFIG_PATH: Path = BASE_DIR / "config.json"
_EXAMPLE_PATH: Path = BASE_DIR / "config.example.json"

# Cached DSA root — resolved once, reused on every subsequent call.
_dsa_root: Path | None = None


# ─────────────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_dsa_root() -> Path:
    """Compute and validate the DSA repository root directory.

    The root is the parent of ``BASE_DIR`` (i.e. the directory that
    *contains* ``dsa-tool/``).

    Returns:
        Absolute path to the DSA repository root.

    Raises:
        FileNotFoundError: If the expected parent directory does not exist,
            which would indicate the tool has been moved outside the repo.
    """
    root = BASE_DIR.parent
    if not root.is_dir():
        raise FileNotFoundError(
            f"DSA repository root not found at: {root}\n"
            "Ensure that dsa-tool/ lives directly inside your DSA repository."
        )
    return root


def _bootstrap_config() -> None:
    """Copy ``config.example.json`` → ``config.json`` on first run.

    Prints a one-time informational message so the user understands what
    happened and where to find their local config file.

    Raises:
        FileNotFoundError: If ``config.example.json`` is also missing
            (indicates a corrupt or incomplete installation).
    """
    if not _EXAMPLE_PATH.exists():
        raise FileNotFoundError(
            f"Neither config.json nor config.example.json found in {BASE_DIR}.\n"
            "Please re-clone or restore the dsa-tool project."
        )

    shutil.copy2(_EXAMPLE_PATH, _CONFIG_PATH)
    print(
        "\n  ℹ️  First run detected — config.json has been created from "
        "config.example.json.\n"
        f"     Edit {_CONFIG_PATH} to customise your defaults.\n"
        "     (config.json is git-ignored, so your changes stay local.)\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_dsa_root() -> Path:
    """Return the cached DSA repository root path.

    The root is resolved on the first call and cached for all subsequent
    calls within the same process.

    Returns:
        Absolute :class:`~pathlib.Path` to the DSA repository root.

    Raises:
        FileNotFoundError: See :func:`_resolve_dsa_root`.
    """
    global _dsa_root
    if _dsa_root is None:
        _dsa_root = _resolve_dsa_root()
    return _dsa_root


def load() -> tuple[dict, Path]:
    """Load configuration and return the DSA repository root.

    If ``config.json`` is absent it is automatically bootstrapped from
    ``config.example.json`` before loading.

    Returns:
        A ``(config_dict, dsa_root)`` tuple where:

        * ``config_dict`` — the parsed JSON configuration dictionary.
        * ``dsa_root``    — absolute path to the DSA repository root.

    Raises:
        FileNotFoundError: If ``config.example.json`` is also missing.
        json.JSONDecodeError: If ``config.json`` contains invalid JSON.
    """
    if not _CONFIG_PATH.exists():
        _bootstrap_config()

    with _CONFIG_PATH.open("r", encoding="utf-8") as fh:
        config: dict = json.load(fh)

    return config, get_dsa_root()
