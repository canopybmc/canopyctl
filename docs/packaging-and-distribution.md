# Packaging and Distribution Guide for canopyctl

## Overview

This guide provides comprehensive information on how to package and redistribute `canopyctl` for different audiences and deployment scenarios. The project supports multiple distribution methods to accommodate various use cases, from individual developer installations to enterprise-wide deployment.

## Table of Contents

- [Distribution Methods](#distribution-methods)
- [Quick Start](#quick-start)
- [Package Types](#package-types)
- [Automated Releases](#automated-releases)
- [Manual Distribution](#manual-distribution)
- [Platform-Specific Packaging](#platform-specific-packaging)
- [Release Process](#release-process)
- [Testing Distributions](#testing-distributions)
- [Security Considerations](#security-considerations)

## Distribution Methods

### 1. Python Package Distribution (PyPI)

**Best for**: Python developers, automated deployments

```bash
# Build distribution packages
python -m build

# Install build tools (if not already installed)
pip install build twine

# Upload to PyPI
twine upload dist/*

# Users install with:
pip install canopyctl
canopyctl rebase
```

**Generated Files**:
- `canopyctl-0.2.0-py3-none-any.whl` (19KB) - Binary wheel
- `canopyctl-0.2.0.tar.gz` (20KB) - Source distribution

### 2. Standalone Executable

**Best for**: System administrators, users without Python

```bash
# Build standalone executable
pip install pyinstaller
pyinstaller --onefile --name canopyctl-simple canopyctl_simple.py

# Users run directly (no Python required)
./canopyctl-simple rebase
```

**Generated Files**:
- `canopyctl-simple` (7.7MB) - Self-contained binary including Python runtime

### 3. Container Distribution

**Best for**: Docker environments, CI/CD pipelines

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENTRYPOINT ["canopyctl"]
CMD ["--help"]
```

Build and distribute:
```bash
docker build -t canopyctl:0.2.0 .
docker push ghcr.io/canopybmc/canopyctl:0.2.0

# Users run with:
docker run --rm -v $(pwd):/workspace -w /workspace \
  ghcr.io/canopybmc/canopyctl:latest rebase
```

## Quick Start

### For End Users

**Python Package (Recommended)**:
```bash
pip install canopyctl
canopyctl --help
canopyctl rebase
```

**Standalone Binary**:
```bash
# Download from GitHub releases
wget https://github.com/canopybmc/canopyctl/releases/latest/download/canopyctl-simple
chmod +x canopyctl-simple
./canopyctl-simple rebase
```

### For Maintainers

**Create Release**:
```bash
# Update version numbers in setup.py and pyproject.toml
git add .
git commit -m "Release v0.2.1"
git tag v0.2.1
git push origin v0.2.1  # Triggers automated build and release
```

## Package Types

### Python Wheel (.whl)

**Advantages**:
- Small size (19KB)
- Fast installation
- Platform independent
- Full feature set

**Usage**:
```bash
pip install canopyctl-0.2.0-py3-none-any.whl
```

### Source Distribution (.tar.gz)

**Advantages**:
- Can be installed on any Python platform
- Shows complete source code
- Can be modified before installation

**Usage**:
```bash
pip install canopyctl-0.2.0.tar.gz
```

### Standalone Executable

**Advantages**:
- No Python dependency
- Single file distribution
- Works on systems without Python

**Disadvantages**:
- Large file size (7.7MB)
- Platform-specific (need separate builds for Windows/macOS/Linux)

**Usage**:
```bash
./canopyctl-simple rebase --help
```

## Automated Releases

### GitHub Actions Workflow

The project includes a comprehensive GitHub Actions workflow (`.github/workflows/release.yml`) that automatically:

1. **Tests** on Python 3.8, 3.9, 3.10, and 3.11
2. **Builds** wheel, source distribution, and standalone binary
3. **Creates** GitHub release with changelog
4. **Uploads** all artifacts with checksums
5. **Publishes** to PyPI automatically

### Workflow Triggers

The workflow triggers on:
```bash
git tag v*  # Any tag starting with 'v' (e.g., v0.2.0, v1.0.0)
```

### Release Artifacts

Each release includes:
- `canopyctl-X.Y.Z-py3-none-any.whl` - Python wheel
- `canopyctl-X.Y.Z.tar.gz` - Source distribution
- `canopyctl-linux-x64` - Standalone Linux binary
- `SHA256SUMS` - Checksums for verification

## Manual Distribution

### Building Packages Locally

```bash
# Install build dependencies
pip install build twine pyinstaller

# Build Python packages
python -m build

# Build standalone executable
pyinstaller --onefile --name canopyctl-simple canopyctl_simple.py

# Generate checksums
cd dist
sha256sum * > SHA256SUMS
```

### Distribution Options

#### Private PyPI Server
```bash
# Upload to private repository
twine upload --repository-url https://your-private-pypi.com/simple/ dist/*
```

#### Direct File Distribution
```bash
# Share wheel files directly
scp dist/canopyctl-*.whl user@server:/path/
```

#### Internal Package Repositories
- **Artifactory**: Upload wheels to JFrog Artifactory
- **Nexus**: Use Sonatype Nexus for package hosting
- **DevPI**: Self-hosted PyPI-compatible server

## Platform-Specific Packaging

### Linux Packages

#### Debian/Ubuntu (.deb)
```bash
# Create debian packaging
sudo apt install devscripts build-essential
dpkg-buildpackage -us -uc

# Install
sudo dpkg -i canopyctl_0.2.0_all.deb
```

#### Red Hat/Fedora (.rpm)
```bash
# Create RPM spec and build
sudo dnf install rpm-build rpmdevtools
rpmbuild -ba canopyctl.spec

# Install
sudo rpm -i canopyctl-0.2.0-1.noarch.rpm
```

#### Arch Linux (AUR)
Create `PKGBUILD` file for Arch User Repository submission.

### Cross-Platform Executables

```bash
# Build for different platforms (requires platform-specific runners)
# Linux
pyinstaller --onefile --name canopyctl-linux canopyctl_simple.py

# Windows (on Windows)
pyinstaller --onefile --name canopyctl.exe canopyctl_simple.py

# macOS (on macOS)
pyinstaller --onefile --name canopyctl-macos canopyctl_simple.py
```

## Release Process

### Pre-Release Checklist

- [ ] Update version numbers in `setup.py` and `pyproject.toml`
- [ ] Update `CHANGELOG.md` with new features and fixes
- [ ] Run comprehensive tests: `python test-comprehensive.py`
- [ ] Test installation from built packages
- [ ] Update documentation if needed

### Creating a Release

1. **Update Version**:
   ```bash
   # Edit setup.py and pyproject.toml
   version = "0.2.1"
   ```

2. **Commit and Tag**:
   ```bash
   git add .
   git commit -m "Release v0.2.1"
   git tag v0.2.1
   ```

3. **Push Tag**:
   ```bash
   git push origin v0.2.1
   ```

4. **Monitor Automation**:
   - Check GitHub Actions for successful build
   - Verify release appears on GitHub
   - Confirm PyPI publication

### Version Management

The project follows **Semantic Versioning** (SemVer):
- `MAJOR.MINOR.PATCH` (e.g., `0.2.1`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

## Testing Distributions

### Local Testing

```bash
# Test wheel installation
pip install dist/canopyctl-0.2.0-py3-none-any.whl
canopyctl --help

# Test source installation
pip install dist/canopyctl-0.2.0.tar.gz
canopyctl rebase --help

# Test standalone executable
./dist/canopyctl-simple --help
```

### Installation Testing

```bash
# Test in clean environment
python -m venv test_env
source test_env/bin/activate
pip install canopyctl
canopyctl --version
deactivate
rm -rf test_env
```

### Cross-Platform Testing

Use GitHub Actions or local VMs to test on:
- Ubuntu 20.04, 22.04
- CentOS/RHEL 8, 9
- Fedora latest
- macOS latest
- Windows 10, 11

## Security Considerations

### Package Signing

```bash
# Sign wheel files
gpg --detach-sign --armor dist/*.whl

# Sign git tags
git tag -s v0.2.0 -m "Signed release v0.2.0"
```

### Checksums

Always provide checksums for verification:
```bash
sha256sum dist/* > dist/SHA256SUMS
```

### PyPI Security

- Use API tokens instead of passwords
- Enable 2FA on PyPI account
- Use trusted publishing for GitHub Actions

### Supply Chain Security

- Pin dependencies in `requirements.txt`
- Use `pip-audit` to check for vulnerabilities
- Regularly update dependencies

## Distribution Strategies by Audience

### Python Developers
```bash
pip install canopyctl
```
**Benefits**: Fast, updatable, integrated with Python ecosystem

### System Administrators
```bash
./canopyctl-simple rebase
```
**Benefits**: No Python dependency, single file, portable

### CI/CD Pipelines
```dockerfile
RUN pip install canopyctl
```
**Benefits**: Reproducible builds, version pinning, container-ready

### Enterprise Users
- Private PyPI repositories
- Signed packages with GPG
- Internal approval processes
- Audit trails and compliance

## Troubleshooting

### Common Issues

**Import Errors in Standalone**:
- Use `canopyctl_simple.py` instead of full package
- Avoid complex import structures in PyInstaller

**Version Conflicts**:
- Use virtual environments
- Pin specific versions in requirements

**Permission Issues**:
- Use `--user` flag for pip installation
- Check file permissions on standalone executables

### Debug Commands

```bash
# Check installed version
pip show canopyctl

# Verify package contents
python -m zipfile -l canopyctl-*.whl

# Test import
python -c "import canopyctl; print('OK')"
```

## Summary

This comprehensive distribution system supports:

- **Multiple formats**: Python packages, standalone binaries, containers
- **Automated releases**: GitHub Actions for consistent deployment
- **Platform support**: Linux, macOS, Windows (where applicable)
- **Security**: Signed packages, checksums, trusted publishing
- **Flexibility**: Choose the right distribution method for your audience

The system is designed to scale from individual developer use to enterprise-wide deployment while maintaining security and reliability standards.