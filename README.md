<div align="center">

# 🛠️ DSA Companion CLI

> A polished, standalone Python CLI application designed to power up your Data Structures and Algorithms practice. Generate workspaces, track progress, and manage your problems directly from the terminal.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-success.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Active_Development-orange.svg)]()
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-lightgrey.svg)]()

</div>

---

## 📋 Table of Contents

- [Introduction](#-introduction)
- [Why DSA Companion CLI?](#-why-dsa-companion-cli)
- [Features](#-features)

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Introduction

**DSA Companion CLI** is a standalone Python CLI for managing Data Structures and Algorithms practice repositories. It automates file creation, maintains your repository index, and tracks your progress locally.

**Core Capabilities:**
- **Import Problem Sets**: Seamlessly import structured problem sheets (e.g., Striver A2Z) straight into a local database.
- **Generate Workspaces**: Automatically scaffold structured folders with C++ templates, problem metadata, and localized READMEs.
- **Search Problems**: Fuzzy-find any problem by name, ID, or topic across your database.
- **Track Progress**: Visually track your completion rates across different topics and difficulties.
- **Manage Notes & Favorites**: Keep personal notes and star your favorite problems for later revision.
- **Automated README Generation**: Rebuild an aesthetically pleasing, organized top-level README for your GitHub repository in milliseconds.
- **Rich Statistics**: View beautifully rendered terminal dashboards with progress bars and completion metrics.

## 💡 Why DSA Companion CLI?

We built this tool to keep you focused on problem-solving, not repository management. It solves common pain points by:
- Eliminating manual folder and file creation
- Automating top-level README maintenance
- Providing a searchable, offline local database
- Tracking your progress visually from the terminal
- Generating ready-to-code workspaces instantly

---

## ✨ Features

| Feature | Description |
|:---:|---|
| **🔍 Search** | Lightning-fast fuzzy search across the entire problem database. |
| **📂 Workspace** | Scaffold solution folders instantly with ready-to-code templates. |
| **⭐ Favorites** | Mark important problems and group them for easy revision. |
| **📝 Notes** | Attach personal Markdown notes to any problem natively. |
| **📊 Statistics** | Track your real-time progress with terminal-based visual dashboards. |
| **📥 Import** | Instantly download and parse comprehensive problem sheets like Striver A2Z. |
| **✅ Validation** | Built-in data validation to ensure database integrity and catch missing attributes. |
| **🤖 Automation** | Auto-generate your repository's Table of Contents and index files. |

---



## 📦 Installation

Ensure you have Python 3.8+ installed on your system.

Clone the repository and install dependencies:

```bash
git clone https://github.com/<your-username>/dsa-companion-cli.git
cd dsa-companion-cli
python3 -m pip install -r requirements.txt
```

---

## ⚡ Quick Start

Launch the interactive CLI by running:

```bash
python3 main.py
```

On your **first run**, the application will automatically create a local `config.json` file from the default `config.example.json`. No manual configuration is required!

Use the on-screen prompts to navigate the menu. Press `Ctrl+C` at any time to return to the main menu.

---

## 🏗️ Architecture

The CLI is modular, separating command logic from database operations and UI rendering.

```text
User
 │
 ▼
CLI Entrypoint (main.py)
 │
 ├── Commands/           (Action handlers: search, update_readme, stats)
 ├── Database/           (Local JSON data store: problems, topics, progress)
 ├── Importers/          (External data ingestion and parsing)
 ├── Templates/          (Boilerplate code and README templates)
 └── Utils/              (Shared UI components, scanners, and configs)
```

---


## 🗺️ Roadmap

We are actively developing new features to make DSA practice even smoother:

- [ ] **Data Export**: Ability to export progress and notes to CSV or standalone Markdown summaries.
- [ ] **GitHub Statistics Badges**: Auto-generated SVG badges for your profile README to show off your progress.
- [ ] **Custom Formatting**: Configurable templates for how the top-level README index is generated.

---

## 🤝 Contributing

We welcome contributions from the community! To get started:

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally: `git clone https://github.com/<your-username>/dsa-companion-cli.git`
3. **Run** the setup: `python3 -m pip install -r requirements.txt && python3 main.py`
4. **Create a branch** for your feature: `git checkout -b feature/amazing-feature`
5. **Commit** your changes: `git commit -m "feat: add amazing feature"`
6. **Open a Pull Request** against our `main` branch.

Please read our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) for more details.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
