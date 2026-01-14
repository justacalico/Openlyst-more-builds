#!/usr/bin/env python3
"""
OpenLyst to F-Droid Repository Builder

This script fetches Android apps from the OpenLyst API and generates F-Droid metadata
following the F-Droid repository structure.
"""

import os
import json
import requests
import configparser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import hashlib
import re
from urllib.parse import urljoin, urlparse
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OpenLystClient:
    """Client for interacting with OpenLyst API"""
    
    BASE_URL = "https://openlyst.ink/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Openlyst-FDroid-Builder/1.0'
        })
    
    def get_all_apps(self, platform: str = "Android", lang: str = "en") -> List[Dict]:
        """Fetch all Android apps from OpenLyst"""
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


class FDroidMetadataGenerator:
    """Generator for F-Droid metadata from OpenLyst app data"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.metadata_dir = output_dir / "metadata"
        self.repo_dir = output_dir / "repo"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.repo_dir.mkdir(parents=True, exist_ok=True)
    
    def sanitize_package_id(self, bundle_id: str, name: str) -> str:
        """Create a valid F-Droid package identifier"""
        if bundle_id and bundle_id != 'unknown':
            return bundle_id
        
        # Generate from name if no bundle ID
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        return f"ink.openlyst.{clean_name}"
    
    def get_android_download_url(self, version: Dict) -> Optional[str]:
        """Extract Android APK download URL from version data"""
        downloads = version.get('downloads', {})
        android_downloads = downloads.get('Android', {})
        
        if not android_downloads:
            return None
        
        # Look for APK file
        if 'apk' in android_downloads and android_downloads['apk']:
            return android_downloads['apk']
        
        return None
    
    def get_file_size_and_hash(self, url: str) -> tuple[Optional[int], Optional[str]]:
        """Get file size and SHA256 hash from download URL"""
        try:
            logger.info(f"Getting file info for {url}")
            response = requests.head(url, timeout=30)
            
            if response.status_code != 200:
                # Try GET if HEAD fails
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    content = response.content
                    size = len(content)
                    sha256_hash = hashlib.sha256(content).hexdigest()
                    return size, sha256_hash
                return None, None
            else:
                # For HEAD request, get size but need GET for hash
                size = int(response.headers.get('content-length', 0))
                
                # Download for hash calculation
                response = requests.get(url, timeout=60)
                if response.status_code == 200:
                    sha256_hash = hashlib.sha256(response.content).hexdigest()
                    return size, sha256_hash
                
                return size, None
                
        except Exception as e:
            logger.warning(f"Failed to get file info for {url}: {e}")
            return None, None
    
    def generate_metadata_file(self, app: Dict, versions: List[Dict], package_id: str, calculate_info: bool = False) -> bool:
        """Generate F-Droid metadata file for an app"""
        if not versions:
            return False
        
        latest_version = versions[0]
        download_url = self.get_android_download_url(latest_version)
        
        if not download_url:
            raise ValueError(f"No Android APK download URL found for {app['name']}")
        
        # Get file size and hash if requested
        file_size = None
        file_hash = None
        if calculate_info:
            file_size, file_hash = self.get_file_size_and_hash(download_url)
        
        # Create metadata content
        metadata = f"""Categories:
  - System
  - Internet

License: Unknown
AuthorName: OpenLyst
AuthorEmail: contact@openlyst.ink
AuthorWebSite: https://openlyst.ink

Summary: {app.get('subtitle', app['name'])}
Description: |
    {app.get('localizedDescription', app.get('subtitle', 'OpenLyst application'))}
    
    This application is part of the OpenLyst project, providing free and open source software.

RepoType: none
Repo: 

IssueTracker: https://openlyst.ink/support
Changelog: https://openlyst.ink/apps/{app.get('slug', '')}
Donate: https://openlyst.ink/contribute

AutoName: {app['name']}

RequiredTargetSdk: 33

Builds:
  - versionName: '{latest_version['version']}'
    versionCode: {self.version_to_code(latest_version['version'])}
    disable: 'Pre-built binary from OpenLyst'

AutoUpdateMode: None
UpdateCheckMode: None
CurrentVersion: {latest_version['version']}
CurrentVersionCode: {self.version_to_code(latest_version['version'])}
"""
        
        # Write metadata file
        metadata_file = self.metadata_dir / f"{package_id}.yml"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(metadata)
        
        # Create app info for index
        app_info = {
            'packageName': package_id,
            'name': app['name'],
            'summary': app.get('subtitle', app['name']),
            'description': app.get('localizedDescription', app.get('subtitle', 'OpenLyst application')),
            'license': 'Unknown',
            'categories': ['System', 'Internet'],
            'authorName': 'OpenLyst',
            'webSite': 'https://openlyst.ink',
            'issueTracker': 'https://openlyst.ink/support',
            'suggestedVersionName': latest_version['version'],
            'suggestedVersionCode': self.version_to_code(latest_version['version'])
        }
        
        # Add download info if available
        if download_url:
            app_info['packages'] = [{
                'versionName': latest_version['version'],
                'versionCode': self.version_to_code(latest_version['version']),
                'apkName': f"{package_id}_{latest_version['version']}.apk",
                'size': file_size,
                'hash': file_hash,
                'hashType': 'sha256' if file_hash else None,
                'minSdkVersion': 21,
                'targetSdkVersion': 33,
                'packageName': package_id
            }]
            
            # Clean up None values
            if not file_size:
                del app_info['packages'][0]['size']
            if not file_hash:
                del app_info['packages'][0]['hash']
                del app_info['packages'][0]['hashType']
        
        logger.info(f"Generated F-Droid metadata for {app['name']}: {metadata_file}")
        return True
    
    def version_to_code(self, version_str: str) -> int:
        """Convert version string to integer version code"""
        try:
            # Remove non-numeric characters and convert to int
            clean_version = re.sub(r'[^\d.]', '', version_str)
            parts = clean_version.split('.')
            
            # Pad with zeros and convert to integer
            while len(parts) < 3:
                parts.append('0')
            
            # Create version code: major*10000 + minor*100 + patch
            major = int(parts[0]) if parts[0] else 0
            minor = int(parts[1]) if parts[1] else 0
            patch = int(parts[2]) if parts[2] else 0
            
            return major * 10000 + minor * 100 + patch
        except:
            return 1
    
    def generate_repository_index(self, app_infos: List[Dict]) -> Dict:
        """Generate F-Droid repository index"""
        return {
            'repo': {
                'name': 'OpenLyst F-Droid Repository',
                'description': 'Free and open source Android applications from OpenLyst',
                'website': 'https://openlyst.ink',
                'address': 'https://raw.githubusercontent.com/HttpAnimation/Openlyst-more-builds/main/fdroid-repo',
                'timestamp': int(datetime.now().timestamp() * 1000),
                'version': 20001,
                'maxage': 1,
                'icon': 'icon.png'
            },
            'packages': {app['packageName']: [app] for app in app_infos if 'packageName' in app}
        }
    
    def generate_metadata_for_app(self, app: Dict, versions: List[Dict], calculate_info: bool = False) -> Optional[Dict]:
        """Generate metadata for a single app"""
        if not versions:
            logger.warning(f"No versions found for app {app.get('name', 'Unknown')}")
            return None
        
        # Use the latest version
        latest_version = versions[0]
        
        # Check if this app supports Android platform
        app_platforms = latest_version.get('platforms', [])
        if 'Android' not in app_platforms:
            logger.info(f"App {app.get('name', 'Unknown')} does not support Android platform")
            return None
        
        try:
            package_id = self.sanitize_package_id(app.get('bundleIdentifier', ''), app['name'])
            
            if self.generate_metadata_file(app, versions, package_id, calculate_info):
                return {
                    'packageName': package_id,
                    'name': app['name'],
                    'summary': app.get('subtitle', app['name']),
                    'description': app.get('localizedDescription', app.get('subtitle', 'OpenLyst application')),
                    'license': 'Unknown',
                    'categories': ['System', 'Internet'],
                    'authorName': 'OpenLyst',
                    'webSite': 'https://openlyst.ink'
                }
            return None
            
        except ValueError as e:
            logger.warning(f"Skipping {app.get('name', 'Unknown')}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate metadata for {app.get('name', 'Unknown')}: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description='Build F-Droid repository from OpenLyst API')
    parser.add_argument('--output-dir', type=str, default='fdroid-repo',
                       help='Output directory for F-Droid repository')
    parser.add_argument('--calculate-info', action='store_true',
                       help='Calculate file sizes and hashes (slower but more complete)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    output_dir = Path(args.output_dir)
    client = OpenLystClient()
    generator = FDroidMetadataGenerator(output_dir)
    
    logger.info(f"Building F-Droid repository for Android platform in {output_dir}")
    
    # Fetch Android apps
    apps = client.get_all_apps(platform="Android")
    if not apps:
        logger.error("No Android apps found or failed to fetch apps")
        return 1
    
    logger.info(f"Found {len(apps)} Android apps")
    
    # Generate metadata
    generated_count = 0
    failed_count = 0
    app_infos = []
    
    for app in apps:
        slug = app.get('slug')
        if not slug:
            logger.warning(f"No slug found for app: {app}")
            failed_count += 1
            continue
        
        # Get versions for this app
        versions = client.get_app_versions(slug)
        
        app_info = generator.generate_metadata_for_app(app, versions, args.calculate_info)
        if app_info:
            app_infos.append(app_info)
            generated_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Metadata generation complete: {generated_count} successful, {failed_count} failed")
    
    # Generate repository index
    if app_infos:
        repo_index = generator.generate_repository_index(app_infos)
        with open(output_dir / "index.json", 'w', encoding='utf-8') as f:
            json.dump(repo_index, f, indent=2)
        logger.info(f"Generated repository index: {output_dir / 'index.json'}")
    
    # Generate repository info file
    repo_info = {
        "name": "OpenLyst F-Droid Repository",
        "description": "F-Droid metadata for Android applications from OpenLyst",
        "homepage": "https://openlyst.ink",
        "generated_at": datetime.now().isoformat() + "Z",
        "metadata_count": generated_count
    }
    
    with open(output_dir / "repo-info.json", 'w', encoding='utf-8') as f:
        json.dump(repo_info, f, indent=2)
    
    logger.info(f"Generated repository info: {output_dir / 'repo-info.json'}")
    
    # Only exit with error if NO metadata files were generated
    if generated_count == 0:
        logger.error("No metadata files were generated - this indicates a serious problem")
        return 1
    elif failed_count > 0:
        logger.warning(f"{failed_count} apps failed to generate metadata, but {generated_count} succeeded")
        return 0
    
    return 0


if __name__ == "__main__":
    exit(main())