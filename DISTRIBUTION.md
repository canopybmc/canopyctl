# Distribution Guide for canopyctl

This guide covers different ways to package and redistribute `canopyctl` for various audiences and deployment scenarios.

## 1. Python Package Distribution (Recommended)

### Build Distribution Packages

```bash
# Install build tools
pip install build twine

# Build wheel and source distribution
python -m build

# This creates:
# - dist/canopyctl-0.2.0-py3-none-any.whl (binary wheel)
# - dist/canopyctl-0.2.0.tar.gz (source distribution)
```

### Distribution Methods

#### A) PyPI (Python Package Index)
```bash
# Test on PyPI Test (recommended first)
twine upload --repository testpypi dist/*

# Upload to main PyPI
twine upload dist/*

# Users can then install with:
pip install canopyctl
```

#### B) Private Package Repository
```bash
# Upload to private PyPI server (e.g., DevPI, Gemfury)
twine upload --repository-url https://your-private-pypi.com/simple/ dist/*
```

#### C) Direct File Distribution
```bash
# Users can install directly from wheel file
pip install canopyctl-0.2.0-py3-none-any.whl

# Or from source
pip install canopyctl-0.2.0.tar.gz
```

## 2. Standalone Executable (No Python Required)

### Using PyInstaller

```bash
# Install PyInstaller
pip install pyinstaller

# Create standalone executable
pyinstaller --onefile --name canopyctl canopyctl.py

# This creates a single binary in dist/canopyctl
# Users can run it without Python installed
```

### Cross-Platform Builds
```bash
# Linux
pyinstaller --onefile --name canopyctl-linux canopyctl.py

# For Windows (if running on Windows)
pyinstaller --onefile --name canopyctl.exe canopyctl.py

# For macOS (if running on macOS)
pyinstaller --onefile --name canopyctl-macos canopyctl.py
```

## 3. Container Distribution

### Docker Image
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
# Build Docker image
docker build -t canopyctl:0.2.0 .

# Tag for distribution
docker tag canopyctl:0.2.0 ghcr.io/canopybmc/canopyctl:0.2.0
docker tag canopyctl:0.2.0 ghcr.io/canopybmc/canopyctl:latest

# Push to GitHub Container Registry
docker push ghcr.io/canopybmc/canopyctl:0.2.0
docker push ghcr.io/canopybmc/canopyctl:latest

# Users run with:
docker run --rm -v $(pwd):/workspace -w /workspace ghcr.io/canopybmc/canopyctl:latest rebase
```

## 4. System Package Distribution

### Debian/Ubuntu (.deb)
Create `debian/` directory structure and use:
```bash
# Install packaging tools
sudo apt install devscripts build-essential

# Create .deb package
dpkg-buildpackage -us -uc

# Users install with:
sudo dpkg -i canopyctl_0.2.0_all.deb
sudo apt install -f  # Fix any dependencies
```

### Red Hat/Fedora (.rpm)
Create RPM spec file and use:
```bash
# Install packaging tools
sudo dnf install rpm-build rpmdevtools

# Build RPM
rpmbuild -ba canopyctl.spec

# Users install with:
sudo rpm -i canopyctl-0.2.0-1.noarch.rpm
# Or: sudo dnf install canopyctl-0.2.0-1.noarch.rpm
```

### Arch Linux (AUR)
Create PKGBUILD file for the AUR.

## 5. GitHub Releases

### Automated Release Pipeline
Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-and-release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install build twine pyinstaller
    
    - name: Build Python packages
      run: python -m build
    
    - name: Build standalone executable
      run: |
        pyinstaller --onefile --name canopyctl canopyctl.py
        mv dist/canopyctl dist/canopyctl-linux-x64
    
    - name: Create Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: \${{ github.ref }}
        release_name: Release \${{ github.ref }}
        draft: false
        prerelease: false
    
    - name: Upload Release Assets
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: \${{ secrets.GITHUB_TOKEN }}
      with:
        upload_url: \${{ steps.create_release.outputs.upload_url }}
        asset_path: ./dist/canopyctl-0.2.0-py3-none-any.whl
        asset_name: canopyctl-0.2.0-py3-none-any.whl
        asset_content_type: application/zip
```

## 6. Distribution Strategies by Audience

### For Python Developers
- **PyPI**: `pip install canopyctl`
- **GitHub**: `pip install git+https://github.com/canopybmc/canopyctl.git`

### For System Administrators  
- **System packages**: `.deb`, `.rpm`, AUR packages
- **Container**: Docker images
- **Standalone binary**: Single executable file

### For CI/CD Pipelines
- **Container images**: Consistent environment
- **Wheel files**: Fast installation in Docker builds
- **GitHub Actions**: Direct integration

### For Enterprise Users
- **Private PyPI**: Internal package repository
- **Tarball**: Self-contained source distribution
- **Container registry**: Private Docker registry

## 7. Release Checklist

Before creating a distribution:

- [ ] Update version number in `setup.py` and `pyproject.toml`
- [ ] Update `CHANGELOG.md` with new features
- [ ] Run comprehensive tests: `python test-comprehensive.py`
- [ ] Update documentation
- [ ] Create git tag: `git tag v0.2.0`
- [ ] Build packages: `python -m build`
- [ ] Test installation: `pip install dist/canopyctl-*.whl`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Create GitHub release with assets
- [ ] Update Docker images
- [ ] Announce release

## 8. Version Management

### Semantic Versioning
- `MAJOR.MINOR.PATCH` (e.g., `0.2.0`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Automated Versioning
Consider using `setuptools_scm` for git-based versioning:

```toml
# In pyproject.toml
[tool.setuptools_scm]
write_to = "canopyctl/_version.py"
```

## 9. Security Considerations

### Signing Releases
- Sign wheel files: `gpg --detach-sign --armor dist/*.whl`
- Sign git tags: `git tag -s v0.2.0`
- Use trusted publishing for PyPI

### Checksums
```bash
# Generate checksums for verification
sha256sum dist/* > dist/SHA256SUMS
```

## 10. Testing Distributions

### Test Each Distribution Method
```bash
# Test wheel installation
pip install dist/canopyctl-0.2.0-py3-none-any.whl
canopyctl --help

# Test source installation  
pip install dist/canopyctl-0.2.0.tar.gz
canopyctl rebase --help

# Test standalone executable
./dist/canopyctl-linux-x64 --help
```

## Summary

Choose distribution methods based on your audience:
- **Python users**: PyPI packages
- **System users**: OS packages or standalone binaries  
- **Container users**: Docker images
- **Developers**: GitHub releases with multiple formats
- **Enterprise**: Private repositories and signed releases