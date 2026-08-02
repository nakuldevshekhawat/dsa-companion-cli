# Contributing to DSA Companion CLI

First off, thank you for considering contributing to DSA Companion CLI! It's people like you that make open source such a great community.

## How to Contribute

### 1. Fork the Repository
Click the "Fork" button at the top right of this repository's page to create a copy in your own GitHub account.

### 2. Clone the Repository
Clone your fork to your local machine:
```bash
git clone https://github.com/<your-username>/dsa-companion-cli.git
cd dsa-companion-cli
```

### 3. Run and Initialize
Run the application once to generate your local `config.json` (which is git-ignored):
```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

### 4. Create a Branch
Create a branch for your feature or bug fix:
```bash
git checkout -b feature/your-feature-name
```

### 5. Commit Your Changes
Make your changes, then commit them with a descriptive message:
```bash
git commit -m "feat: add amazing new feature"
```

### 6. Push and Open a Pull Request
Push your branch to your fork and open a Pull Request against the `main` branch of the original repository:
```bash
git push origin feature/your-feature-name
```
Navigate to your fork on GitHub and click "Compare & pull request".

## Best Practices
- Ensure your code follows the existing style.
- Test your changes locally before opening a PR.
- Keep PRs focused on a single issue or feature.
