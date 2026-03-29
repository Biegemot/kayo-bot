import os
import sys
import subprocess
import logging
import json
import urllib.request
import urllib.error
import tempfile
import shutil
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class AutoUpdater:
    def __init__(self, repo_owner: str = "Biegemot", repo_name: str = "kayo-bot"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
    def get_current_version(self) -> str:
        """Get current version from git tags."""
        try:
            # Run git describe --tags --abbrev=0
            version = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], 
                                              stderr=subprocess.DEVNULL,
                                              universal_newlines=True).strip()
            return version
        except Exception as e:
            logger.debug(f"Could not get version from git: {e}")
            return "dev"
    
    def get_latest_release_info(self) -> Optional[dict]:
        """Fetch latest release info from GitHub API."""
        try:
            req = urllib.request.Request(
                self.github_api_url,
                headers={'User-Agent': 'KayoBot-AutoUpdater'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return data
                else:
                    logger.warning(f"GitHub API returned status {response.status}")
                    return None
        except Exception as e:
            logger.warning(f"Failed to fetch latest release info: {e}")
            return None
    
    def get_asset_name_for_version(self, version: str) -> str:
        """Determine the asset name for the given version."""
        # Check if we're running as a frozen executable (e.g., PyInstaller)
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            if sys.platform.startswith('win'):
                return f"kayo-bot-{version}.exe"
            elif sys.platform.startswith('darwin'):
                return f"kayo-bot-{version}-macos"
            else:
                return f"kayo-bot-{version}-linux"
        else:
            # Running as script - no asset to download for source
            return None
    
    def download_and_apply_update(self, asset_name: str, download_url: str) -> bool:
        """Download the update asset and apply it."""
        try:
            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                asset_path = os.path.join(temp_dir, asset_name)
                
                # Download the asset
                logger.info(f"Downloading update from {download_url}")
                req = urllib.request.Request(
                    download_url,
                    headers={'User-Agent': 'KayoBot-AutoUpdater'}
                )
                with urllib.request.urlopen(req, timeout=30) as response, \
                     open(asset_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                
                logger.info(f"Download completed: {asset_path}")
                
                # Replace current executable
                current_executable = sys.executable
                logger.info(f"Current executable: {current_executable}")
                
                # Backup current executable (optional)
                backup_path = current_executable + ".backup"
                if os.path.exists(current_executable):
                    shutil.move(current_executable, backup_path)
                    logger.info(f"Backed up current executable to {backup_path}")
                
                # Move new executable to current position
                shutil.move(asset_path, current_executable)
                logger.info(f"Updated executable moved to {current_executable}")
                
                # Make executable (on Unix-like systems)
                if not sys.platform.startswith('win'):
                    os.chmod(current_executable, 0o755)
                
                # Restart the bot
                logger.info("Restarting bot with updated version...")
                os.execv(current_executable, sys.argv)
                
        except Exception as e:
            logger.error(f"Failed to apply update: {e}")
            return False
        
        return True
    
    def check_and_apply_update(self) -> bool:
        """Check for updates and apply if available. Returns True if update was applied."""
        try:
            current_version = self.get_current_version()
            logger.info(f"Current version: {current_version}")
            
            if current_version == "dev":
                logger.info("Running in development mode, skipping update check")
                return False
            
            release_info = self.get_latest_release_info()
            if not release_info:
                logger.warning("Could not fetch release info")
                return False
            
            latest_tag = release_info.get('tag_name', '').lstrip('v')
            logger.info(f"Latest release tag: {latest_tag}")
            
            # Compare versions (simple string comparison, assumes semantic versioning)
            if self._is_newer_version(latest_tag, current_version):
                logger.info(f"Newer version available: {latest_tag}")
                
                # Find appropriate asset
                asset_name = self.get_asset_name_for_version(latest_tag)
                if not asset_name:
                    logger.info("No asset needed for current platform (running as script)")
                    return False
                
                # Look for the asset in the release
                assets = release_info.get('assets', [])
                download_url = None
                for asset in assets:
                    if asset.get('name') == asset_name:
                        download_url = asset.get('browser_download_url')
                        break
                
                if not download_url:
                    logger.warning(f"Asset {asset_name} not found in release")
                    return False
                
                logger.info(f"Found update asset: {asset_name}")
                return self.download_and_apply_update(asset_name, download_url)
            else:
                logger.info("Current version is up to date")
                return False
                
        except Exception as e:
            logger.error(f"Error during update check: {e}")
            return False
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings. Returns True if latest > current."""
        try:
            # Simple version comparison - split by dots and compare numerically
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except Exception:
            # Fallback to string comparison
            return latest > current

def setup_auto_update(application) -> None:
    """Setup auto-update to run on bot startup."""
    try:
        updater = AutoUpdater()
        # Check for updates (non-blocking, log errors)
        if updater.check_and_apply_update():
            # If update was applied, the bot would have restarted already
            # This line won't be reached if update succeeded
            pass
    except Exception as e:
        logger.error(f"Failed to setup auto-update: {e}")