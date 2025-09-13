# canopyctl Documentation

Welcome to the comprehensive documentation for `canopyctl`, a tool for managing and inspecting Canopy configurations and performing smart rebases against upstream OpenBMC.

## Documentation Overview

This documentation covers all aspects of `canopyctl`, from basic usage to advanced deployment scenarios.

## Table of Contents

### Getting Started
- **[Installation Guide](../INSTALL.md)** - How to install canopyctl on your system
- **[Quick Start](../README.md)** - Basic usage examples and getting started
- **[Requirements](../README.md#requirements)** - System requirements and dependencies

### Core Features
- **[Rebase Documentation](../README-rebase.md)** - Complete guide to smart rebase functionality
  - Auto-detection of target branches
  - Canopy-aware branch analysis  
  - Conflict resolution workflows
  - Safety features and backup management

- **[Configuration Analysis](../README.md#usage)** - Yocto/OpenEmbedded configuration inspection
  - Recipe analysis
  - Build detection
  - Systemd service tracking

### Distribution & Deployment
- **[Packaging and Distribution](packaging-and-distribution.md)** - Complete guide to packaging and redistributing canopyctl
  - Python package distribution (PyPI)
  - Standalone executable creation
  - Container distribution
  - Automated CI/CD releases
  - Platform-specific packaging

### Development & Contributing
- **[Phase 1 Summary](../PHASE1-SUMMARY.md)** - Implementation details and completed features
- **[Release Summary](../RELEASE-SUMMARY.md)** - Current release status and distribution methods
- **[Testing](../test-comprehensive.py)** - Comprehensive test suite

## Quick Reference

### Installation
```bash
# Python package (recommended)
pip install canopyctl

# Standalone binary (no Python required)
# Download from: https://github.com/canopybmc/canopyctl/releases
./canopyctl-simple rebase
```

### Basic Usage
```bash
# Smart rebase with auto-detection
canopyctl rebase

# Rebase against specific branch
canopyctl rebase --branch master

# Configuration analysis
canopyctl config show systemd
canopyctl config list "phosphor*"
```

### Key Features

#### 🎯 **Smart Rebase**
- **Auto-detection**: Automatically finds the correct upstream branch to rebase against
- **Canopy-aware**: Understands Canopy-specific branch patterns (LTS branches, etc.)
- **Safety-first**: Creates backups before any operation
- **Conflict handling**: Interactive resolution with clear guidance

#### 🔧 **Configuration Analysis**
- **Recipe inspection**: Analyze Yocto/OpenEmbedded recipes
- **Build detection**: Determine if recipes are included in builds
- **Service tracking**: Find and analyze systemd services

#### 📦 **Multiple Distribution Methods**
- **Python package**: `pip install canopyctl`
- **Standalone binary**: Single-file executable (no Python required)  
- **Container**: Docker images for consistent environments
- **Automated releases**: GitHub Actions for CI/CD

## Architecture Overview

### Core Components
- **CLI Interface** (`canopyctl.cli`) - Command-line argument parsing and dispatch
- **Git Operations** (`canopyctl.core.git_ops`) - Safe Git command wrapper
- **Repository Analysis** (`canopyctl.core.repo_analyzer`) - Smart branch detection and patch analysis
- **Rebase Engine** (`canopyctl.core.rebase_engine`) - Core rebase orchestration
- **Backup Management** (`canopyctl.core.backup_manager`) - Safety backup creation and restoration

### Command Structure
```
canopyctl
├── rebase              # Smart rebase functionality
│   ├── --branch        # Specify target branch
│   ├── --remote        # Specify remote
│   ├── --continue      # Continue after conflicts
│   └── --abort         # Abort and restore
└── config              # Configuration analysis
    ├── show [recipe]   # Show recipe details
    └── list [pattern]  # List available recipes
```

## Use Cases

### For Developers
- **Daily workflow**: Keep Canopy patches rebased against upstream
- **Branch management**: Smart detection of which upstream branch to target
- **Conflict resolution**: Clear guidance when conflicts occur

### For System Administrators  
- **Configuration audit**: Understand what's built into images
- **Service analysis**: Track systemd services across recipes
- **Build validation**: Verify recipe inclusion and configuration

### For CI/CD Pipelines
- **Automated rebasing**: Keep downstream forks up-to-date
- **Build verification**: Ensure consistent configurations
- **Release management**: Automated package distribution

## Support & Community

### Getting Help
- **Command help**: `canopyctl --help`, `canopyctl rebase --help`
- **Documentation**: This docs folder contains comprehensive guides
- **Issues**: Report bugs and request features on GitHub
- **Testing**: Run `python test-comprehensive.py` for validation

### Contributing
1. **Read the documentation**: Understand the architecture and features
2. **Run tests**: Ensure your changes don't break existing functionality  
3. **Follow patterns**: Use existing code patterns and conventions
4. **Update docs**: Keep documentation in sync with changes

## Version History

- **v0.2.0**: Complete rebase functionality with Canopy-aware detection
- **v0.1.0**: Initial configuration analysis features

## License

This project is licensed under the Apache License 2.0. See LICENSE file for details.

---

**Need help?** Check the specific documentation files listed above, or run `canopyctl --help` for command-specific guidance.