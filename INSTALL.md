# Installation Instructions for canopyctl

## Method 1: Install from Source (Recommended for Development)

### Prerequisites
- Python 3.8 or newer
- pip package manager
- Git

### Installation Steps

1. **Clone/Download the repository**:
   ```bash
   git clone https://github.com/canopybmc/canopyctl.git
   cd canopyctl
   ```

2. **Install in development mode** (recommended for development):
   ```bash
   pip install -e .
   ```
   
   This creates a `canopyctl` command that automatically reflects any code changes.

3. **Or install normally**:
   ```bash
   pip install .
   ```

4. **Verify installation**:
   ```bash
   canopyctl --help
   canopyctl rebase --help
   ```

### Uninstallation
```bash
pip uninstall canopyctl
```

## Method 2: Direct Binary Installation

If you prefer not to use pip, you can create a direct binary:

1. **Make the Python script executable**:
   ```bash
   chmod +x canopyctl.py
   ```

2. **Create a symlink in your PATH**:
   ```bash
   # Option A: System-wide installation (requires sudo)
   sudo ln -s /path/to/canopyctl/canopyctl.py /usr/local/bin/canopyctl
   
   # Option B: User installation
   mkdir -p ~/.local/bin
   ln -s /path/to/canopyctl/canopyctl.py ~/.local/bin/canopyctl
   
   # Make sure ~/.local/bin is in your PATH
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

## Method 3: Distribution-Specific Packages (Future)

In the future, we plan to provide:
- **Debian/Ubuntu**: `.deb` packages
- **Red Hat/Fedora**: `.rpm` packages  
- **Arch Linux**: AUR packages
- **Homebrew**: For macOS users

## Verification

After installation, verify that canopyctl works:

```bash
# Check version and help
canopyctl --help

# Test in an OpenBMC repository
cd /path/to/openbmc
canopyctl rebase --help
canopyctl rebase  # This will auto-detect the correct branch to rebase against
```

## Troubleshooting

### Command not found
If you get "command not found" after installation:

1. **Check if it's installed**:
   ```bash
   pip list | grep canopyctl
   ```

2. **Check your PATH**:
   ```bash
   echo $PATH
   which canopyctl
   ```

3. **For pip user installation**, ensure `~/.local/bin` is in PATH:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

### Import errors
If you get import errors, try:
```bash
pip install --force-reinstall canopyctl
```

## Development Setup

For contributors and developers:

1. **Install in development mode with test dependencies**:
   ```bash
   pip install -e .[dev]  # (when dev dependencies are added)
   ```

2. **Run tests**:
   ```bash
   python test-comprehensive.py
   ```

3. **Check code quality**:
   ```bash
   # When linting tools are configured
   flake8 canopyctl/
   mypy canopyctl/
   ```

## Requirements

- **Python**: 3.8 or newer
- **Operating System**: Linux, macOS, Windows (with WSL recommended)
- **Git**: Required for rebase functionality
- **Network**: Required for fetching from upstream remotes

## Next Steps

After installation, see:
- `README-rebase.md` for detailed rebase functionality documentation
- `canopyctl rebase --help` for command-line options
- `canopyctl config --help` for configuration analysis features