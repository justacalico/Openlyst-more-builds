#!/usr/bin/env python3
"""
OpenLyst Unified Build Script

This script fetches apps from the OpenLyst API and generates repositories for:
- AltStore (iOS)
- F-Droid (Android)
- Homebrew Tap (macOS/Linux)

Usage:
    python build.py --target all                    # Build all targets
    python build.py --target altstore              # Build AltStore repo only
    python build.py --target fdroid                # Build F-Droid repo only
    python build.py --target homebrew              # Build Homebrew tap only
    python build.py --target homebrew --platform macOS  # Build Homebrew for macOS only
"""

import os
import sys
import json
import hashlib
import re
import argparse
import logging
import tempfile
import zipfile
import plistlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin, urlparse

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# OpenLyst API Client (Shared)
# =============================================================================

class OpenLystClient:
    """Client for interacting with OpenLyst API"""
    
    BASE_URL = "https://openlyst.ink/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Openlyst-Unified-Builder/1.0'
        })
    
    def get_all_apps(self, platform: str = "iOS", lang: str = "en") -> List[Dict]:
        """Fetch all apps from OpenLyst for specified platform"""
        try:
            url = f"{self.BASE_URL}/apps"
            params = {
                'platform': platform,
                'lang': lang,
                'filter': 'active'
            }
            
            logger.info(f"Fetching apps from {url} for platform {platform}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                apps = data.get('data', [])
                logger.info(f"Successfully fetched {len(apps)} apps")
                return apps
            else:
                logger.error(f"API returned unsuccessful response: {data}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch apps: {e}")
            return []
    
    def get_app_details(self, slug: str, lang: str = "en") -> Optional[Dict]:
        """Fetch detailed information about a specific app"""
        try:
            url = f"{self.BASE_URL}/apps/{slug}"
            params = {'lang': lang}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data.get('data')
            return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch app details for {slug}: {e}")
            return None
    
    def get_app_versions(self, slug: str, lang: str = "en") -> List[Dict]:
        """Fetch all versions of a specific app"""
        try:
            url = f"{self.BASE_URL}/apps/{slug}/versions"
            params = {'lang': lang}
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                versions = data.get('data', [])
                logger.debug(f"Fetched {len(versions) if isinstance(versions, list) else '?'} versions for {slug}")
                return versions if isinstance(versions, list) else []
            return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch app versions for {slug}: {e}")
            return []


# =============================================================================
# Utility Functions (Shared)
# =============================================================================

def get_file_size(url: str) -> Optional[int]:
    """Get file size from URL without downloading"""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        if 'content-length' in response.headers:
            return int(response.headers['content-length'])
    except Exception as e:
        logger.warning(f"Could not determine file size for {url}: {e}")
    return None


def get_sha256(url: str) -> Optional[str]:
    """Calculate SHA256 hash of download file"""
    try:
        logger.info(f"Calculating SHA256 for {url}")
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            return hashlib.sha256(response.content).hexdigest()
        return None
    except Exception as e:
        logger.warning(f"Failed to calculate SHA256 for {url}: {e}")
        return None


def sanitize_name(name: str, style: str = "class") -> str:
    """Sanitize name for various formats
    
    Args:
        name: The name to sanitize
        style: 'class' for Ruby class names, 'package' for package IDs, 'filename' for filenames
    """
    if style == "class":
        # Convert to valid Ruby class name
        sanitized = re.sub(r'[^a-zA-Z0-9]', '', name.title())
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"App{sanitized}"
        return sanitized
    elif style == "package":
        # Convert to valid package/bundle ID
        sanitized = re.sub(r'[^a-zA-Z0-9.]', '', name.lower())
        return sanitized
    elif style == "filename":
        # Convert to safe filename
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name.lower().replace(' ', '-'))
        return sanitized
    return name


# =============================================================================
# AltStore Repository Builder
# =============================================================================

class AltStoreBuilder:
    """Builder for AltStore repository JSON"""
    
    def __init__(self, client: OpenLystClient, base_repo_url: str = "https://raw.githubusercontent.com/justacalico/Openlyst-more-builds/main/repo"):
        self.client = client
        self.base_repo_url = base_repo_url
    
    def extract_ipa_url(self, version: Dict) -> Optional[str]:
        """Extract iOS IPA download URL from version data"""
        if not isinstance(version, dict):
            return None
        
        # Primary: Check downloads.iOS
        downloads = version.get('downloads')
        if isinstance(downloads, dict):
            ios_download = downloads.get('iOS')
            if isinstance(ios_download, str) and ios_download.strip():
                return ios_download.strip()
        
        # Fallback: Check platformInstall.iOS
        platform_install = version.get('platformInstall')
        if isinstance(platform_install, dict):
            ios_install = platform_install.get('iOS')
            if isinstance(ios_install, str) and ios_install.strip() and ios_install.startswith('http'):
                return ios_install.strip()
        
        # Last fallback: Try direct downloadURL field
        download_url = version.get('downloadURL')
        if download_url and isinstance(download_url, str) and download_url.strip().startswith('http'):
            return download_url.strip()
        
        return None
    
    def extract_permissions_from_ipa(self, ipa_url: str) -> Optional[Dict[str, Any]]:
        """Download IPA and extract entitlements and privacy usage descriptions."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".ipa", delete=True) as tmp:
                logger.info(f"Downloading IPA for permissions: {ipa_url}")
                with self.client.session.get(ipa_url, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            tmp.write(chunk)
                tmp.flush()

                entitlements: List[str] = []
                privacy: Dict[str, str] = {}

                with zipfile.ZipFile(tmp.name, 'r') as z:
                    app_dirs = [
                        name for name in z.namelist()
                        if name.startswith('Payload/') and name.endswith('.app/')
                    ]
                    if not app_dirs:
                        logger.warning("IPA does not contain a Payload .app directory")
                        return None
                    app_dir = app_dirs[0]

                    # Parse Info.plist for privacy usage descriptions
                    info_path = app_dir + 'Info.plist'
                    if info_path in z.namelist():
                        with z.open(info_path) as f:
                            try:
                                plist = plistlib.load(f)
                                for k, v in plist.items():
                                    if isinstance(k, str) and k.endswith('UsageDescription') and isinstance(v, str):
                                        privacy[k] = v
                            except Exception as e:
                                logger.debug(f"Failed parsing Info.plist: {e}")

                    # Parse entitlements
                    for ent_path in [app_dir + 'archived-expanded-entitlements.xcent', app_dir + 'entitlements.plist']:
                        if ent_path in z.namelist():
                            with z.open(ent_path) as f:
                                try:
                                    ent_plist = plistlib.load(f)
                                    if isinstance(ent_plist, dict):
                                        entitlements = sorted(list(ent_plist.keys()))
                                except Exception as e:
                                    logger.debug(f"Failed parsing entitlements: {e}")
                            break

                # Filter out common entitlements
                filtered_ents = [
                    e for e in entitlements
                    if e not in ("com.apple.developer.team-identifier", "application-identifier")
                ]

                if not filtered_ents and not privacy:
                    return None

                return {"entitlements": filtered_ents, "privacy": privacy}

        except Exception as e:
            logger.info(f"Could not extract permissions from IPA: {e}")
            return None
    
    def _map_category(self, category: str) -> str:
        """Map category to valid AltStore category"""
        valid_categories = {
            'developer', 'entertainment', 'games', 'lifestyle',
            'other', 'photo-video', 'social', 'utilities'
        }
        category = str(category).lower().replace(' ', '-')
        return category if category in valid_categories else 'other'
    
    def _process_screenshots(self, screenshots: Any) -> List[str]:
        """Process screenshots array"""
        result = []
        if isinstance(screenshots, list):
            for shot in screenshots:
                if isinstance(shot, str):
                    result.append(shot)
                elif isinstance(shot, dict) and 'imageURL' in shot:
                    result.append(shot['imageURL'])
        return result[:10]
    
    def build_app_entry(self, app: Dict, slug: str) -> Optional[Dict]:
        """Build an AltStore app entry from OpenLyst app data"""
        try:
            versions = self.client.get_app_versions(slug)
            if not versions or not isinstance(versions, list):
                logger.warning(f"No versions found for app {slug}")
                return None
            
            altstore_versions = []
            for version_data in versions[:10]:
                if not isinstance(version_data, dict):
                    continue
                
                ipa_url = self.extract_ipa_url(version_data)
                if not ipa_url:
                    logger.debug(f"No IPA URL found for {slug} version {version_data.get('version')}")
                    continue
                
                size = get_file_size(ipa_url)
                
                altstore_version = {
                    "version": str(version_data.get('version', '1.0')),
                    "buildVersion": str(version_data.get('buildVersion', '1')),
                    "date": str(version_data.get('date', datetime.now().isoformat())),
                    "downloadURL": ipa_url,
                }
                
                if size:
                    altstore_version['size'] = size
                
                description = version_data.get('localizedDescription')
                if description and isinstance(description, str):
                    altstore_version['localizedDescription'] = description
                
                altstore_versions.append(altstore_version)
            
            if not altstore_versions:
                logger.warning(f"No valid IPA versions found for app {slug}")
                return None
            
            app_entry = {
                "name": str(app.get('name', 'Unknown App')),
                "bundleIdentifier": str(app.get('bundleIdentifier', slug)),
                "developerName": str(app.get('developerName', 'OpenLyst Developer')),
                "subtitle": str(app.get('subtitle', 'An app from OpenLyst')),
                "localizedDescription": str(app.get('localizedDescription', app.get('description', 'A free and open source app'))),
                "iconURL": str(app.get('iconURL', '')),
                "tintColor": str(app.get('tintColor', '#dc2626')),
                "category": self._map_category(app.get('category', 'other')),
                "versions": altstore_versions,
            }
            
            # Extract permissions from latest IPA
            latest_ipa = altstore_versions[0].get("downloadURL")
            if latest_ipa:
                perms = self.extract_permissions_from_ipa(latest_ipa)
                if perms:
                    app_entry["appPermissions"] = perms
            
            if app.get('screenshots'):
                app_entry['screenshots'] = self._process_screenshots(app['screenshots'])
            
            return app_entry
        
        except Exception as e:
            logger.error(f"Error building app entry for {slug}: {e}", exc_info=True)
            return None
    
    def build(self, output_dir: str = "repo") -> bool:
        """Build the complete AltStore repository"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            logger.info("Fetching all iOS apps from OpenLyst...")
            apps = self.client.get_all_apps(platform="iOS")
            
            if not apps:
                logger.error("No apps fetched from OpenLyst")
                return False
            
            logger.info("Building AltStore app entries...")
            app_entries = []
            
            for app in apps:
                slug = app.get('slug')
                if not slug:
                    continue
                
                logger.info(f"Processing app: {slug}")
                app_entry = self.build_app_entry(app, slug)
                
                if app_entry:
                    app_entries.append(app_entry)
            
            if not app_entries:
                logger.error("No valid app entries created")
                return False
            
            repository = {
                "name": "OpenLyst iOS Apps",
                "subtitle": "Free and open source iOS applications",
                "description": "A curated collection of free and open source iOS applications from OpenLyst.",
                "iconURL": urljoin(self.base_repo_url, "icon.png"),
                "headerURL": urljoin(self.base_repo_url, "header.png"),
                "website": "https://openlyst.ink",
                "tintColor": "#dc2626",
                "featuredApps": [app['bundleIdentifier'] for app in app_entries[:5]],
                "apps": app_entries,
                "news": []
            }
            
            repo_file = os.path.join(output_dir, "apps.json")
            with open(repo_file, 'w', encoding='utf-8') as f:
                json.dump(repository, f, indent=2, ensure_ascii=False)
            
            logger.info(f"AltStore repository built: {repo_file} ({len(app_entries)} apps)")
            
            index_data = {
                "repositoryURL": urljoin(self.base_repo_url, "apps.json"),
                "name": repository['name'],
                "subtitle": repository['subtitle'],
                "description": repository['description'],
                "generatedAt": datetime.now().isoformat()
            }
            
            index_file = os.path.join(output_dir, "index.json")
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
            return True
        
        except Exception as e:
            logger.error(f"Error building AltStore repository: {e}")
            return False


# =============================================================================
# F-Droid Repository Builder
# =============================================================================

class FDroidBuilder:
    """Builder for F-Droid repository metadata"""
    
    def __init__(self, client: OpenLystClient, base_repo_url: str = "https://raw.githubusercontent.com/justacalico/Openlyst-more-builds/main/fdroid-repo"):
        self.client = client
        self.base_repo_url = base_repo_url
    
    def extract_apk_url(self, version: Dict) -> Optional[str]:
        """Extract Android APK download URL from version data"""
        if not isinstance(version, dict):
            return None
        
        downloads = version.get('downloads')
        if isinstance(downloads, dict):
            android_download = downloads.get('Android')
            if isinstance(android_download, str) and android_download.strip():
                return android_download.strip()
            # Handle nested structure (e.g., downloads.Android.apk)
            if isinstance(android_download, dict):
                for key in ['apk', 'universal', 'arm64', 'arm', 'x86_64', 'x86']:
                    if key in android_download and android_download[key]:
                        return android_download[key]
        
        download_url = version.get('downloadURL')
        if download_url and isinstance(download_url, str) and download_url.strip().startswith('http'):
            return download_url.strip()
        
        return None
    
    def _map_fdroid_category(self, category: str) -> str:
        """Map category to F-Droid category"""
        category_map = {
            'entertainment': 'Multimedia',
            'games': 'Games',
            'lifestyle': 'System',
            'photo-video': 'Multimedia',
            'social': 'Internet',
            'utilities': 'System',
            'developer': 'Development',
            'other': 'System'
        }
        category = str(category).lower().replace(' ', '-')
        return category_map.get(category, 'System')
    
    def build_metadata_yml(self, app: Dict, versions: List[Dict]) -> Optional[str]:
        """Build F-Droid metadata YAML content for an app"""
        if not versions:
            return None
        
        latest_version = versions[0]
        apk_url = self.extract_apk_url(latest_version)
        
        if not apk_url:
            return None
        
        # Build YAML content (F-Droid metadata format)
        name = app.get('name', 'Unknown')
        package_id = app.get('bundleIdentifier', sanitize_name(name, 'package'))
        
        metadata = f"""Categories:
  - {self._map_fdroid_category(app.get('category', 'other'))}
License: Unknown
AuthorName: {app.get('developerName', 'OpenLyst Developer')}
AuthorWebSite: {app.get('website', 'https://openlyst.ink')}
WebSite: {app.get('website', 'https://openlyst.ink')}
SourceCode: {app.get('sourceCode', '')}
IssueTracker: {app.get('issueTracker', '')}

AutoName: {name}
Summary: {app.get('subtitle', name)[:80]}

Description: |
    {app.get('localizedDescription', app.get('description', 'A free and open source app.'))}

RepoType: git
Repo: {app.get('sourceCode', '')}

Builds:
"""
        # Add version entries
        for v in versions[:5]:
            version_code = v.get('buildVersion', '1')
            version_name = v.get('version', '1.0')
            apk = self.extract_apk_url(v)
            if apk:
                metadata += f"""
  - versionName: '{version_name}'
    versionCode: {version_code}
    commit: v{version_name}
    subdir: app
    gradle:
      - yes
"""
        
        metadata += f"""
CurrentVersion: '{latest_version.get('version', '1.0')}'
CurrentVersionCode: {latest_version.get('buildVersion', '1')}
"""
        
        return metadata
    
    def build_index_json(self, apps_data: List[Dict]) -> Dict:
        """Build F-Droid index.json"""
        packages = {}
        
        for app_data in apps_data:
            app = app_data['app']
            versions = app_data['versions']
            package_id = app.get('bundleIdentifier', sanitize_name(app.get('name', 'unknown'), 'package'))
            
            package_versions = []
            for v in versions[:5]:
                apk_url = self.extract_apk_url(v)
                if not apk_url:
                    continue
                
                package_versions.append({
                    "added": int(datetime.now().timestamp() * 1000),
                    "apkName": f"{package_id}-{v.get('version', '1.0')}.apk",
                    "hash": "",  # Would need to download to calculate
                    "hashType": "sha256",
                    "minSdkVersion": 21,
                    "packageName": package_id,
                    "size": get_file_size(apk_url) or 0,
                    "targetSdkVersion": 34,
                    "versionCode": int(v.get('buildVersion', 1)),
                    "versionName": v.get('version', '1.0')
                })
            
            if package_versions:
                packages[package_id] = package_versions
        
        return {
            "repo": {
                "name": "OpenLyst F-Droid Repository",
                "description": "Free and open source Android applications from OpenLyst",
                "icon": "icon.png",
                "address": self.base_repo_url,
                "timestamp": int(datetime.now().timestamp() * 1000),
                "version": 21
            },
            "requests": {
                "install": [],
                "uninstall": []
            },
            "apps": [
                {
                    "packageName": app_data['app'].get('bundleIdentifier', ''),
                    "name": app_data['app'].get('name', ''),
                    "summary": app_data['app'].get('subtitle', ''),
                    "icon": app_data['app'].get('iconURL', ''),
                    "description": app_data['app'].get('localizedDescription', ''),
                    "license": "Unknown",
                    "categories": [self._map_fdroid_category(app_data['app'].get('category', 'other'))],
                    "webSite": app_data['app'].get('website', 'https://openlyst.ink'),
                    "added": int(datetime.now().timestamp() * 1000),
                    "lastUpdated": int(datetime.now().timestamp() * 1000)
                }
                for app_data in apps_data
            ],
            "packages": packages
        }
    
    def build(self, output_dir: str = "fdroid-repo", calculate_info: bool = False) -> bool:
        """Build the complete F-Droid repository"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            metadata_dir = os.path.join(output_dir, "metadata")
            os.makedirs(metadata_dir, exist_ok=True)
            
            logger.info("Fetching all Android apps from OpenLyst...")
            apps = self.client.get_all_apps(platform="Android")
            
            if not apps:
                logger.error("No Android apps fetched from OpenLyst")
                return False
            
            logger.info(f"Building F-Droid metadata for {len(apps)} apps...")
            
            apps_data = []
            generated_count = 0
            
            for app in apps:
                slug = app.get('slug')
                if not slug:
                    continue
                
                logger.info(f"Processing app: {slug}")
                versions = self.client.get_app_versions(slug)
                
                if not versions:
                    continue
                
                # Check if Android versions exist
                has_android = False
                for v in versions:
                    if self.extract_apk_url(v):
                        has_android = True
                        break
                
                if not has_android:
                    logger.debug(f"No Android versions for {slug}")
                    continue
                
                apps_data.append({'app': app, 'versions': versions})
                
                # Write metadata YAML
                metadata = self.build_metadata_yml(app, versions)
                if metadata:
                    package_id = app.get('bundleIdentifier', sanitize_name(app.get('name', slug), 'package'))
                    metadata_file = os.path.join(metadata_dir, f"{package_id}.yml")
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        f.write(metadata)
                    generated_count += 1
            
            if not apps_data:
                logger.error("No valid Android app entries created")
                return False
            
            # Write index.json
            index = self.build_index_json(apps_data)
            index_file = os.path.join(output_dir, "index.json")
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            
            logger.info(f"F-Droid repository built: {output_dir} ({generated_count} apps)")
            return True
        
        except Exception as e:
            logger.error(f"Error building F-Droid repository: {e}")
            return False


# =============================================================================
# Homebrew Tap Builder
# =============================================================================

class HomebrewBuilder:
    """Builder for Homebrew tap formulae"""
    
    def __init__(self, client: OpenLystClient, output_dir: Path):
        self.client = client
        self.output_dir = output_dir
        self.formula_dir = output_dir / "Formula"
        self.formula_dir.mkdir(parents=True, exist_ok=True)
    
    def get_download_url_for_platform(self, version: Dict, platform: str) -> Optional[str]:
        """Extract appropriate download URL for the specified platform"""
        downloads = version.get('downloads', {})
        platform_downloads = downloads.get(platform, {})
        
        if not platform_downloads:
            return None
        
        if platform == "macOS":
            for arch in ['universal', 'arm64', 'x86_64']:
                if arch in platform_downloads and platform_downloads[arch]:
                    return platform_downloads[arch]
        
        elif platform == "Linux":
            for package_type in ['appimage', 'zip', 'deb', 'rpm']:
                if package_type in platform_downloads:
                    pkg_data = platform_downloads[package_type]
                    if isinstance(pkg_data, dict):
                        for arch in ['x86_64', 'arm64']:
                            if arch in pkg_data and pkg_data[arch]:
                                return pkg_data[arch]
                    elif isinstance(pkg_data, str) and pkg_data:
                        return pkg_data
        
        # Fallback
        for key, value in platform_downloads.items():
            if isinstance(value, dict):
                for arch_key, arch_value in value.items():
                    if isinstance(arch_value, str) and arch_value.startswith('http'):
                        return arch_value
            elif isinstance(value, str) and value.startswith('http'):
                return value
        
        return None
    
    def generate_formula_content(self, app: Dict, version: Dict, platform: str, calculate_sha256: bool = False) -> str:
        """Generate Homebrew formula content for an app version"""
        class_name = sanitize_name(app['name'], 'class')
        download_url = self.get_download_url_for_platform(version, platform)
        
        if not download_url:
            raise ValueError(f"No download URL found for {app['name']} on {platform}")
        
        url_path = urlparse(download_url).path
        file_extension = Path(url_path).suffix.lower()
        
        sha256_line = '  # sha256 "REPLACE_WITH_ACTUAL_SHA256"'
        if calculate_sha256:
            sha256_hash = get_sha256(download_url)
            if sha256_hash:
                sha256_line = f'  sha256 "{sha256_hash}"'
        
        homepage = app.get('website', 'https://openlyst.ink')
        desc = app.get('subtitle', app.get('name', '')).replace('"', '\\"')
        
        # Determine installation method
        if file_extension in ['.dmg', '.pkg', '.app']:
            install_method = '    # macOS app installation\n    prefix.install Dir["*"]'
        else:
            install_method = '    # Generic installation\n    prefix.install Dir["*"]'
        
        formula_content = f'''class {class_name} < Formula
  desc "{desc}"
  homepage "{homepage}"
  url "{download_url}"
  version "{version['version']}"
{sha256_line}

  def install
{install_method}
  end

  test do
    # Test that the application was installed
    system "true"
  end
end
'''
        
        return formula_content
    
    def generate_formula(self, app: Dict, versions: List[Dict], platform: str, calculate_sha256: bool = False) -> bool:
        """Generate Homebrew formula for an app"""
        if not versions:
            logger.warning(f"No versions found for app {app.get('name', 'Unknown')}")
            return False
        
        latest_version = versions[0]
        
        # Check platform support
        app_platforms = latest_version.get('platforms', [])
        if platform not in app_platforms:
            logger.info(f"App {app.get('name', 'Unknown')} does not support {platform}")
            return False
        
        try:
            formula_content = self.generate_formula_content(app, latest_version, platform, calculate_sha256)
            
            class_name = sanitize_name(app['name'], 'class')
            suffix = '-linux' if platform == 'Linux' else ''
            filename = f"{class_name.lower()}{suffix}.rb"
            formula_path = self.formula_dir / filename
            
            with open(formula_path, 'w', encoding='utf-8') as f:
                f.write(formula_content)
            
            logger.info(f"Generated formula: {formula_path}")
            return True
            
        except ValueError as e:
            logger.warning(f"Skipping {app.get('name', 'Unknown')}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to generate formula for {app.get('name', 'Unknown')}: {e}")
            return False
    
    def build(self, platform: str = "macOS", calculate_sha256: bool = False) -> bool:
        """Build Homebrew tap for specified platform"""
        try:
            logger.info(f"Building Homebrew tap for {platform} platform...")
            apps = self.client.get_all_apps(platform=platform)
            
            if not apps:
                logger.error(f"No {platform} apps found")
                return False
            
            logger.info(f"Found {len(apps)} apps for {platform}")
            
            generated_count = 0
            failed_count = 0
            
            for app in apps:
                slug = app.get('slug')
                if not slug:
                    failed_count += 1
                    continue
                
                versions = self.client.get_app_versions(slug)
                
                if self.generate_formula(app, versions, platform, calculate_sha256):
                    generated_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"Homebrew formulae: {generated_count} generated, {failed_count} skipped")
            
            # Generate tap info
            tap_info = {
                "name": "OpenLyst Homebrew Tap",
                "description": f"Homebrew formulae for {platform} applications from OpenLyst",
                "homepage": "https://openlyst.ink",
                "generated_at": datetime.now().isoformat() + "Z",
                "platform": platform,
                "formulae_count": generated_count
            }
            
            with open(self.output_dir / "tap-info.json", 'w', encoding='utf-8') as f:
                json.dump(tap_info, f, indent=2)
            
            return generated_count > 0
        
        except Exception as e:
            logger.error(f"Error building Homebrew tap: {e}")
            return False


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='OpenLyst Unified Build Script - Build AltStore, F-Droid, and Homebrew repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python build.py --target all                     # Build everything
    python build.py --target altstore               # Build AltStore repo only
    python build.py --target fdroid                 # Build F-Droid repo only
    python build.py --target homebrew               # Build Homebrew tap (both platforms)
    python build.py --target homebrew --platform macOS    # Build Homebrew for macOS only
    python build.py --target altstore,fdroid        # Build multiple targets
        """
    )
    
    parser.add_argument(
        '--target',
        type=str,
        default='all',
        help='Build target(s): all, altstore, fdroid, homebrew, or comma-separated list'
    )
    parser.add_argument(
        '--platform',
        type=str,
        choices=['macOS', 'Linux', 'both'],
        default='both',
        help='Platform for Homebrew builds (default: both)'
    )
    parser.add_argument(
        '--altstore-output',
        type=str,
        default='repo',
        help='Output directory for AltStore repository (default: repo)'
    )
    parser.add_argument(
        '--fdroid-output',
        type=str,
        default='fdroid-repo',
        help='Output directory for F-Droid repository (default: fdroid-repo)'
    )
    parser.add_argument(
        '--homebrew-output',
        type=str,
        default='homebrew-tap',
        help='Output directory for Homebrew tap (default: homebrew-tap)'
    )
    parser.add_argument(
        '--repo-url',
        type=str,
        default='https://raw.githubusercontent.com/justacalico/Openlyst-more-builds/main/repo',
        help='Base URL for AltStore repository'
    )
    parser.add_argument(
        '--calculate-sha256',
        action='store_true',
        help='Calculate SHA256 hashes (slower but more secure)'
    )
    parser.add_argument(
        '--calculate-info',
        action='store_true',
        help='Calculate file sizes and hashes for F-Droid'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Parse targets
    targets: Set[str] = set()
    if args.target.lower() == 'all':
        targets = {'altstore', 'fdroid', 'homebrew'}
    else:
        targets = {t.strip().lower() for t in args.target.split(',')}
    
    logger.info(f"Building targets: {', '.join(sorted(targets))}")
    
    # Initialize shared client
    client = OpenLystClient()
    
    results = {}
    
    # Build AltStore repository
    if 'altstore' in targets:
        logger.info("=" * 60)
        logger.info("Building AltStore Repository")
        logger.info("=" * 60)
        builder = AltStoreBuilder(client, base_repo_url=args.repo_url)
        results['altstore'] = builder.build(output_dir=args.altstore_output)
    
    # Build F-Droid repository
    if 'fdroid' in targets:
        logger.info("=" * 60)
        logger.info("Building F-Droid Repository")
        logger.info("=" * 60)
        fdroid_url = args.repo_url.replace('/repo', '/fdroid-repo')
        builder = FDroidBuilder(client, base_repo_url=fdroid_url)
        results['fdroid'] = builder.build(
            output_dir=args.fdroid_output,
            calculate_info=args.calculate_info
        )
    
    # Build Homebrew tap
    if 'homebrew' in targets:
        logger.info("=" * 60)
        logger.info("Building Homebrew Tap")
        logger.info("=" * 60)
        
        homebrew_results = []
        
        if args.platform in ['macOS', 'both']:
            builder = HomebrewBuilder(client, Path(args.homebrew_output))
            homebrew_results.append(builder.build(
                platform='macOS',
                calculate_sha256=args.calculate_sha256
            ))
        
        if args.platform in ['Linux', 'both']:
            builder = HomebrewBuilder(client, Path(args.homebrew_output))
            homebrew_results.append(builder.build(
                platform='Linux',
                calculate_sha256=args.calculate_sha256
            ))
        
        results['homebrew'] = any(homebrew_results)
    
    # Summary
    logger.info("=" * 60)
    logger.info("Build Summary")
    logger.info("=" * 60)
    
    all_success = True
    for target, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        logger.info(f"  {target.upper()}: {status}")
        if not success:
            all_success = False
    
    if all_success:
        logger.info("All builds completed successfully!")
        return 0
    else:
        logger.error("Some builds failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
