"""
commands/update_readme.py
--------------------------
Implements the "Update README" command.

Scans the DSA repository for all problems and regenerates the top-level
``README.md`` with a polished GitHub landing page, live statistics, and 
a fully-linked, auto-sorted index table.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import utils.config as cfg
from utils.database import find_by_id, load_problems, load_progress, load_topics
from utils.scanner import ProblemEntry, scan_problems
from utils.ui import print_header


# ─────────────────────────────────────────────────────────────────────────────
#  Generators
# ─────────────────────────────────────────────────────────────────────────────

def _generate_header() -> str:
    return (
        "# 📘 Data Structures & Algorithms Practice\n\n"
        "A modern Data Structures & Algorithms repository powered by **DSA Companion CLI**.\n\n"
        "The repository combines:\n\n"
        "- Striver A2Z Sheet\n"
        "- GeeksForGeeks\n"
        "- LeetCode\n"
        "- Local progress tracking\n"
        "- Automated workspace generation\n"
        "- Repository statistics\n"
        "- Search\n"
        "- Notes\n"
        "- Favorites\n"
    )

def _generate_features() -> str:
    return (
        "## ✨ Features\n\n"
        "- 📥 Import the complete Striver A2Z Sheet\n"
        "- 🔍 Search 450+ problems instantly\n"
        "- 📂 Generate problem workspaces\n"
        "- ⭐ Favorite problems\n"
        "- 📝 Personal notes\n"
        "- 📊 Progress tracking\n"
        "- ✅ Database validation\n"
        "- 🔄 Automatic README generation\n"
    )

def _generate_cli_preview() -> str:
    return (
        "## 💻 CLI Preview\n\n"
        "```text\n"
        "  ╔══════════════════════════════════════╗\n"
        "  ║           MAIN MENU                  ║\n"
        "  ╠══════════════════════════════════════╣\n"
        "  ║  1.  📂  Create Problem              ║\n"
        "  ║  2.  📝  Update README               ║\n"
        "  ║  3.  📊  Show Stats                  ║\n"
        "  ║  4.  📥  Import Problems             ║\n"
        "  ║  5.  🔄  Refresh Problem Database    ║\n"
        "  ║  6.  ✅  Validate Database           ║\n"
        "  ║  7.  🔎  Search Problems             ║\n"
        "  ║  8.  🚪  Exit                        ║\n"
        "  ╚══════════════════════════════════════╝\n"
        "```\n"
    )

def _generate_repo_tree(dsa_root: Path) -> str:
    dirs = []
    for p in dsa_root.iterdir():
        if p.is_dir() and p.name not in (".git", "dsa-tool", ".vscode"):
            dirs.append(p.name)
    dirs.sort()
    
    tree = "DSA/\n"
    for d in dirs:
        tree += f"├── {d}/\n"
    tree += "└── dsa-tool/\n"

    return (
        "## 🗂️ Repository Structure\n\n"
        "```text\n"
        f"{tree}"
        "```\n"
    )

def _generate_topic_progress(problems_list: list[dict], solved_ids: set[str]) -> str:
    topic_stats: dict[str, dict[str, int]] = {}
    for p in problems_list:
        t = p["topic"]
        if t not in topic_stats:
            topic_stats[t] = {"total": 0, "solved": 0}
        topic_stats[t]["total"] += 1
        if p["id"] in solved_ids:
            topic_stats[t]["solved"] += 1

    lines = [
        "## 📈 Topic Progress\n",
        "| Topic | Solved | Total | Progress |",
        "|-------|-------:|------:|---------:|"
    ]
    for t in sorted(topic_stats.keys()):
        stats = topic_stats[t]
        prog = (stats["solved"] / stats["total"] * 100) if stats["total"] > 0 else 0
        lines.append(f"| {t} | {stats['solved']} | {stats['total']} | {prog:.1f}% |")

    return "\n".join(lines) + "\n"

def _generate_statistics(problems_list: list[dict], solved_ids: set[str]) -> str:
    total = len(problems_list)
    solved = len(solved_ids)
    remaining = total - solved
    completion = (solved / total * 100) if total > 0 else 0
    
    topics = set(p["topic"] for p in problems_list)
    
    easy_total = sum(1 for p in problems_list if p["difficulty"] == "Easy")
    med_total = sum(1 for p in problems_list if p["difficulty"] == "Medium")
    hard_total = sum(1 for p in problems_list if p["difficulty"] == "Hard")
    
    easy_solved = sum(1 for p in problems_list if p["difficulty"] == "Easy" and p["id"] in solved_ids)
    med_solved = sum(1 for p in problems_list if p["difficulty"] == "Medium" and p["id"] in solved_ids)
    hard_solved = sum(1 for p in problems_list if p["difficulty"] == "Hard" and p["id"] in solved_ids)

    return (
        "## 📊 Statistics\n\n"
        f"- **Total Problems**: {total}\n"
        f"- **Solved**: {solved}\n"
        f"- **Remaining**: {remaining}\n"
        f"- **Completion**: {completion:.1f}%\n"
        f"- **Topics**: {len(topics)}\n"
        f"- **Easy**: {easy_solved} / {easy_total}\n"
        f"- **Medium**: {med_solved} / {med_total}\n"
        f"- **Hard**: {hard_solved} / {hard_total}\n"
    )

def _generate_quick_start() -> str:
    return (
        "## 🚀 Quick Start\n\n"
        "```bash\n"
        "# Clone the repository\n"
        "git clone <your-repo-url>\n"
        "cd DSA\n\n"
        "# Install dependencies\n"
        "cd dsa-tool\n"
        "pip install -r requirements.txt\n\n"
        "# Run the CLI\n"
        "python3 main.py\n"
        "```\n"
    )

def _generate_roadmap() -> str:
    return (
        "## 🗺️ Roadmap\n\n"
        "- [x] Data-driven database\n"
        "- [x] BugAddr importer\n"
        "- [x] Interactive search\n"
        "- [x] Favorites\n"
        "- [x] Notes\n"
        "- [x] Workspace automation\n"
        "- [ ] Revision scheduler\n"
        "- [ ] Daily challenge\n"
        "- [ ] React dashboard\n"
    )

def _generate_recent_activity(solved_ids: list[str]) -> str:
    if not solved_ids:
        return ""
        
    lines = ["## 🕒 Recent Activity\n"]
    recent = solved_ids[-5:] # Last 5 solved
    recent.reverse() # Most recent first
    
    for pid in recent:
        prob = find_by_id(pid)
        if prob:
            lines.append(f"- Solved **{prob['name']}** ({prob['difficulty']})")
    
    if len(lines) > 1:
        return "\n".join(lines) + "\n"
    return ""

def _generate_project_information(dsa_root: Path, problems_list: list[dict]) -> str:
    version_file = dsa_root / "VERSION"
    repo_version = version_file.read_text().strip() if version_file.exists() else "1.0.0"
    cli_version = repo_version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_size = len(problems_list)
    
    topics = set(p["topic"] for p in problems_list)
    subtopics = set(p["subtopic"] for p in problems_list)

    return (
        "## ℹ️ Project Information\n\n"
        f"- **Repository Version**: {repo_version}\n"
        f"- **CLI Version**: {cli_version}\n"
        f"- **Python Version**: {py_version}\n"
        f"- **Problem Database Size**: {db_size} problems\n"
        f"- **Topics**: {len(topics)} topics, {len(subtopics)} subtopics\n"
        f"- **Last Updated**: {timestamp}\n"
    )

def _generate_problem_index(problems_dict: dict[str, list[ProblemEntry]]) -> str:
    lines: list[str] = [
        "## 📋 Problem Index\n",
    ]

    if not problems_dict:
        lines.append("_No problems scaffolded yet. Use the CLI to start solving!_\n")
        return "\n".join(lines)

    for topic in sorted(problems_dict):
        anchor = topic.lower().replace(" ", "-")
        lines.append(f"- [{topic}](#{anchor}) ({len(problems_dict[topic])})")

    lines += ["", "---", ""]

    for topic in sorted(problems_dict):
        lines += [
            f"### {topic}\n",
            "| # | Problem | Platform | Difficulty | Link |",
            "|---|---------|----------|------------|------|",
        ]
        for entry in problems_dict[topic]:
            link_cell = f"[Link]({entry.link})" if entry.link != "—" else "—"
            problem_cell = f"[{entry.name}](./{entry.rel_path}/README.md)"
            lines.append(
                f"| {entry.number} | {problem_cell} "
                f"| {entry.platform} | {entry.difficulty} | {link_cell} |"
            )
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_readme_content(
    dsa_root: Path,
    scaffolded_problems: dict[str, list[ProblemEntry]],
    db_problems: list[dict],
    solved_ids: list[str]
) -> str:
    """Compose the generated Markdown content for the top-level ``README.md``."""
    solved_set = set(solved_ids)
    
    sections = [
        _generate_header(),
        _generate_features(),
        _generate_cli_preview(),
        _generate_repo_tree(dsa_root),
        _generate_topic_progress(db_problems, solved_set),
        _generate_statistics(db_problems, solved_set),
        _generate_quick_start(),
        _generate_roadmap(),
        _generate_recent_activity(solved_ids),
        _generate_project_information(dsa_root, db_problems),
        _generate_problem_index(scaffolded_problems)
    ]
    
    # Filter out empty sections and join with double newlines
    valid_sections = [s for s in sections if s.strip()]
    return "\n".join(valid_sections)


def _write_readme(dsa_root: Path, content: str) -> None:
    """Write *content* to ``<dsa_root>/README.md``, backing up the old file."""
    readme_dest = dsa_root / "README.md"

    if readme_dest.exists():
        backup = dsa_root / "README.md.bak"
        backup.write_text(readme_dest.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"  💾  Previous README backed up → {backup.name}")

    readme_dest.write_text(content, encoding="utf-8")
    print(f"  🎉  README.md updated:\n     {readme_dest}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def run() -> None:
    """Scan the DSA repo and regenerate the top-level ``README.md`` landing page."""
    _, dsa_root = cfg.load()

    print_header("📝  Update Top-Level README")
    print("  🔍  Scanning repository for problems...")

    scaffolded_problems = scan_problems(dsa_root)
    total_scaffolded = sum(len(v) for v in scaffolded_problems.values())

    print(f"  ✅  Found {total_scaffolded} scaffolded problem(s) across {len(scaffolded_problems)} topic(s).")
    print("  🔍  Loading local database statistics...")
    
    db_problems = load_problems()
    progress = load_progress()
    solved_ids = progress.get("solved", [])

    print("  ✏️  Generating polished README content...")

    content = _build_readme_content(dsa_root, scaffolded_problems, db_problems, solved_ids)
    _write_readme(dsa_root, content)
