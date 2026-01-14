#!/usr/bin/env python3
"""
OpenLyst to Homebrew Tap Builder

This script fetches apps from the OpenLyst API and generates Homebrew formulae
for macOS and Linux applications. The formulae are created in the Formula/ directory
following Homebrew tap conventions.
"""

import os
import json
import requests
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
            'User-Agent': 'Openlyst-Homebrew-Builder/1.0'
        })
    
    def get_all_apps(self, platform: str = "macOS", lang: str = "en") -> List[Dict]:
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


class HomebrewFormulaGenerator:
    """Generator for Homebrew formulae from OpenLyst app data"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.formula_dir = output_dir / "Formula"
        self.formula_dir.mkdir(parents=True, exist_ok=True)
    
    def sanitize_class_name(self, name: str) -> str:
        """Convert app name to valid Ruby class name for Homebrew formula"""
        # Remove special characters and capitalize words
        sanitized = re.sub(r'[^a-zA-Z0-9]', '', name.title())
        # Ensure it starts with a letter
        if not sanitized[0].isalpha():
            sanitized = f"App{sanitized}"
        return sanitized
    
    def get_download_url_for_platform(self, version: Dict, platform: str) -> Optional[str]:
        """Extract appropriate download URL for the specified platform from version data"""
        downloads = version.get('downloads', {})
        platform_downloads = downloads.get(platform, {})
        
        if not platform_downloads:
            return None
        
        # Priority order for different package types based on platform
        if platform == "macOS":
            # Prefer universal, then arm64, then x86_64
            for arch in ['universal', 'arm64', 'x86_64']:
                if arch in platform_downloads and platform_downloads[arch]:
                    return platform_downloads[arch]
        
        elif platform == "Linux":
            # Prefer AppImage, then zip, then deb, then rpm
            for package_type in ['appimage', 'zip', 'deb', 'rpm']:
                if package_type in platform_downloads:
                    pkg_data = platform_downloads[package_type]
                    # Check for x86_64 architecture first
                    if isinstance(pkg_data, dict):
                        for arch in ['x86_64', 'arm64']:
                            if arch in pkg_data and pkg_data[arch]:
                                return pkg_data[arch]
                    elif isinstance(pkg_data, str) and pkg_data:
                        return pkg_data
        
        elif platform == "Windows":
            # Prefer zip, then exe, then msi
            for package_type in ['zip', 'exe', 'msi']:
                if package_type in platform_downloads:
                    pkg_data = platform_downloads[package_type]
                    if isinstance(pkg_data, dict):
                        for arch in ['x86_64', 'arm64']:
                            if arch in pkg_data and pkg_data[arch]:
                                return pkg_data[arch]
                    elif isinstance(pkg_data, str) and pkg_data:
                        return pkg_data
        
        # Fallback: try to find any URL in the platform downloads
        for key, value in platform_downloads.items():
            if isinstance(value, dict):
                for arch_key, arch_value in value.items():
                    if isinstance(arch_value, str) and arch_value.startswith('http'):
                        return arch_value
            elif isinstance(value, str) and value.startswith('http'):
                return value
        
        return None
    
    def get_download_url_sha256(self, url: str) -> Optional[str]:
        """Calculate SHA256 hash of download file"""
        try:
            logger.info(f"Calculating SHA256 for {url}")
            response = requests.head(url, timeout=30)
            if response.status_code != 200:
                # Try GET if HEAD fails
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return hashlib.sha256(response.content).hexdigest()
            else:
                # For HEAD request, we need to download to get hash
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return hashlib.sha256(response.content).hexdigest()
            return None
        except Exception as e:
            logger.warning(f"Failed to calculate SHA256 for {url}: {e}")
            return None
        """Calculate SHA256 hash of download file"""
        try:
            logger.info(f"Calculating SHA256 for {url}")
            response = requests.head(url, timeout=30)
            if response.status_code != 200:
                # Try GET if HEAD fails
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return hashlib.sha256(response.content).hexdigest()
            else:
                # For HEAD request, we need to download to get hash
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    return hashlib.sha256(response.content).hexdigest()
            return None
        except Exception as e:
            logger.warning(f"Failed to calculate SHA256 for {url}: {e}")
            return None
    
    def generate_formula_content(self, app: Dict, version: Dict, platform: str, calculate_sha256: bool = False) -> str:
        """Generate Homebrew formula content for an app version"""
        class_name = self.sanitize_class_name(app['name'])
        download_url = self.get_download_url_for_platform(version, platform)
        
        if not download_url:
            raise ValueError(f"No download URL found for {app['name']} on {platform}")
        
        # Extract file extension to determine installation method
        url_path = urlparse(download_url).path
        file_extension = Path(url_path).suffix.lower()
        
        # Calculate SHA256 hash if requested
        if calculate_sha256:
            try:
                sha256_hash = self.get_download_url_sha256(download_url)
                sha256_line = f'  sha256 "{sha256_hash}"'
            except Exception as e:
                logger.warning(f"Failed to calculate SHA256 for {download_url}: {e}")
                sha256_line = '  # sha256 "REPLACE_WITH_ACTUAL_SHA256"'
        else:
            sha256_line = '  # sha256 "REPLACE_WITH_ACTUAL_SHA256"'
        
        # Determine installation method based on file type
        if file_extension in ['.dmg', '.pkg']:
            install_method = self.generate_cask_install(app, version)
            formula_type = "cask"
        elif file_extension in ['.zip', '.tar.gz', '.tgz']:
            install_method = self.generate_archive_install(app, version)
            formula_type = "formula"
        elif file_extension in ['.app']:
            install_method = self.generate_app_install(app, version)
            formula_type = "cask"
        else:
            install_method = self.generate_generic_install(app, version)
            formula_type = "formula"
        
        homepage = app.get('website', 'https://openlyst.ink')
        desc = app.get('subtitle', app.get('name', '')).replace('"', '\\"')
        
        if formula_type == "cask":
            formula_content = f'''cask "{class_name.lower()}" do
  version "{version['version']}"
{sha256_line}

  url "{download_url}"
  name "{app['name']}"
  desc "{desc}"
  homepage "{homepage}"

  livecheck do
    skip "No version check available"
  end

{install_method}
end
'''
        else:
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
    
    def generate_cask_install(self, app: Dict, version: Dict) -> str:
        """Generate installation instructions for cask-type applications"""
        app_name = app['name']
        return f'''  app "{app_name}.app"
  
  zap trash: [
    "~/Library/Preferences/com.{app['bundleIdentifier']}.plist",
    "~/Library/Application Support/{app_name}",
  ]'''
    
    def generate_archive_install(self, app: Dict, version: Dict) -> str:
        """Generate installation instructions for archive-type applications"""
        return f'''    # Extract and install archive
    prefix.install Dir["*"]'''
    
    def generate_app_install(self, app: Dict, version: Dict) -> str:
        """Generate installation instructions for .app bundles"""
        app_name = app['name']
        return f'''  app "{app_name}.app"'''
    
    def generate_generic_install(self, app: Dict, version: Dict) -> str:
        """Generate generic installation instructions"""
        return f'''    # Generic installation
    prefix.install Dir["*"]'''
    
    def generate_formula(self, app: Dict, versions: List[Dict], platform: str, calculate_sha256: bool = False) -> bool:
        """Generate Homebrew formula for an app"""
        if not versions:
            logger.warning(f"No versions found for app {app.get('name', 'Unknown')}")
            return False
        
        # Use the latest version
        latest_version = versions[0]
        
        # Check if this app supports the target platform
        app_platforms = latest_version.get('platforms', [])
        if platform not in app_platforms:
            logger.info(f"App {app.get('name', 'Unknown')} does not support {platform} platform")
            return False
        
        try:
            formula_content = self.generate_formula_content(app, latest_version, platform, calculate_sha256)
            
            # Generate filename
            class_name = self.sanitize_class_name(app['name'])
            filename = f"{class_name.lower()}.rb"
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


def main():
    parser = argparse.ArgumentParser(description='Build Homebrew tap from OpenLyst API')
    parser.add_argument('--output-dir', type=str, default='homebrew-tap',
                       help='Output directory for Homebrew tap')
    parser.add_argument('--platform', type=str, default='macOS',
                       choices=['macOS', 'Linux'],
                       help='Platform to fetch apps for')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--calculate-sha256', action='store_true',
                       help='Calculate SHA256 hashes for download files (slower but more secure)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    output_dir = Path(args.output_dir)
    client = OpenLystClient()
    generator = HomebrewFormulaGenerator(output_dir)
    
    logger.info(f"Building Homebrew tap for {args.platform} platform in {output_dir}")
    
    # Fetch apps
    apps = client.get_all_apps(platform=args.platform)
    if not apps:
        logger.error("No apps found or failed to fetch apps")
        return 1
    
    logger.info(f"Found {len(apps)} apps for {args.platform}")
    
    # Generate formulae
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
        
        if generator.generate_formula(app, versions, args.platform, args.calculate_sha256):
            generated_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Formula generation complete: {generated_count} successful, {failed_count} failed")
    
    # Generate tap info file
    tap_info = {
        "name": "Openlyst Homebrew Tap",
        "description": f"Homebrew formulae for {args.platform} applications from OpenLyst",
        "homepage": "https://openlyst.ink",
        "generated_at": datetime.now().isoformat() + "Z",
        "platform": args.platform,
        "formulae_count": generated_count
    }
    
    with open(output_dir / "tap-info.json", 'w', encoding='utf-8') as f:
        json.dump(tap_info, f, indent=2)
    
    logger.info(f"Generated tap info: {output_dir / 'tap-info.json'}")
    
    # Only exit with error if NO formulae were generated
    if generated_count == 0:
        logger.error("No formulae were generated - this indicates a serious problem")
        return 1
    elif failed_count > 0:
        logger.warning(f"{failed_count} apps failed to generate formulae, but {generated_count} succeeded")
        return 0  # Success with warnings
    
    return 0


if __name__ == "__main__":
    exit(main())