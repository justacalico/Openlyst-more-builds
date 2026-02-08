# AltStore Repository Setup Summary

## Quick Links

**Add this URL to AltStore:**
```
https://raw.githubusercontent.com/justacalico/Openlyst-more-builds/main/repo/apps.json
```

**Faster CDN Alternative:**
```
https://cdn.jsdelivr.net/gh/JustACalicos/Openlyst-more-builds@main/repo/apps.json
```

---

## What You've Got

✅ **Automatic Build System**
- Fetches apps from OpenLyst API daily (2 AM UTC)
- Generates AltStore-compatible repository JSON
- Updates committed to git history
- Releases tagged for version tracking

✅ **Static URL (Never Changes)**
- GitHub Raw Content URL is permanent
- Works automatically after each commit
- No domain ownership needed
- 100% GitHub uptime guarantee

✅ **Multiple Access Methods**
- Primary: GitHub Raw (`raw.githubusercontent.com`)
- Fast: jsDelivr CDN (`cdn.jsdelivr.net`)
- Archive: GitHub Releases (`github.com/releases`)

---

## Files Created

| File | Purpose |
|------|---------|
| `build_altstore_repo.py` | Main Python build script |
| `.github/workflows/altstore.yml` | GitHub Actions automation |
| `requirements.txt` | Python dependencies |
| `test-build.sh` | Local testing script |
| `BUILD_ALTSTORE_REPO_README.md` | Detailed documentation |
| `ALTSTORE_CONFIG.md` | Configuration reference |

---

## How It Works

```
1. GitHub Actions Trigger (Daily)
        ↓
2. Run build_altstore_repo.py
        ↓
3. Fetch apps from OpenLyst API
        ↓
4. Extract IPA URLs & metadata
        ↓
5. Generate apps.json
        ↓
6. Commit to repo/
        ↓
7. Push to main branch
        ↓
8. Create Release tag
        ↓
9. Deploy to GitHub Pages
        ↓
10. URLs auto-update (no changes needed!)
```

---

## Getting Started

### For Users
1. Open AltStore → Browse
2. Tap + button (top right)
3. Paste: `https://raw.githubusercontent.com/justacalico/Openlyst-more-builds/main/repo/apps.json`
4. Tap Add

### For Local Testing
```bash
chmod +x test-build.sh
./test-build.sh
```

### Manual Workflow Trigger
- Go to GitHub Actions
- Select "Build AltStore Repository"
- Click "Run workflow"

---

## Why GitHub URLs?

✅ No domain required  
✅ 100% uptime (GitHub CDN)  
✅ Automatic versioning (git history)  
✅ Free HTTPS everywhere  
✅ Redundancy (GitHub Releases backup)  
✅ jsDelivr CDN for global speed  

---

## Key Features

| Feature | Details |
|---------|---------|
| **Update Schedule** | Daily at 2 AM UTC |
| **Manual Updates** | Via GitHub Actions workflow |
| **URL Stability** | Permanent, never changes |
| **Fallback** | jsDelivr CDN, GitHub Releases |
| **Authentication** | None required (public) |
| **Rate Limits** | OpenLyst API has none |
| **Version History** | Git commits + releases |
| **Deployment** | GitHub Pages + commits |

---

## Important Notes

- ⚠️ First build will take 2-5 minutes (downloading app metadata)
- 📊 IPA file sizes detected automatically
- 🔄 GitHub Actions has workflow logs for debugging
- 📝 All URLs remain constant forever
- 🛡️ No need to maintain custom infrastructure

---

## Documentation

- **Full Guide**: [BUILD_ALTSTORE_REPO_README.md](BUILD_ALTSTORE_REPO_README.md)
- **Configuration**: [ALTSTORE_CONFIG.md](ALTSTORE_CONFIG.md)
- **OpenLyst API**: https://openlyst.ink/docs/api
- **AltStore Format**: https://github.com/altstoreio/FAQ/blob/main/developers/make-a-source.md

---

## Next Steps

1. **Test locally**: Run `./test-build.sh`
2. **Review** the generated `repo/apps.json`
3. **Commit and push**: `git add repo/ && git commit -m "initial: build altstore repository"`
4. **Test in AltStore**: Add the GitHub URL
5. **Enable Actions**: Make sure GitHub Actions is enabled in Settings

That's it! The build will run automatically from now on.
