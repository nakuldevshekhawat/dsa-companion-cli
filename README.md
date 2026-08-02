# 🛠️ DSA Companion CLI

> A standalone Python CLI application to manage your DSA practice repository — scaffold problems, auto-index them, and track your progress from the terminal.

---

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Commands](#-commands)
- [Project Structure](#-project-structure)
- [Data Sources](#-data-sources)
- [Configuration](#-configuration)
- [Screenshots](#-screenshots)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

- **Interactive Problem Scaffolding**: Quickly create problem folders with boilerplate code and READMEs.
- **Automated Indexing**: Scan your repository and auto-generate a comprehensive top-level README with a problem index.
- **Progress Tracking**: View detailed statistics and progress bars for your solved problems, categorized by topic and difficulty.
- **Problem Database Integration**: Import problem sets (e.g., Striver A2Z) and keep them synchronized.
- **Fuzzy Search**: Quickly search your problem database from the terminal.
- **Data Validation**: Ensure your local database is free of missing data or duplicate IDs.

---

## 📦 Installation

Ensure you have Python 3 installed on your system.

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/<username>/dsa-companion-cli.git
cd dsa-companion-cli
pip install -r requirements.txt
```

---

## 🚀 Quick Start

To launch the interactive CLI, simply run:

```bash
python3 main.py
```

On **first run**, `config.json` is automatically created by copying
`config.example.json`. No manual setup required.

You will see the interactive menu:

```
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
```

Use `Ctrl+C` inside any command to cancel and return to the menu.

---

## 🔧 Commands

### 1. Create Problem

Interactively scaffolds a new problem folder inside your repository.

**Prompts:**

| Field | Description |
|-------|-------------|
| Topic | Choose from the configured topic list |
| Problem Number | Integer (zero-padded automatically, e.g. `1` → `01`) |
| Problem Name | Human-readable name (e.g. `Largest Element`) |
| Platform | LeetCode, Codeforces, GeeksForGeeks, etc. |
| Difficulty | Easy, Medium, or Hard |
| Problem Link | URL to the problem |

**Result:**

```
dsa-companion-cli/
└── Arrays/
    └── 01_Largest_Element/
        ├── README.md       ← pre-filled with your metadata
        └── solution.cpp    ← C++ boilerplate with problem header
```

### 2. Update README

Scans the repository for all problem folders (detected by the
presence of `solution.cpp`) and regenerates the top-level `README.md`
with a structured, alphabetically sorted problem index.

- Creates a Table of Contents with per-topic links and counts.
- Each topic section has a Markdown table with problem number, name, platform, difficulty, and link.
- Problems are sorted by **integer** problem number (not lexicographic).
- The previous `README.md` is backed up as `README.md.bak` before overwriting.

### 3. Show Stats

Displays a terminal dashboard with Unicode progress bars showing overall progress, and progress by difficulty and topic.

### 4. Import Problems

One-time import of problem lists (like the Striver A2Z sheet).
Downloads the data, parses it, extracts metadata and tags, and builds the database at `data/problems.json`.

### 5. Refresh Problem Database

Force re-downloads the upstream source, updates the local cache, and rebuilds the `problems.json` database.

### 6. Validate Database

Runs the validation suite on `data/problems.json` to check for missing topics, duplicate IDs, missing difficulty levels, and broken URLs.

### 7. Search Problems

Fuzzy search through the imported problems database to quickly find problem metadata, difficulty, and topics.

---

## 📁 Project Structure

```
dsa-companion-cli/
├── commands/                # CLI command modules (create, update, stats, etc.)
├── data/                    # JSON databases and raw problem data
├── importers/               # Data importers for external problem sheets
├── templates/               # Boilerplate templates (README, solution.cpp)
├── utils/                   # Shared utilities (config, file, UI, scanner helpers)
├── main.py                  # CLI entry point & menu dispatcher
├── README.md                # Project documentation
├── VERSION                  # Current version identifier
├── requirements.txt         # Python dependencies
├── config.example.json      # Portable configuration defaults (committed)
└── .gitignore               # Git ignore rules
```

---

## 🗄️ Data Sources

The database architecture is stored in `data/`. It strictly separates static application data from your personal progress.

| File | Purpose | Git-committed? |
|------|---------|----------------|
| `problems.json` | The canonical shared dataset containing all problem metadata (ID, name, difficulty, platforms, tags). | ✅ Yes |
| `topics.json` | Derived hierarchy of topics → subtopics → problem counts. | ✅ Yes |
| `progress.json` | Your personal state (solved, favorites, revision lists). | ❌ No |
| `notes.json` | Your personal notes on specific problems. | ❌ No |
| `source_a2z.json` | A raw upstream cache of the downloaded dataset. Kept for debugging and cache hits. | ❌ No |

> **Why is `source_a2z.json` not committed?**
> It is an upstream cache that can easily be reconstructed by running `Refresh Problem Database`. We commit the normalized `problems.json` instead so everyone gets the curated data instantly.

---

## ⚙️ Configuration

### `config.example.json` vs `config.json`

| File | Purpose | Git-committed? |
|------|---------|----------------|
| `config.example.json` | Portable defaults — safe to share | ✅ Yes |
| `config.json` | Your local overrides — machine-specific | ❌ No (git-ignored) |

### How it works

1. **First run** → `config.json` does not exist → tool copies `config.example.json` → `config.json`.
2. **Subsequent runs** → `config.json` loaded directly.
3. The repository root is resolved dynamically — no absolute paths stored.

### Customisable fields

```json
{
    "default_author": "Your Name",
    "default_language": "C++",
    "default_platform": "LeetCode",
    "platforms": ["LeetCode", "Codeforces", "GeeksForGeeks", "HackerRank", "AtCoder", "Other"],
    "difficulties": ["Easy", "Medium", "Hard"],
    "topics": ["Arrays", "Trees", "Graphs", "..."]
}
```

> **Why is `config.json` git-ignored?**
> It may contain personal preferences that differ per machine. Keeping it
> out of Git prevents merge conflicts when collaborating.

---

## 🖼️ Screenshots

> **Note:** Add screenshots of the CLI interface, statistics dashboard, and created folder structures here.

*(Placeholder for screenshots)*

---

## 🗺️ Roadmap

- [ ] Support for multiple programming languages in templates.
- [ ] Integration with LeetCode API to fetch problems.
- [ ] Export progress to a web-based dashboard.
- [ ] Add more platform importers.

---

## 🤝 Contributing

1. Fork the repository.
2. Clone your fork: `git clone https://github.com/<username>/dsa-companion-cli.git`
3. Run `python3 main.py` once to generate `config.json`.
4. Create a new branch for your feature.
5. Make your changes and open a PR.

> Never commit `config.json` — it is git-ignored for good reason.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
