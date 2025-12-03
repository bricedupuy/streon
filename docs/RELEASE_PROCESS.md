# Streon Release Process

This document outlines the complete process for creating a new Streon release with pre-built binaries.

## Overview

Each Streon release includes:
- Source code (tagged in Git)
- Pre-built binaries for x86_64 and aarch64
- Checksums for verification
- Release notes and documentation

## Prerequisites

Before creating a release:

- [ ] All features tested and working
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated in relevant files
- [ ] Access to both x86_64 and aarch64 build systems (or use GitHub Actions)

## Option 1: Automated Build (GitHub Actions)

**Recommended** - Fully automated binary building.

### 1. Prepare Release

```bash
# Update version in files
vim install/download-binaries.sh  # Update VERSION variable
vim README.md                     # Update version references
vim CHANGELOG.md                  # Add release notes

# Commit changes
git add -A
git commit -m "Prepare v1.0.0 release"
git push origin master
```

### 2. Create Git Tag

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Streon v1.0.0 - Multi-Flow Audio Transport System"

# Push tag
git push origin v1.0.0
```

### 3. Create GitHub Release

1. Go to: https://github.com/bricedupuy/streon/releases/new
2. Select tag: `v1.0.0`
3. Release title: `Streon v1.0.0`
4. Description: Copy from CHANGELOG.md or write release notes
5. Click "Publish release"

### 4. Automatic Binary Building

GitHub Actions will automatically:
1. Detect the new release
2. Build binaries for x86_64
3. Build binaries for aarch64 (using Docker + QEMU)
4. Upload all binaries to the release
5. Generate checksums
6. Create release notes

**Build time:** ~60-90 minutes (runs in parallel)

### 5. Verify Release

Once workflow completes:

1. Check release page has all files:
   - `ffmpeg-x86_64.tar.gz` + `.sha256`
   - `liquidsoap-2.4.0-x86_64.tar.gz` + `.sha256`
   - `inferno-x86_64.tar.gz` + `.sha256`
   - `ffmpeg-aarch64.tar.gz` + `.sha256`
   - `liquidsoap-2.4.0-aarch64.tar.gz` + `.sha256`
   - `inferno-aarch64.tar.gz` + `.sha256`
   - `MANIFEST-x86_64.txt`
   - `MANIFEST-aarch64.txt`
   - `RELEASE_NOTES.md`

2. Test download script:
```bash
git clone https://github.com/bricedupuy/streon.git
cd streon
git checkout v1.0.0
sudo ./install/download-binaries.sh
```

## Option 2: Manual Build (Local Systems)

Use this if you need custom builds or GitHub Actions isn't available.

### 1. Build on x86_64 System

```bash
# On x86_64 machine (Debian 13)
git clone https://github.com/bricedupuy/streon.git
cd streon
git checkout v1.0.0

# Install dependencies
sudo ./install/dependencies.sh

# Build binaries
sudo ./install/build-release-binaries.sh

# Binaries are in: ./release-binaries/
ls -lh release-binaries/
```

### 2. Build on aarch64 System

```bash
# On aarch64 machine (Raspberry Pi 5, Debian 13)
git clone https://github.com/bricedupuy/streon.git
cd streon
git checkout v1.0.0

# Install dependencies
sudo ./install/dependencies.sh

# Build binaries
sudo ./install/build-release-binaries.sh

# Binaries are in: ./release-binaries/
ls -lh release-binaries/
```

### 3. Collect Binaries

Transfer all files from both systems to your workstation:

```bash
# From x86_64 system
scp user@x86-builder:~/streon/release-binaries/* ./release-binaries/

# From aarch64 system
scp user@arm-builder:~/streon/release-binaries/* ./release-binaries/
```

### 4. Create GitHub Release Manually

1. Create tag and push (as in Option 1)
2. Create GitHub release
3. Manually upload all binaries from `./release-binaries/`

## Post-Release

### 1. Announce Release

Update the following:
- GitHub Discussions (if enabled)
- Project README.md (latest version reference)
- Documentation site (if applicable)
- Social media / mailing lists

### 2. Test Installation

Test on fresh systems:

```bash
# On Debian 13 (x86_64)
git clone https://github.com/bricedupuy/streon.git
cd streon
git checkout v1.0.0
sudo ./install/debian-13-install.sh
# Choose: Use pre-built binaries? Y

# On Debian 13 (aarch64)
git clone https://github.com/bricedupuy/streon.git
cd streon
git checkout v1.0.0
sudo ./install/debian-13-install.sh
# Choose: Use pre-built binaries? Y
```

Verify:
- Installation completes in ~5 minutes
- All binaries work correctly
- FFmpeg has SRT support: `ffmpeg -protocols | grep srt`
- Liquidsoap runs: `liquidsoap --version`
- Inferno binaries present: `ls /opt/inferno/bin/`

### 3. Monitor Issues

Watch for installation issues:
- GitHub Issues
- Discussion forums
- User feedback

Common issues:
- Checksum verification failures
- Binary incompatibilities
- Missing dependencies
- Network download problems

## Version Numbering

Streon uses Semantic Versioning (SemVer):

- **Major version** (1.x.x): Breaking changes, incompatible API changes
- **Minor version** (x.1.x): New features, backward-compatible
- **Patch version** (x.x.1): Bug fixes, backward-compatible

Examples:
- `v1.0.0` - First stable release
- `v1.1.0` - Added new features (e.g., NDI input support)
- `v1.1.1` - Bug fixes for v1.1.0
- `v2.0.0` - Breaking changes (e.g., new config format)

Pre-release tags:
- `v1.0.0-alpha` - Alpha release
- `v1.0.0-beta.1` - Beta release
- `v1.0.0-rc.1` - Release candidate

## Files to Update for New Release

### 1. Version References

- `install/download-binaries.sh` - `VERSION` variable
- `controller/main.py` - `__version__` variable
- `web-ui/package.json` - `version` field
- `README.md` - Version references

### 2. Documentation

- `CHANGELOG.md` - Add release notes
- `docs/RELEASE_NOTES.md` - Update for this release
- `README.md` - Update "Current Version" section

### 3. Git

- Create and push annotated tag
- Update master branch if needed

## Rollback Process

If a release has critical issues:

### 1. Mark Release as Pre-release

1. Edit GitHub release
2. Check "This is a pre-release"
3. Add warning notice to description

### 2. Fix Issues

```bash
# Create hotfix branch
git checkout v1.0.0
git checkout -b hotfix-v1.0.1

# Fix issues
# ... make changes ...

# Commit and tag
git commit -m "Fix critical bug in XYZ"
git tag -a v1.0.1 -m "Hotfix release"
git push origin hotfix-v1.0.1
git push origin v1.0.1
```

### 3. Create New Release

Follow normal release process for v1.0.1.

## Checklist Template

Use this for each release:

```markdown
## Pre-Release
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Build systems ready (x86_64 + aarch64)

## Release
- [ ] Git tag created and pushed
- [ ] GitHub release created
- [ ] Binaries built (automated or manual)
- [ ] All files uploaded to release
- [ ] Checksums verified

## Post-Release
- [ ] Installation tested on x86_64
- [ ] Installation tested on aarch64
- [ ] Release announced
- [ ] Documentation updated
- [ ] Monitoring for issues

## Verification
- [ ] FFmpeg SRT support: `ffmpeg -protocols | grep srt`
- [ ] Liquidsoap version: `liquidsoap --version`
- [ ] Inferno binaries: `ls /opt/inferno/bin/`
- [ ] Installation time: ~5 minutes
- [ ] Checksums valid: `sha256sum -c *.sha256`
```

## Troubleshooting Release Builds

### GitHub Actions Build Fails

**Check workflow logs:**
1. Go to: https://github.com/bricedupuy/streon/actions
2. Find failed workflow
3. Review build logs

**Common issues:**
- Dependency installation failure
- Build timeout (increase timeout in workflow)
- Out of disk space (clean up build artifacts)

**Solution:**
- Fix issues in `build-release-binaries.sh`
- Delete failed release and try again

### Manual Build Fails

**FFmpeg build fails:**
- Check dependencies: `sudo ./install/dependencies.sh`
- Review FFmpeg configure output
- Check available disk space

**Liquidsoap build fails:**
- OPAM issues: `opam update && opam upgrade`
- OCaml version: Ensure compatible version
- Missing dependencies

**Inferno build fails:**
- Rust not installed: Run `install/inferno-setup.sh`
- Cargo errors: `cargo clean` and rebuild
- Git submodules: `git submodule update --init --recursive`

## Support

For questions about the release process:
- Review [BINARY_DISTRIBUTION.md](BINARY_DISTRIBUTION.md)
- Check GitHub Actions workflow logs
- Open an issue: https://github.com/bricedupuy/streon/issues
