# canopyctl Quick Reference

## Installation

```bash
# Python package (recommended)
pip install canopyctl

# Development install
pip install -e .

# Standalone binary (download from releases)
wget https://github.com/canopybmc/canopyctl/releases/latest/download/canopyctl-simple
chmod +x canopyctl-simple
```

## Commands

### Rebase Commands

```bash
# Smart rebase (auto-detects target branch)
canopyctl rebase

# Rebase against specific branch  
canopyctl rebase --branch master
canopyctl rebase --branch kirkstone

# Rebase against different remote
canopyctl rebase --remote origin --branch main

# Continue after resolving conflicts
canopyctl rebase --continue

# Abort rebase and restore original state
canopyctl rebase --abort
```

### Configuration Commands

```bash
# Show overall configuration
canopyctl config show

# Analyze specific recipe
canopyctl config show systemd
canopyctl config show my-custom-service  

# List all recipes
canopyctl config list

# List recipes matching pattern
canopyctl config list "phosphor*"
canopyctl config list "*network*"
```

## Rebase Workflow

### Normal Flow
1. `canopyctl rebase` - Start rebase with auto-detection
2. ✅ Success - patches applied cleanly
3. Test your changes
4. `git push --force-with-lease origin <branch>`

### Conflict Resolution Flow
1. `canopyctl rebase` - Start rebase
2. ❌ Conflicts detected - rebase pauses
3. Edit files to resolve conflicts
4. `git add <resolved-files>`
5. `canopyctl rebase --continue`
6. Repeat steps 3-5 if more conflicts
7. ✅ Success - all patches applied

### Emergency Recovery
1. `canopyctl rebase --abort` - Restore original state
2. Or manually: `git reset --hard canopy-backup-<timestamp>`

## Smart Branch Detection Logic

1. **Exact Match**: Looks for `upstream/current-branch`
2. **Canopy Analysis**: Checks if branch exists on Canopy remote
3. **History Analysis**: Uses git merge-base to find origin branch
4. **Fallback**: Defaults to `upstream/master`

### Examples
- `LTS/2025.08` → detects → `upstream/master`
- `main` → detects → `upstream/master`  
- `feature/xyz` → traces history → best upstream match

## Common Patterns

### Daily Development
```bash
# Morning sync
canopyctl rebase
# Work on features...
# Evening sync
canopyctl rebase
```

### Release Preparation
```bash
# Ensure clean rebase against target
canopyctl rebase --branch master
# Run tests...
# Create release
```

### Troubleshooting
```bash
# Check git status
git status

# Check recent commits  
git log --oneline -10

# Check remotes
git remote -v

# Verify canopyctl installation
canopyctl --help
```

## Error Messages & Solutions

### `Working directory has uncommitted changes`
```bash
# Solution 1: Commit changes
git add .
git commit -m "Work in progress"

# Solution 2: Stash changes  
git stash push -m "Before rebase"
# After rebase: git stash pop
```

### `No upstream remote found`
```bash
git remote add upstream https://github.com/openbmc/openbmc.git
git fetch upstream
```

### `Cannot find branch upstream/xyz`
```bash
# Check available branches
git branch -r | grep upstream

# Use explicit branch
canopyctl rebase --branch master
```

## File Locations

### Generated Files
- `.canopyctl-rebase-state` - Rebase state (temporary)
- `canopy-backup-<timestamp>` - Safety backup branches

### Configuration Files
- `setup.py` / `pyproject.toml` - Package configuration
- `.github/workflows/release.yml` - CI/CD automation

## Environment

### Prerequisites
- Git repository with upstream remote
- Clean working directory (no uncommitted changes)
- Python 3.8+ (for pip install) or standalone binary

### Supported Platforms
- Linux (all distributions)
- macOS (with Python or standalone)
- Windows (with WSL recommended)

## Advanced Usage

### Custom Remotes
```bash
# Add multiple remotes
git remote add company-fork https://github.com/company/openbmc.git

# Rebase against company fork
canopyctl rebase --remote company-fork --branch develop
```

### Automation
```bash
# In scripts/CI
canopyctl rebase --branch master
if [ $? -eq 0 ]; then
    echo "Rebase successful"
    # Continue with build/test
else
    echo "Rebase failed, manual intervention needed"
    exit 1
fi
```

## Help & Documentation

### Built-in Help
```bash
canopyctl --help                # Main help
canopyctl rebase --help         # Rebase help
canopyctl config --help         # Config help
```

### Full Documentation
- `docs/` - Complete documentation
- `README-rebase.md` - Detailed rebase guide
- `INSTALL.md` - Installation instructions
- `DISTRIBUTION.md` - Packaging guide

### Testing
```bash
python test-comprehensive.py    # Run test suite
```

---

**💡 Tip**: Start with `canopyctl rebase` - the auto-detection works for most scenarios!