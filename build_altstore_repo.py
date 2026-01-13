#!/usr/bin/env python3
"""
OpenLyst to AltStore Repository Builder

This script fetches apps from the OpenLyst API and generates a static AltStore
repository JSON file. The repository URL structure remains constant across builds.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from urllib.parse import urljoin

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
            'User-Agent': 'Openlyst-AltStore-Builder/1.0'
        })
    
    def get_all_apps(self, platform: str = "iOS", lang: str = "en") -> List[Dict]:
        """Fetch all iOS apps from OpenLyst"""
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
                if versions and logger.level == logging.DEBUG:
                    logger.debug(f"Sample version structure: {str(versions[0])[:200]}")
                return versions if isinstance(versions, list) else []
            return []
                
        except requests.RequestException as e:
            logger.error(f"Failed to fetch versions for {slug}: {e}")
            return []


class AltStoreRepoBuilder:
    """Builder for AltStore repository JSON"""
    
    def __init__(self, base_repo_url: str = "https://raw.githubusercontent.com/httpanimations/Openlyst-more-builds/main/repo"):
        """
        Initialize the builder
        
        Args:
            base_repo_url: Static base URL for the repository (GitHub Raw Content URL - never changes)
        """
        self.base_repo_url = base_repo_url
        self.client = OpenLystClient()
    
    def extract_ipa_url(self, version: Dict) -> Optional[str]:
        """Extract iOS IPA download URL from version data"""
        if not isinstance(version, dict):
            return None
        
        # Primary: Check downloads.iOS (direct string URL)
        downloads = version.get('downloads')
        if isinstance(downloads, dict):
            ios_download = downloads.get('iOS')
            # iOS download can be a string URL or empty string
            if isinstance(ios_download, str) and ios_download.strip():
                return ios_download.strip()
        
        # Fallback: Check platformInstall.iOS (might contain URL or text)
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
    
    def get_file_size(self, url: str) -> Optional[int]:
        """Get file size from URL without downloading"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if 'content-length' in response.headers:
                return int(response.headers['content-length'])
        except Exception as e:
            logger.warning(f"Could not determine file size for {url}: {e}")
        return None
    
    def build_app_entry(self, app: Dict, slug: str) -> Optional[Dict]:
        """Build an AltStore app entry from OpenLyst app data"""
        try:
            # Get latest versions
            versions = self.client.get_app_versions(slug)
            if not versions:
                logger.warning(f"No versions found for app {slug}")
                return None
            
            # Ensure versions is a list
            if not isinstance(versions, list):
                logger.warning(f"Versions for {slug} is not a list: {type(versions)}")
                return None
            
            # Build version entries (AltStore expects newest first)
            altstore_versions = []
            for version_data in versions[:10]:  # Limit to last 10 versions
                if not isinstance(version_data, dict):
                    logger.warning(f"Version entry for {slug} is not a dict: {type(version_data)}")
                    continue
                
                ipa_url = self.extract_ipa_url(version_data)
                
                if not ipa_url:
                    logger.debug(f"No IPA URL found for {slug} version {version_data.get('version')}")
                    continue
                
                size = self.get_file_size(ipa_url)
                
                altstore_version = {
                    "version": str(version_data.get('version', '1.0')),
                    "buildVersion": str(version_data.get('buildVersion', '1')),
                    "date": str(version_data.get('date', datetime.now().isoformat())),
                    "downloadURL": ipa_url,
                }
                
                if size:
                    altstore_version['size'] = size
                
                # Add optional description
                description = version_data.get('localizedDescription')
                if description and isinstance(description, str):
                    altstore_version['localizedDescription'] = description
                
                altstore_versions.append(altstore_version)
            
            if not altstore_versions:
                logger.warning(f"No valid IPA versions found for app {slug}")
                return None
            
            # Build main app entry
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
            
            # Add optional fields
            if app.get('screenshots'):
                app_entry['screenshots'] = self._process_screenshots(app['screenshots'])
            
            return app_entry
        
        except Exception as e:
            logger.error(f"Error building app entry for {slug}: {e}", exc_info=True)
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
        """Process screenshots array, handling both simple URLs and complex objects"""
        result = []
        
        if isinstance(screenshots, list):
            for shot in screenshots:
                if isinstance(shot, str):
                    result.append(shot)
                elif isinstance(shot, dict):
                    if 'imageURL' in shot:
                        result.append(shot['imageURL'])
        
        return result[:10]  # Limit to 10 screenshots
    
    def build_repository(self, output_dir: str = "repo") -> bool:
        """Build the complete AltStore repository"""
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Fetch all apps
            logger.info("Fetching all iOS apps from OpenLyst...")
            apps = self.client.get_all_apps(platform="iOS")
            
            if not apps:
                logger.error("No apps fetched from OpenLyst")
                return False
            
            # Build app entries
            logger.info("Building AltStore app entries...")
            app_entries = []
            
            for app in apps:
                slug = app.get('slug')
                if not slug:
                    logger.warning(f"App missing slug: {app.get('name')}")
                    continue
                
                logger.info(f"Processing app: {slug}")
                app_entry = self.build_app_entry(app, slug)
                
                if app_entry:
                    app_entries.append(app_entry)
                else:
                    logger.warning(f"Skipped app {slug} - no valid versions")
            
            if not app_entries:
                logger.error("No valid app entries created")
                return False
            
            # Build repository structure
            repository = {
                "name": app.get('name', 'OpenLyst iOS Apps'),
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
            
            # Write repository JSON
            repo_file = os.path.join(output_dir, "apps.json")
            with open(repo_file, 'w', encoding='utf-8') as f:
                json.dump(repository, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Repository built successfully: {repo_file}")
            logger.info(f"Total apps: {len(app_entries)}")
            
            # Create index file pointing to apps.json
            index_file = os.path.join(output_dir, "index.json")
            index_data = {
                "repositoryURL": urljoin(self.base_repo_url, "apps.json"),
                "name": repository['name'],
                "subtitle": repository['subtitle'],
                "description": repository['description'],
                "generatedAt": datetime.now().isoformat()
            }
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
            logger.info(f"Index file created: {index_file}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error building repository: {e}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Build an AltStore repository from OpenLyst API'
    )
    parser.add_argument(
        '--output-dir',
        default='repo',
        help='Output directory for repository files (default: repo)'
    )
    parser.add_argument(
        '--repo-url',
        default='https://repo.openlyst.ink',
        help='Static base URL for the repository (default: https://repo.openlyst.ink)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting build with repo URL: {args.repo_url}")
    
    builder = AltStoreRepoBuilder(base_repo_url=args.repo_url)
    success = builder.build_repository(output_dir=args.output_dir)
    
    if success:
        logger.info("Build completed successfully!")
        return 0
    else:
        logger.error("Build failed!")
        return 1


if __name__ == "__main__":
    exit(main())
