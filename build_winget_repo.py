#!/usr/bin/env python3
"""
OpenLyst to Winget Repository Builder

This script fetches Windows apps from the OpenLyst API and generates Winget manifest files
following the Microsoft winget-pkgs repository structure.
"""

import os
import json
import requests
import yaml
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
            'User-Agent': 'Openlyst-Winget-Builder/1.0'
        })
    
    def get_all_apps(self, platform: str = "Windows", lang: str = "en") -> List[Dict]:
        """Fetch all Windows apps from OpenLyst"""
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


class WingetManifestGenerator:
    """Generator for Winget manifest files from OpenLyst app data"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.manifests_dir = output_dir / "manifests"
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
    
    def sanitize_package_id(self, name: str, publisher: str = "OpenLyst") -> str:
        """Create a valid Winget package identifier"""
        # Remove special characters and spaces
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name.title())
        clean_publisher = re.sub(r'[^a-zA-Z0-9]', '', publisher)
        return f"{clean_publisher}.{clean_name}"
    
    def get_windows_download_url(self, version: Dict) -> Optional[str]:
        """Extract Windows download URL from version data"""
        downloads = version.get('downloads', {})
        windows_downloads = downloads.get('Windows', {})
        
        if not windows_downloads:
            return None
        
        # Priority order for Windows package types
        for package_type in ['exe', 'msi', 'msix', 'zip']:
            if package_type in windows_downloads:
                pkg_data = windows_downloads[package_type]
                if isinstance(pkg_data, dict):
                    # Check for x86_64 architecture first
                    for arch in ['x86_64', 'arm64']:
                        if arch in pkg_data and pkg_data[arch]:
                            return pkg_data[arch]
                elif isinstance(pkg_data, str) and pkg_data.startswith('http'):
                    return pkg_data
        
        return None
    
    def get_file_sha256(self, url: str) -> Optional[str]:
        """Calculate SHA256 hash of download file"""
        try:
            logger.info(f"Calculating SHA256 for {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            sha256_hash = hashlib.sha256(response.content).hexdigest().upper()
            return sha256_hash
        except Exception as e:
            logger.warning(f"Failed to calculate SHA256 for {url}: {e}")
            return None
    
    def determine_installer_type(self, download_url: str) -> str:
        """Determine installer type from URL"""
        url_path = urlparse(download_url).path.lower()
        
        if url_path.endswith('.msi'):
            return 'msi'
        elif url_path.endswith('.msix'):
            return 'msix'
        elif url_path.endswith('.exe'):
            return 'exe'
        elif url_path.endswith('.zip'):
            return 'zip'
        else:
            return 'exe'  # Default assumption
    
    def generate_version_manifest(self, app: Dict, version: Dict, package_id: str, calculate_hash: bool = False) -> Dict:
        """Generate Winget version manifest"""
        download_url = self.get_windows_download_url(version)
        
        if not download_url:
            raise ValueError(f"No Windows download URL found for {app['name']}")
        
        installer_type = self.determine_installer_type(download_url)
        
        # Calculate file hash if requested
        installer_sha256 = None
        if calculate_hash:
            installer_sha256 = self.get_file_sha256(download_url)
        
        manifest = {
            'PackageIdentifier': package_id,
            'PackageVersion': version['version'],
            'ManifestType': 'version',
            'ManifestVersion': '1.4.0',
            'Installers': [
                {
                    'Architecture': 'x64',
                    'InstallerType': installer_type,
                    'InstallerUrl': download_url,
                    'InstallerSwitches': {
                        'Silent': '/S' if installer_type == 'exe' else None,
                        'SilentWithProgress': '/S' if installer_type == 'exe' else None
                    }
                }
            ]
        }
        
        # Add hash if calculated
        if installer_sha256:
            manifest['Installers'][0]['InstallerSha256'] = installer_sha256
        
        # Clean up None values
        if manifest['Installers'][0]['InstallerSwitches']['Silent'] is None:
            del manifest['Installers'][0]['InstallerSwitches']
        
        return manifest
    
    def generate_default_locale_manifest(self, app: Dict, package_id: str) -> Dict:
        """Generate Winget default locale manifest"""
        return {
            'PackageIdentifier': package_id,
            'PackageVersion': app.get('version', '1.0.0'),
            'PackageLocale': 'en-US',
            'ManifestType': 'defaultLocale',
            'ManifestVersion': '1.4.0',
            'Publisher': 'OpenLyst',
            'PackageName': app['name'],
            'License': 'Open Source',
            'ShortDescription': app.get('subtitle', app['name']),
            'Description': app.get('localizedDescription', app.get('subtitle', app['name'])),
            'PackageUrl': 'https://openlyst.ink',
            'Tags': ['opensource', 'free', 'openlyst']
        }
    
    def generate_installer_manifest(self, app: Dict, package_id: str) -> Dict:
        """Generate Winget installer manifest"""
        return {
            'PackageIdentifier': package_id,
            'PackageVersion': app.get('version', '1.0.0'),
            'ManifestType': 'installer',
            'ManifestVersion': '1.4.0'
        }
    
    def create_manifest_directory(self, package_id: str, version: str) -> Path:
        """Create directory structure for manifest files"""
        # Winget uses Publisher/PackageName/Version structure
        parts = package_id.split('.')
        publisher = parts[0] if len(parts) > 1 else 'OpenLyst'
        package_name = '.'.join(parts[1:]) if len(parts) > 1 else parts[0]
        
        manifest_dir = self.manifests_dir / publisher / package_name / version
        manifest_dir.mkdir(parents=True, exist_ok=True)
        
        return manifest_dir
    
    def generate_manifests(self, app: Dict, versions: List[Dict], calculate_hash: bool = False) -> bool:
        """Generate all manifest files for an app"""
        if not versions:
            logger.warning(f"No versions found for app {app.get('name', 'Unknown')}")
            return False
        
        # Use the latest version
        latest_version = versions[0]
        
        # Check if this app supports Windows platform
        app_platforms = latest_version.get('platforms', [])
        if 'Windows' not in app_platforms:
            logger.info(f"App {app.get('name', 'Unknown')} does not support Windows platform")
            return False
        
        try:
            package_id = self.sanitize_package_id(app['name'])
            version_str = latest_version['version']
            
            # Create manifest directory
            manifest_dir = self.create_manifest_directory(package_id, version_str)
            
            # Generate version manifest
            version_manifest = self.generate_version_manifest(app, latest_version, package_id, calculate_hash)
            
            # Generate default locale manifest
            app_with_version = {**app, 'version': version_str}
            default_locale_manifest = self.generate_default_locale_manifest(app_with_version, package_id)
            
            # Generate installer manifest
            installer_manifest = self.generate_installer_manifest(app_with_version, package_id)
            
            # Write manifest files
            with open(manifest_dir / f"{package_id}.installer.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(installer_manifest, f, default_flow_style=False, sort_keys=False)
            
            with open(manifest_dir / f"{package_id}.locale.en-US.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(default_locale_manifest, f, default_flow_style=False, sort_keys=False)
            
            with open(manifest_dir / f"{package_id}.yaml", 'w', encoding='utf-8') as f:
                yaml.dump(version_manifest, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Generated Winget manifests for {app['name']} in {manifest_dir}")
            return True
            
        except ValueError as e:
            logger.warning(f"Skipping {app.get('name', 'Unknown')}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to generate manifests for {app.get('name', 'Unknown')}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Build Winget repository from OpenLyst API')
    parser.add_argument('--output-dir', type=str, default='winget-repo',
                       help='Output directory for Winget repository')
    parser.add_argument('--calculate-hash', action='store_true',
                       help='Calculate SHA256 hashes for installers (slower but required for Winget)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    output_dir = Path(args.output_dir)
    client = OpenLystClient()
    generator = WingetManifestGenerator(output_dir)
    
    logger.info(f"Building Winget repository for Windows platform in {output_dir}")
    
    # Fetch Windows apps
    apps = client.get_all_apps(platform="Windows")
    if not apps:
        logger.error("No Windows apps found or failed to fetch apps")
        return 1
    
    logger.info(f"Found {len(apps)} Windows apps")
    
    # Generate manifests
    generated_count = 0
    failed_count = 0
    
    for app in apps:
        slug = app.get('slug')
        if not slug:
            logger.warning(f"No slug found for app: {app}")
            failed_count += 1
            continue
        
        # Get versions for this app
        versions = client.get_app_versions(slug)
        
        if generator.generate_manifests(app, versions, args.calculate_hash):
            generated_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Manifest generation complete: {generated_count} successful, {failed_count} failed")
    
    # Generate repository info file
    repo_info = {
        "name": "OpenLyst Winget Repository",
        "description": "Winget manifest files for Windows applications from OpenLyst",
        "homepage": "https://openlyst.ink",
        "generated_at": datetime.now().isoformat() + "Z",
        "manifest_count": generated_count
    }
    
    with open(output_dir / "repo-info.json", 'w', encoding='utf-8') as f:
        json.dump(repo_info, f, indent=2)
    
    logger.info(f"Generated repository info: {output_dir / 'repo-info.json'}")
    
    # Only exit with error if NO manifests were generated
    if generated_count == 0:
        logger.error("No manifests were generated - this indicates a serious problem")
        return 1
    elif failed_count > 0:
        logger.warning(f"{failed_count} apps failed to generate manifests, but {generated_count} succeeded")
        return 0
    
    return 0


if __name__ == "__main__":
    exit(main())