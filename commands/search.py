"""
commands/search.py
------------------
Interactive search and problem details CLI.

Allows the user to search the imported problem database using fuzzy
matching, select a problem from the results, and interact with it:
- View details (topic, difficulty, platforms, status, notes)
- Mark Solved / Unsolved
- Add / Remove Favorite
- View / Edit / Delete Notes
- Open links in the default web browser
"""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path
from typing import Any

import commands.update_readme as update_readme
import utils.config as cfg
from utils.database import (
    delete_note,
    find_by_id,
    get_note,
    load_problems,
    load_progress,
    mark_favorite,
    mark_solved,
    mark_unsolved,
    remove_favorite,
    search,
    update_note,
)
from utils.file_utils import (
    build_folder_name,
    build_placeholders,
    ensure_dir,
    render_template,
    write_file,
)
from utils.ui import print_header, print_section, prompt_choice


# ─────────────────────────────────────────────────────────────────────────────
#  UI formatting helpers
# ─────────────────────────────────────────────────────────────────────────────

def _format_status(problem_id: str, solved_ids: set[str], fav_ids: set[str]) -> str:
    """Format the solved/favorite status as emojis."""
    status = "✅" if problem_id in solved_ids else "❌"
    if problem_id in fav_ids:
        status += " ⭐"
    return status


def _print_problem_row(idx: int, prob: dict[str, Any], solved_ids: set[str], fav_ids: set[str]) -> None:
    """Print a single row in the search results table."""
    name = prob["name"][:35]
    diff = prob["difficulty"]
    topic = prob["topic"][:20]
    status = _format_status(prob["id"], solved_ids, fav_ids)
    
    platforms = [k.title() for k, v in prob.get("platforms", {}).items() if v]
    plat_str = ",".join(platforms)[:15]

    # Simple color coding for difficulty
    if diff == "Easy":
        diff_str = f"\033[92m{diff:<8}\033[0m"
    elif diff == "Medium":
        diff_str = f"\033[93m{diff:<8}\033[0m"
    elif diff == "Hard":
        diff_str = f"\033[91m{diff:<8}\033[0m"
    else:
        diff_str = f"{diff:<8}"

    print(f"  {idx:<3} {name:<35} {diff_str} {topic:<20} {plat_str:<15} {status}")


# ─────────────────────────────────────────────────────────────────────────────
#  Interactive commands
# ─────────────────────────────────────────────────────────────────────────────

def _create_workspace(prob: dict[str, Any]) -> None:
    """Implement the complete 'Start Solving' workspace scaffolding workflow."""
    config, dsa_root = cfg.load()
    
    # 1. Determine folder
    topic = prob.get("topic", "Unknown")
    problem_number = prob.get("problemNumber", "0") # Some problems might not have number parsed, fallback to 0
    name = prob.get("name", "Unknown")
    
    folder_name = build_folder_name(problem_number, name)
    problem_dir = dsa_root / topic / folder_name

    # Check if exists
    overwrite = False
    if problem_dir.is_dir():
        print(f"\n  ⚠️  This folder already exists:\n     {problem_dir}")
        choice = prompt_choice("Choose Action:", ["Open Existing", "Overwrite", "Cancel"])
        if choice == "Cancel":
            return
        elif choice == "Overwrite":
            overwrite = True

    ensure_dir(problem_dir)
    print(f"\n  ✅  Directory ready: {problem_dir}")

    # Render templates
    # Pick a valid primary link from the available ones
    platforms = prob.get("platforms", {})
    primary_link = ""
    primary_plat = ""
    for p in ["Leetcode", "Gfg", "Codestudio"]:
        if platforms.get(p.lower()):
            primary_link = platforms.get(p.lower())
            primary_plat = p
            break
            
    if not primary_link and platforms:
        # Fallback to the first available link if standard ones are missing
        for k, v in platforms.items():
            if v and k != "youtube":
                primary_link = v
                primary_plat = k.title()
                break

    difficulty = prob.get("difficulty", "Unknown")
    
    placeholders = build_placeholders(
        name, primary_plat, difficulty, primary_link, topic
    )

    _files = [
        ("README.md", "📄  README.md"),
        ("solution.cpp", "💻  solution.cpp"),
    ]

    templates_dir = cfg.BASE_DIR / "templates"
    for template_name, label in _files:
        content = render_template(templates_dir / template_name, placeholders)
        dest = problem_dir / template_name
        if write_file(dest, content, overwrite=overwrite):
            print(f"  {label} created.")
        else:
            print(f"  ⏭️  {template_name} already exists — skipped.")

    # Update README index with the newly scaffolded folder
    print("\n  🔄  Updating repository README index...")
    update_readme.run()
    
    # Ask about VS Code
    open_ide = input(f"\n  ➤  Open files in VS Code? [y/N]: ").strip().lower()
    if open_ide == "y":
        readme_path = problem_dir / "README.md"
        sol_path = problem_dir / "solution.cpp"
        # Open the folder to load the workspace, and the two files directly
        subprocess.run(["code", str(problem_dir), str(readme_path), str(sol_path)], check=False)

    # Post creation menu
    while True:
        print(f"\n  🎉  Problem scaffold ready at:\n     {problem_dir}\n")
        post_opts = []
        if platforms.get("gfg"): post_opts.append("Open GFG")
        if platforms.get("leetcode"): post_opts.append("Open LeetCode")
        post_opts.extend(["Open Folder", "Start Coding"])
        
        post_choice = prompt_choice("Next steps:", post_opts)
        
        if post_choice == "Open GFG":
            webbrowser.open(platforms["gfg"])
        elif post_choice == "Open LeetCode":
            webbrowser.open(platforms["leetcode"])
        elif post_choice == "Open Folder":
            # Using standard 'open' on macOS to reveal folder
            subprocess.run(["open", str(problem_dir)], check=False)
        elif post_choice == "Start Coding":
            break


def _edit_notes(problem_id: str) -> None:
    """Prompt the user to add or edit a note for the problem."""
    print("\n  ✏️  Enter your note (leave empty to cancel):")
    note_text = input("  ➤  ").strip()
    if note_text:
        update_note(problem_id, note_text)
        print("  ✅  Note saved!")


def _open_link(platforms: dict[str, str]) -> None:
    """Prompt the user to select a platform and open its link in the browser."""
    available = {k: v for k, v in platforms.items() if v}
    if not available:
        print("\n  ❌  No links available for this problem.")
        return

    choices = list(available.keys())
    choice = prompt_choice("Select platform to open:", choices)
    url = available[choice]
    print(f"  🌐  Opening {choice} link in browser...")
    webbrowser.open(url)


def _view_problem_details(problem_id: str) -> None:
    """Display problem details and provide an interactive action menu."""
    while True:
        # Re-fetch state each loop to reflect changes
        prob = find_by_id(problem_id)
        if not prob:
            print("\n  ❌  Problem not found.")
            return

        progress = load_progress()
        solved = problem_id in progress.get("solved", [])
        favorite = problem_id in progress.get("favorites", [])
        
        rev_level = "None"
        if problem_id in progress.get("revision1", []): rev_level = "1"
        elif problem_id in progress.get("revision2", []): rev_level = "2"
        elif problem_id in progress.get("revision3", []): rev_level = "3"

        note_data = get_note(problem_id)

        print_header(f"📖  Problem: {prob['name']}")
        
        print_section("📌  Details")
        print(f"  Topic      : {prob.get('topic')}")
        print(f"  Subtopic   : {prob.get('subtopic')}")
        print(f"  Difficulty : {prob.get('difficulty')}")
        print(f"  Tags       : {', '.join(prob.get('tags', [])) or 'None'}")
        
        print_section("📈  Status")
        print(f"  Solved     : {'✅ Yes' if solved else '❌ No'}")
        print(f"  Favorite   : {'⭐ Yes' if favorite else '❌ No'}")
        print(f"  Revision   : {rev_level}")
        
        print_section("🔗  Links")
        platforms = prob.get("platforms", {})
        has_links = False
        for plat, url in platforms.items():
            if url:
                has_links = True
                print(f"  • {plat.title():<10} : {url}")
        if not has_links:
            print("  No links available.")

        print_section("📝  Notes")
        if note_data:
            print(f"  [Updated: {note_data['updated']}]")
            print(f"  {note_data['note']}")
        else:
            print("  No notes added yet.")
            
        print(f"\n  {'═' * 48}\n")

        # Action Menu
        actions = [
            "Start Solving",
            "Mark Solved" if not solved else "Mark Unsolved",
            "Add Favorite" if not favorite else "Remove Favorite",
            "Edit Notes",
            "Delete Notes" if note_data else None,
            "Open Link in Browser" if has_links else None,
            "Back to Search Results"
        ]
        # Filter out None values
        valid_actions = [a for a in actions if a is not None]

        choice = prompt_choice("Actions:", valid_actions)

        if choice == "Start Solving":
            _create_workspace(prob)
        elif choice == "Mark Solved":
            mark_solved(problem_id)
            print("  ✅  Marked as solved!")
        elif choice == "Mark Unsolved":
            mark_unsolved(problem_id)
            print("  ❌  Marked as unsolved.")
        elif choice == "Add Favorite":
            mark_favorite(problem_id)
            print("  ⭐  Added to favorites!")
        elif choice == "Remove Favorite":
            remove_favorite(problem_id)
            print("  ❌  Removed from favorites.")
        elif choice == "Edit Notes":
            _edit_notes(problem_id)
        elif choice == "Delete Notes":
            delete_note(problem_id)
            print("  🗑️   Note deleted.")
        elif choice == "Open Link in Browser":
            _open_link(platforms)
        elif choice == "Back to Search Results":
            break


# ─────────────────────────────────────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def run() -> None:
    """Interactive fuzzy search through the problem database."""
    print_header("🔎  Search Problems")

    problems = load_problems()
    if not problems:
        print("  ℹ️  No problems imported yet.")
        print("     Run the importer first (Menu → Import Problems).\n")
        return

    # Basic UI allows filtering by term. The backend `search` supports more,
    # but the prompt asks for basic filters for now via simple query.
    query = input("  Enter search query (leave empty to list all): ").strip()

    results = search(query)
    if not results:
        print(f"\n  No results found for '{query}'.\n")
        return

    progress = load_progress()
    solved_ids = set(progress.get("solved", []))
    fav_ids = set(progress.get("favorites", []))

    while True:
        print(f"\n  Found {len(results)} result(s). Showing top 20:\n")
        print(f"  {'#':<3} {'Name':<35} {'Diff':<8} {'Topic':<20} {'Platforms':<15} {'Status'}")
        print(f"  {'─'*3} {'─'*35} {'─'*8} {'─'*20} {'─'*15} {'─'*8}")

        top_results = results[:20]
        for idx, prob in enumerate(top_results, start=1):
            _print_problem_row(idx, prob, solved_ids, fav_ids)

        if len(results) > 20:
            print(f"\n  … and {len(results) - 20} more result(s).")

        print("\n  Enter the number of a problem to view details.")
        print("  Enter 'q' to quit search and return to main menu.")
        
        choice = input("\n  ➤  ").strip()
        
        if choice.lower() == 'q':
            break
            
        if not choice.isdigit():
            print("  ⚠️  Invalid input. Please enter a number or 'q'.")
            continue
            
        idx = int(choice)
        if 1 <= idx <= len(top_results):
            prob = top_results[idx - 1]
            _view_problem_details(prob["id"])
            # Reload progress after returning from details view
            progress = load_progress()
            solved_ids = set(progress.get("solved", []))
            fav_ids = set(progress.get("favorites", []))
        else:
            print(f"  ⚠️  Please enter a number between 1 and {len(top_results)}.")
