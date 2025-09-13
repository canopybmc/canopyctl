# canopyctl

A command-line tool for managing and inspecting Canopy configurations in Yocto/OpenEmbedded build environments.

## Features

The `canopyctl config show` command provides comprehensive configuration analysis:

- **Recipe Build Detection**: Determines whether a recipe is included in the current build
- **Configuration Parsing**: Shows key configuration variables including:
  - `PACKAGECONFIG`
  - `DISTRO_FEATURES` 
  - `PREFERRED_VERSION`
- **Source Tracking**: Displays where configuration values come from:
  - `local.conf`
  - `machine/*.conf`
  - `distro/*.conf`
  - `*.bb` and `*.bbappend` files
- **Systemd Service Analysis**: Identifies systemd services installed by recipes and their enabled status

## Usage

### Basic Usage

```bash
# Show help
canopyctl --help

# Show configuration help
canopyctl config --help

# Show overall configuration
canopyctl config show

# Analyze a specific recipe
canopyctl config show <recipe-name>

# Smart rebase functionality
canopyctl rebase          # Auto-detects target branch
canopyctl rebase --branch master  # Explicit branch
```

### Examples

```bash
# Analyze the systemd recipe
canopyctl config show systemd

# Analyze a custom recipe
canopyctl config show my-custom-service

# Rebase against upstream with auto-detection
canopyctl rebase

# Rebase against specific branch
canopyctl rebase --branch kirkstone
```

## Requirements

- Python 3.6 or later
- Must be run from within or near a Yocto/OpenEmbedded build environment

## Installation

### Quick Install (Recommended)
```bash
# Install from source directory
pip install -e .

# Now you can use 'canopyctl' directly
canopyctl --help
canopyctl rebase --help
```

### Alternative: Direct Script Usage
```bash
# Make executable and run directly  
chmod +x canopyctl.py
python canopyctl.py --help
```

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## Documentation

📚 **[Complete Documentation](docs/)** - Comprehensive guides and references

- **[Quick Reference](docs/quick-reference.md)** - Command cheat sheet and common patterns
- **[Rebase Guide](README-rebase.md)** - Detailed smart rebase functionality  
- **[Installation Guide](INSTALL.md)** - Step-by-step installation instructions
- **[Packaging & Distribution](docs/packaging-and-distribution.md)** - How to package and redistribute canopyctl

## Build Environment Detection

The tool automatically searches for Yocto/OpenEmbedded build environments by looking for:
- `conf/local.conf` in the current directory
- Common build directory names (`build`, `builds`, `tmp`)
- `conf/bblayers.conf` for layer detection

## Output Format

The tool provides structured output showing:
1. Build directory location
2. Detected meta layers
3. Recipe-specific analysis (if specified)
4. Global configuration variables with their sources
