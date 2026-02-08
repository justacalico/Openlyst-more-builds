# AltStore Builder

Automated build system to create an AltStore repository from the OpenLyst API with a static, unchanging URL.

## Overview

This project automatically:
1. Fetches all iOS apps from the [OpenLyst API](https://openlyst.ink/docs/api)
2. Extracts IPA files and metadata
3. Builds an AltStore-compatible repository JSON
4. Deploys with a **static, permanent URL** that never changes
5. Updates daily automatically

## Repository URL

**Add to AltStore:**
```
https://raw.githubusercontent.com/justacalico/Openlyst-more-builds/main/repo/apps.json
```

**CDN Mirror (faster, optional):**
```
https://cdn.jsdelivr.net/gh/JustACalicos/Openlyst-more-builds@main/repo/apps.json
```

Both URLs are **permanently static** — the path never changes even after new builds. GitHub serves updates automatically with every commit.

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ OpenLyst API (openlyst.ink/api/v1)                          │
│ - Provides app metadata, versions, and download links       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Python Build Script (build_altstore_repo.py)                │
│ - Fetches all iOS apps                                      │
│ - Extracts IPA URLs and metadata                            │
│ - Determines file sizes                                     │
│ - Validates data                                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ AltStore Repository JSON                                    │
│ - Standardized format for AltStore app distribution         │
│ - Located in /repo/apps.json                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
GitHub Pages    GitHub Releases  Git Repository
(Pages Deploy)  (Versioned)      (Historical Records)
```

### Build Process

1. **GitHub Actions Workflow** (`.github/workflows/altstore.yml`)
   - Triggers: Daily at 2 AM UTC or manual dispatch
   - Runs on Ubuntu 22.04
   - Python 3.11

2. **Build Script** (`build_altstore_repo.py`)
   - Connects to OpenLyst API
   - Fetches app data, versions, and metadata
   - Extracts IPA download URLs
   - Determines file sizes
   - Validates all entries
   - Generates AltStore-compatible JSON

3. **Deployment**
   - Git commit to `main` branch (preserves history)
   - GitHub Release tagged with build number
   - GitHub Pages deployment (served via HTTPS)
   - Static URLs remain unchanged

## Usage

### For Users

**In AltStore:**
1. Browse → + (add source)
2. Enter repository URL
3. Tap Add

### For Developers

**Local Build:**
```bash
python build_altstore_repo.py --output-dir repo --repo-url https://repo.openlyst.ink
```

**With Verbose Output:**
```bash
python build_altstore_repo.py --output-dir repo --repo-url https://repo.openlyst.ink --verbose
```

**Manual Workflow Trigger:**
- Go to GitHub Actions
- Select "Build AltStore Repository"
- Click "Run workflow"
- Optionally specify custom repository URL

## Configuration

### Environment Variables

The GitHub Actions workflow respects these inputs:

- `REPO_URL` - Static base repository URL (default: `https://repo.openlyst.ink`)
- `OUTPUT_DIR` - Output directory for repository files (default: `repo`)

### Schedule

Edit `.github/workflows/altstore.yml` to change build schedule:

```yaml
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

## API Response Format

The builder expects the OpenLyst API to return apps with this structure:

```json
{
  "success": true,
  "data": [
    {
      "name": "App Name",
      "slug": "app-slug",
      "bundleIdentifier": "com.example.app",
      "subtitle": "Description",
      "localizedDescription": "Full description",
      "iconURL": "https://...",
      "tintColor": "#dc2626",
      "platforms": ["iOS", "macOS", ...],
      "versions": [...]
    }
  ]
}
```

## Output Format

The generated `apps.json` conforms to the [AltStore source specification](https://github.com/altstoreio/FAQ/blob/main/developers/make-a-source.md):

```json
{
  "name": "OpenLyst iOS Apps",
  "subtitle": "Free and open source iOS applications",
  "description": "...",
  "iconURL": "https://repo.openlyst.ink/icon.png",
  "headerURL": "https://repo.openlyst.ink/header.png",
  "website": "https://openlyst.ink",
  "tintColor": "#dc2626",
  "featuredApps": ["com.app.one", "com.app.two"],
  "apps": [
    {
      "name": "App Name",
      "bundleIdentifier": "com.example.app",
      "developerName": "Developer",
      "subtitle": "Short description",
      "localizedDescription": "Full description",
      "iconURL": "https://...",
      "tintColor": "#dc2626",
      "versions": [
        {
          "version": "1.0",
          "buildVersion": "1",
          "date": "2024-01-15",
          "downloadURL": "https://.../app.ipa",
          "size": 12345678
        }
      ]
    }
  ],
  "news": []
}
```

## Files

- **`build_altstore_repo.py`** - Main build script
- **`.github/workflows/altstore.yml`** - GitHub Actions workflow
- **`repo/apps.json`** - Generated repository (git-tracked for history)
- **`repo/index.json`** - Repository metadata (auto-generated)

## Features

✅ **Static URL Structure** - Never changes between builds  
✅ **Automatic Daily Updates** - Scheduled GitHub Actions  
✅ **Error Handling** - Graceful failures with detailed logging  
✅ **Version History** - Git commits preserve all builds  
✅ **Release Tags** - Tagged releases for tracking  
✅ **GitHub Pages** - Served via HTTPS with landing page  
✅ **No Authentication** - Uses public OpenLyst API  
✅ **Extensible** - Easy to modify for custom needs  

## Troubleshooting

### Build Fails to Complete
Check workflow logs in GitHub Actions for error messages. Common issues:
- Network timeout connecting to OpenLyst API
- Invalid IPA URLs in OpenLyst data
- Insufficient permissions for git operations

### Repository Not Showing in AltStore
1. Verify URL is correctly formatted
2. Check repository JSON syntax: `jq . repo/apps.json`
3. Ensure all required fields are present
4. Check app has valid IPA download URL

### File Size Detection Failing
If file sizes aren't being detected:
- IPA URLs may require authentication
- Server may not support HEAD requests
- Network timeout during size check

## Links

- [OpenLyst](https://openlyst.ink/)
- [OpenLyst API Documentation](https://openlyst.ink/docs/api)
- [AltStore Documentation](https://altstoreio.github.io/)
- [AltStore Source Format](https://github.com/altstoreio/FAQ/blob/main/developers/make-a-source.md)

## License

This builder is provided as-is for creating AltStore repositories from OpenLyst data.
