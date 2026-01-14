This project provides builds for Openlyst projects

https://openlyst.ink

## AltStore (iOS)

- Add this Source URL in AltStore: https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/repo/apps.json
- If Raw is slow (pause), use CDN: https://cdn.jsdelivr.net/gh/HttpAnimation/Openlyst-more-builds@main/repo/apps.json
- To refresh the source, run the "Build AltStore Repository" workflow in GitHub Actions.

Notes
- The source includes app permissions (privacy descriptions and entitlements) when available.

## Homebrew (macOS/Linux)

### Quick Setup

Add this Homebrew tap:

```bash
brew tap httpanimation/openlyst-more-builds
```

Repository: [https://github.com/HttpAnimation/Openlyst-more-builds](https://github.com/HttpAnimation/Openlyst-more-builds)

### Installation

First, add this tap to your Homebrew:

```bash
brew tap httpanimation/openlyst-more-builds https://github.com/HttpAnimation/Openlyst-more-builds.git
```

Then install any available formula:

```bash
# For regular formulae
brew install httpanimation/openlyst-more-builds/app-name

# For cask applications on macOS
brew install --cask httpanimation/openlyst-more-builds/app-name
```

### Available Commands

- **Update the tap**: `brew update`
- **List available formulae**: `brew search httpanimation/openlyst-more-builds/`
- **Install an application**: `brew install httpanimation/openlyst-more-builds/app-name`
- **Uninstall an application**: `brew uninstall app-name`
- **Get formula info**: `brew info httpanimation/openlyst-more-builds/app-name`

### Automated Updates

- Formulae are automatically updated via GitHub Actions
- Manual updates can be triggered via the "Build Homebrew Tap" workflow
- To refresh the tap: run the "Build Homebrew Tap" workflow in GitHub Actions

## Winget (Windows)

### Quick Setup

Install packages using Windows Package Manager:

```powershell
# Install a specific OpenLyst application
winget install OpenLyst.AppName

# Search for available applications
winget search OpenLyst.
```

Repository: [https://github.com/HttpAnimation/Openlyst-more-builds](https://github.com/HttpAnimation/Openlyst-more-builds)

### Available Commands

- **Search packages**: `winget search OpenLyst.`
- **Install application**: `winget install OpenLyst.AppName`
- **Get package info**: `winget show OpenLyst.AppName`
- **Uninstall application**: `winget uninstall OpenLyst.AppName`

### Automated Updates

- Manifests are automatically updated via GitHub Actions
- Manual updates can be triggered via the "Build Winget Repository" workflow

## F-Droid (Android)

### Quick Setup

Add this repository to F-Droid:

1. Open **F-Droid** → **Settings** → **Repositories**
2. Tap **+** to add repository
3. Enter: `https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/fdroid-repo`

Repository: [https://github.com/HttpAnimation/Openlyst-more-builds](https://github.com/HttpAnimation/Openlyst-more-builds)

### Installation

- Browse apps in F-Droid after adding the repository
- Download APKs directly from OpenLyst or GitHub releases
- All applications are free and open source

### Automated Updates

- Repository metadata is automatically updated via GitHub Actions
- Manual updates can be triggered via the "Build F-Droid Repository" workflow
