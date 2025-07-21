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
./canopyctl.py --help

# Show configuration help
./canopyctl.py config --help

# Show overall configuration
./canopyctl.py config show

# Analyze a specific recipe
./canopyctl.py config show <recipe-name>
```

### Examples

```bash
# Analyze the systemd recipe
./canopyctl.py config show systemd

# Analyze a custom recipe
./canopyctl.py config show my-custom-service
```

## Requirements

- Python 3.6 or later
- Must be run from within or near a Yocto/OpenEmbedded build environment

## Installation

1. Clone or download this repository
2. Make the script executable:
   ```bash
   chmod +x canopyctl.py
   ```
3. Run from the build environment directory

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
