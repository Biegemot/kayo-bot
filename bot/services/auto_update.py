import os
import sys
import subprocess
import logging
import threading

logger = logging.getLogger(__name__)

class AutoUpdater:
    def __init__(self, repo_owner: str = "Biegemot", repo_name: str = "kayo-bot"):
        # Parameters kept for compatibility but not used in this implementation
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self._timer = None
        self._start_periodic_check()

    def _start_periodic_check(self):
        # Check for updates immediately
        self.check_and_apply_update()
        # Schedule next check in 6 hours
        self._timer = threading.Timer(6 * 60 * 60, self._periodic_check)
        self._timer.daemon = True
        self._timer.start()

    def _periodic_check(self):
        self.check_and_apply_update()
        self._start_periodic_check()

    def stop_periodic_check(self):
        if self._timer:
            self._timer.cancel()

    def check_and_apply_update(self) -> bool:
        """Check for updates using git and apply if available.
        Returns True if update was applied (and bot restarted), False otherwise.
        """
        try:
            # Verify we are in a git repository
            root = subprocess.check_output(
                ['git', 'rev-parse', '--show-toplevel'],
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
        except subprocess.CalledProcessError:
            logger.warning("Not in a git repository, skipping update check")
            return False

        try:
            # Fetch latest from origin
            subprocess.check_call(
                ['git', 'fetch', 'origin'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to fetch from origin: {e}")
            return False

        try:
            # Get current commit hash (HEAD)
            local_hash = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
            # Get remote commit hash (origin/main)
            remote_hash = subprocess.check_output(
                ['git', 'rev-parse', 'origin/main'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get commit hashes: {e}")
            return False

        if local_hash == remote_hash:
            logger.info("Local repository is up to date with origin/main")
            return False

        # Try to get remote version for logging
        try:
            remote_version = subprocess.check_output(
                ['git', 'show', 'origin/main:version.txt'],
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
            logger.info(f"Update available: remote version {remote_version}")
        except Exception:
            logger.info("Local repository is behind origin/main, checking for file changes...")

        # Get list of changed files between HEAD and origin/main
        try:
            changed_files = subprocess.check_output(
                ['git', 'diff', '--name-only', 'HEAD', 'origin/main'],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            ).strip()
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get changed files: {e}")
            return False

        if not changed_files:
            logger.info("No changed files found.")
            return False

        changed_files_list = [f.strip() for f in changed_files.split('\n') if f.strip()]

        # Filter out excluded files: .env and anything under bot/data/
        excluded_files = []
        filtered_files = []
        for f in changed_files_list:
            if f == '.env' or f.startswith('bot/data/'):
                excluded_files.append(f)
            else:
                filtered_files.append(f)

        if excluded_files:
            logger.info(f"Excluded files from update: {excluded_files}")

        if not filtered_files:
            logger.info("No files to update after excluding .env and bot/data/")
            return False

        logger.info(f"Files to update: {filtered_files}")

        # Update each file
        for file in filtered_files:
            try:
                # Get file content from origin/main
                content = subprocess.check_output(
                    ['git', 'show', f'origin/main:{file}'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to get file {file} from origin/main: {e}")
                continue  # Skip this file and continue with others

            # Ensure directory exists
            dirname = os.path.dirname(file)
            if dirname and not os.path.exists(dirname):
                try:
                    os.makedirs(dirname)
                except OSError as e:
                    logger.error(f"Failed to create directory {dirname}: {e}")
                    return False

            # Write the content
            try:
                with open(file, 'wb') as f:
                    f.write(content)
                logger.info(f"Updated file: {file}")
            except Exception as e:
                logger.error(f"Failed to write file {file}: {e}")
                return False

        # If we updated any files, restart the bot
        logger.info("Update applied. Restarting bot...")
        try:
            os.execv(sys.executable, sys.argv)
        except Exception as e:
            logger.error(f"Failed to restart bot: {e}")
            return False

        # Note: os.execv does not return on success
        # If we reach here, execv failed (should not happen because we return False in except)
        return False

def setup_auto_update(application) -> None:
    """Setup auto-update to run on bot startup and periodically."""
    try:
        updater = AutoUpdater()
        # The updater starts a periodic thread in __init__
        # If update is applied, the bot restarts via os.execv
        # If not, the thread continues to check every 6 hours
        logger.info("Auto-update scheduler started")
    except Exception as e:
        logger.error(f"Failed to setup auto-update: {e}")