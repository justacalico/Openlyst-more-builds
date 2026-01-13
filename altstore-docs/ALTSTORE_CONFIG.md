# AltStore Repository Configuration

This file documents the static repository configuration.

## Repository Metadata

- **Name**: OpenLyst iOS Apps
- **Subtitle**: Free and open source iOS applications
- **Website**: https://openlyst.ink
- **Tint Color**: #dc2626 (OpenLyst Red)

## Static URLs

These URLs **never change** between builds:

### Primary Repository URL
```
https://raw.githubusercontent.com/httpanimations/Openlyst-more-builds/main/repo/apps.json
```
Served via GitHub Raw Content CDN (auto-updated with every commit)

### CDN URL (Fast Cache)
```
https://cdn.jsdelivr.net/gh/httpanimations/Openlyst-more-builds@main/repo/apps.json
```
Served via jsDelivr CDN for faster downloads globally (auto-purges on new commits)

### Metadata URL
```
https://raw.githubusercontent.com/httpanimations/Openlyst-more-builds/main/repo/index.json
```

## Update Schedule

- **Frequency**: Daily at 2 AM UTC
- **Source**: OpenLyst API (openlyst.ink/api/v1)
- **Automatic**: Yes, via GitHub Actions
- **Manual**: Can be triggered via GitHub Actions workflow

## Repository Contents

Each build includes:

1. **All Active iOS Apps** from OpenLyst
2. **Latest Versions** for each app
3. **IPA Download Links** extracted from OpenLyst
4. **App Metadata**:
   - Name, description, icon
   - Bundle identifier
   - Tint colors
   - Categories
   - File sizes
5. **Version Information**:
   - Version numbers
   - Build numbers
   - Release dates
   - Changelogs (when available)

## AltStore Compatibility

The generated JSON strictly follows the [AltStore source specification](https://github.com/altstoreio/FAQ/blob/main/developers/make-a-source.md):

- ✅ Valid JSON schema
- ✅ All required fields present
- ✅ Proper bundle identifiers
- ✅ Valid icon URLs
- ✅ Correct date formats (ISO 8601)
- ✅ Working download URLs
- ✅ File sizes included

## Usage in AltStore

**URL to add:**
```
https://raw.githubusercontent.com/httpanimations/Openlyst-more-builds/main/repo/apps.json
```

**Steps:**
1. Open AltStore → Browse
2. Tap + (top right)
3. Paste URL
4. Tap Add
5. Apps will appear in the source

## Deployment Infrastructure

### Current Setup
- **Repository Host**: GitHub (openlyst-more-builds)
- **Raw Content CDN**: GitHub Raw (cdn.jsdelivr.net compatible)
- **CI/CD**: GitHub Actions
- **Version Control**: Git
- **Releases**: GitHub Releases

### Static URL Strategy

The URL structure is designed to be **permanent and unchanging**:

- Base URL never changes: `https://raw.githubusercontent.com/httpanimations/Openlyst-more-builds/main/repo`
- Endpoint never changes: `/apps.json`
- Content is updated in-place with each commit
- GitHub ensures 100% uptime as a CDN
- Git history preserves all versions
- Old versions accessible via GitHub Releases

### Fallback Options
Multiple ways to access the repository:

1. **Primary - GitHub Raw Content** (100% uptime SLA):
   ```
   https://raw.githubusercontent.com/httpanimations/Openlyst-more-builds/main/repo/apps.json
   ```

2. **Secondary - jsDelivr CDN** (global fast cache):
   ```
   https://cdn.jsdelivr.net/gh/httpanimations/Openlyst-more-builds@main/repo/apps.json
   ```

3. **Archive - GitHub Releases** (version history):
   ```
   https://github.com/httpanimations/Openlyst-more-builds/releases/download/altstore-repo-{BUILD_NUMBER}
   https://cdn.jsdelivr.net/gh/httpanimations/Openlyst-more-builds@main/repo/apps.json
   ```

## Monitoring

Track build status:
- GitHub Actions: Settings → Actions → Build AltStore Repository
- Release Tags: Releases → altstore-repo-{number}
- Commits: History in repo/ directory

## Error Handling

If a build fails:
1. GitHub Actions sends workflow notification
2. Previous version remains available
3. Error logs available in Actions run details
4. Automatic retry on next scheduled time

## API Dependencies

This system depends on:
- **OpenLyst API** (openlyst.ink/api/v1)
  - No authentication required
  - No rate limits
  - Public and stable
  - CORS enabled

## Customization

To modify the build process:

1. Edit `build_altstore_repo.py`:
   - Change featured apps count
   - Filter apps by category
   - Modify app metadata
   - Add custom descriptions

2. Edit `.github/workflows/altstore.yml`:
   - Change schedule
   - Add additional steps
   - Configure notifications
   - Modify deployment targets

3. Edit this config file to document changes

## Maintenance

### Regular Tasks
- Monitor build success/failure rate
- Check for OpenLyst API changes
- Review error logs weekly
- Update documentation as needed

### Long-term Stability
- Keep GitHub repository active
- Maintain git history
- Test fallback URLs quarterly
- Document any infrastructure changes

## Support

For issues:
1. Check GitHub Issues in this repository
2. Review GitHub Actions logs
3. Verify OpenLyst API is accessible
4. Test repository URL manually

---

**Last Updated**: See git history
**Build System**: Python 3.11 + GitHub Actions
**AltStore Version Support**: All recent versions
