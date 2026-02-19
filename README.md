# OpenLyst Multi-Platform Builds

This project provides builds for OpenLyst projects across multiple platforms.

https://openlyst.ink

**📦 [OpenLyst Builds — Releases & Repositories](https://justacalico.github.io/Openlyst-more-builds/)** — A GitHub Pages site listing all pre-releases, repositories (AltStore, F-Droid, Homebrew, AUR, Docker), and GitHub releases in one place. Enable Pages in repo Settings → Pages → Source: Deploy from branch → Branch: main, folder: `/docs`.

## Unified Build Script

All repositories are generated using a single unified build script (`build.py`) that supports AltStore (iOS), F-Droid (Android), Homebrew (macOS/Linux), and AUR (Arch Linux).

### Usage

```bash
# Build all repositories
python build.py --target all

# Build specific targets
python build.py --target altstore          # AltStore only
python build.py --target fdroid            # F-Droid only
python build.py --target homebrew          # Homebrew only
python build.py --target aur               # AUR PKGBUILDs only (for Arch Linux)
python build.py --target altstore,fdroid   # Multiple targets

# Homebrew platform options
python build.py --target homebrew --platform macOS   # macOS only
python build.py --target homebrew --platform Linux   # Linux only
python build.py --target homebrew --platform both    # Both platforms

# Additional options
python build.py --target all --calculate-sha256      # Calculate SHA256 hashes
python build.py --target all --verbose               # Verbose logging
```

### GitHub Actions

Run the "Build All Repositories" workflow to update all repositories at once, or use the individual workflows for specific targets.

---

## AltStore (iOS)

- Add this Source URL in AltStore: `https://raw.githubusercontent.com/JustACalico/Openlyst-more-builds/main/repo/apps.json`
- CDN URL (faster): `https://cdn.jsdelivr.net/gh/JustACalico/Openlyst-more-builds@main/repo/apps.json`

**Notes:**
- The source includes app permissions (privacy descriptions and entitlements) when available.

---

## F-Droid (Android)

- Repository URL: `https://raw.githubusercontent.com/JustACalico/Openlyst-more-builds/main/fdroid-repo`
- Add this repository in F-Droid client to access OpenLyst Android apps.

---

## Homebrew (macOS/Linux)

### Quick Setup

```bash
brew tap justacalico/openlyst-more-builds
```

### Installation

```bash
# Add the tap
brew tap justacalico/openlyst-more-builds https://github.com/justacalico/openlyst-more-builds.git

# Install apps
brew install justacalico/openlyst-more-builds/app-name

# For cask applications on macOS
brew install --cask justacalico/openlyst-more-builds/app-name
```

### Available Commands

| Command | Description |
|---------|-------------|
| `brew update` | Update the tap |
| `brew search justacalico/openlyst-more-builds/` | List available formulae |
| `brew install justacalico/openlyst-more-builds/app-name` | Install an application |
| `brew uninstall app-name` | Uninstall an application |
| `brew info justacalico/openlyst-more-builds/app-name` | Get formula info |

---

## AUR (Arch Linux)

The "Build All Repositories" workflow can update AUR packages from the [Openlyst API](https://openlyst.ink/docs/api). Known packages (finar-bin, klit-bin, doudou-bin, docan-bin) are updated automatically; any **new app that has a Linux build** (e.g. opentorrent-bin) gets a PKGBUILD generated—create the package on AUR first (e.g. via the AUR website), then the workflow can push to it.

To enable AUR pushes, add these GitHub repository secrets:

| Secret | Description |
|--------|-------------|
| `AUR_SSH_KEY_BASE64` | Base64-encoded private key (e.g. `cat ~/.ssh/id_ed25519 \| base64 -w0`) that has push access to the AUR packages above |
| `AUR_SSH_KEY_PASSWORD` | Passphrase for the key (leave empty if the key has no passphrase) |

Run the workflow with target **aur** or **all** to update AUR packages to the latest version from the Openlyst API.

---

## Docker

Docker images are published to GitHub Container Registry (ghcr.io) for web-based applications.

### Available Images

| App | Image | Description |
|-----|-------|-------------|
| Finar | `ghcr.io/justacalico/finar` | Jellyfin web client |

### Quick Start

```bash
# Pull the latest image
docker pull ghcr.io/justacalico/<app-name>:latest

# Run with default settings
docker run -d -p 8080:80 ghcr.io/justacalico/<app-name>:latest
```

### Finar

A beautiful, modern Jellyfin client built with Flutter.

```bash
# Pull the image
docker pull ghcr.io/justacalico/finar:latest

# Run the container
docker run -d -p 8080:80 ghcr.io/justacalico/finar:latest

# Run with Jellyfin proxy (for CORS)
docker run -d -p 8080:80 -e JELLYFIN_URL=http://your-jellyfin-server:8096 ghcr.io/justacalico/finar:latest
```

Then open http://localhost:8080 in your browser.

### Docker Compose

Example `docker-compose.yml`:

```yaml
services:
  finar:
    image: ghcr.io/justacalico/finar:latest
    ports:
      - "8080:80"
    environment:
      - JELLYFIN_URL=http://your-jellyfin-server:8096  # Optional: for CORS proxy
    restart: unless-stopped
```

### Available Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release |
| `x.y.z` | Specific version (e.g., `1.0.0`) |
| `x.y.z-YYYY-MM-DD` | Version with build date |

---

## Development

### Requirements

```bash
pip install -r requirements.txt
```

### Project Structure

```
├── build.py                    # Unified build script
├── repo/                       # AltStore repository output
├── fdroid-repo/               # F-Droid repository output
├── homebrew-tap/              # Homebrew tap output
│   └── Formula/               # Homebrew formulae
└── .github/workflows/
    └── build-unified.yml      # Unified GitHub Actions workflow
```
