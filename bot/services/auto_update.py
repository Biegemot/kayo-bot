"""
Auto-update module for Kayo Bot.
- Git mode (dev): pull latest from origin/main
- Frozen mode (.exe): download latest release from GitHub API
"""
import os
import sys
import logging
import threading
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import json

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com/repos/Biegemot/kayo-bot/releases/latest"
CHECK_INTERVAL_HOURS = 6


def get_current_version():
    """Get current version from version.txt."""
    search_paths = []

    if getattr(sys, 'frozen', False):
        # PyInstaller: check MEIPASS (temp extract dir) and exe directory
        if hasattr(sys, '_MEIPASS'):
            search_paths.append(Path(sys._MEIPASS) / 'version.txt')
        search_paths.append(Path(sys.executable).parent / 'version.txt')
    else:
        base = Path(__file__).parent.parent.parent
        search_paths.append(base / 'version.txt')

    for path in search_paths:
        if path.exists():
            try:
                return path.read_text(encoding='utf-8').strip()
            except Exception:
                continue
    return "0.0.0"


def version_tuple(v):
    """Convert version string to tuple for comparison."""
    try:
        return tuple(int(x) for x in v.split('.'))
    except Exception:
        return (0, 0, 0)


def get_latest_release_info():
    """Fetch latest release info from GitHub API."""
    try:
        req = Request(GITHUB_API, headers={'User-Agent': 'KayoBot-Updater'})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            tag = data.get('tag_name', '').lstrip('v')
            assets = data.get('assets', [])
            return tag, assets
    except (URLError, Exception) as e:
        logger.debug(f"Could not fetch release info: {e}")
        return None, []


def find_asset_for_platform(assets):
    """Find the correct asset for current platform."""
    if sys.platform == 'win32':
        suffix = '-win.exe'
    else:
        suffix = '-linux'

    for asset in assets:
        name = asset.get('name', '')
        if name.endswith(suffix):
            return asset.get('browser_download_url'), name
    return None, None


def download_file(url, dest_path):
    """Download a file from URL to destination."""
    req = Request(url, headers={'User-Agent': 'KayoBot-Updater'})
    with urlopen(req, timeout=120) as resp:
        with open(dest_path, 'wb') as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)


def check_and_apply_update(force=False):
    """
    Check for updates and apply if available.
    Returns (updated: bool, message: str).
    """
    current = get_current_version()

    # Git-based update (development mode)
    if not getattr(sys, 'frozen', False):
        return _git_update(current)

    # Frozen mode: GitHub API update
    return _frozen_update(current, force)


def _git_update(current):
    """Update using git (development mode)."""
    try:
        import subprocess

        # Check git available
        subprocess.check_output(['git', '--version'], stderr=subprocess.DEVNULL)

        # Fetch
        subprocess.check_call(['git', 'fetch', 'origin'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Compare
        local = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                        stderr=subprocess.DEVNULL).decode().strip()
        remote = subprocess.check_output(['git', 'rev-parse', 'origin/main'],
                                         stderr=subprocess.DEVNULL).decode().strip()

        if local == remote:
            return False, f"Актуальная версия: {current}"

        # Get changed files
        changed = subprocess.check_output(
            ['git', 'diff', '--name-only', 'HEAD', 'origin/main'],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        if not changed:
            return False, "Нет файлов для обновления"

        # Filter protected files
        files = [f.strip() for f in changed.split('\n') if f.strip()]
        protected = {'.env', 'bot/data'}
        to_update = [f for f in files if not any(f.startswith(p) for p in protected)]

        if not to_update:
            return False, "Все изменённые файлы защищены"

        # Apply updates
        base = Path(__file__).parent.parent.parent
        for fname in to_update:
            try:
                content = subprocess.check_output(
                    ['git', 'show', f'origin/main:{fname}'],
                    stderr=subprocess.DEVNULL
                )
                fpath = base / fname
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_bytes(content)
                logger.info(f"Updated: {fname}")
            except Exception as e:
                logger.warning(f"Failed to update {fname}: {e}")

        return True, "Обновление применено, перезапуск..."

    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "Git не найден, автообновление недоступно"


def _frozen_update(current, force=False):
    """Update from GitHub releases (frozen .exe mode)."""
    new_version, assets = get_latest_release_info()

    if not new_version:
        return False, "Не удалось проверить обновления (нет интернета?)"

    if not force and version_tuple(new_version) <= version_tuple(current):
        return False, f"Актуальная версия: v{current}"

    if version_tuple(new_version) <= version_tuple(current):
        return False, f"Установлена последняя версия: v{current}"

    download_url, asset_name = find_asset_for_platform(assets)
    if not download_url:
        return False, f"Нет сборки для {sys.platform} в релизе v{new_version}"

    # Download to temp file
    try:
        base = Path(sys.executable).parent
        exe_name = Path(sys.executable).name
        temp_path = base / f"{exe_name}.new"

        logger.info(f"Downloading v{new_version} from {download_url}...")
        download_file(download_url, str(temp_path))

        # On Windows, need to replace running exe
        old_path = base / exe_name
        backup_path = base / f"{exe_name}.old"

        # Remove old backup if exists
        if backup_path.exists():
            try:
                backup_path.unlink()
            except Exception:
                pass

        # Rename current -> backup, new -> current
        try:
            os.rename(str(old_path), str(backup_path))
            os.rename(str(temp_path), str(old_path))
        except Exception as e:
            # Rollback
            if backup_path.exists() and not old_path.exists():
                os.rename(str(backup_path), str(old_path))
            raise e

        return True, f"Обновлено до v{new_version}, перезапуск..."

    except Exception as e:
        logger.error(f"Update failed: {e}")
        return False, f"Ошибка обновления: {e}"


def restart_application():
    """Restart the current application."""
    os.execv(sys.executable, [sys.executable] + sys.argv)


class AutoUpdater:
    def __init__(self):
        self._timer = None
        self._start_periodic_check()

    def _start_periodic_check(self):
        self.check_and_apply_update()
        self._timer = threading.Timer(CHECK_INTERVAL_HOURS * 3600, self._periodic_check)
        self._timer.daemon = True
        self._timer.start()

    def _periodic_check(self):
        self.check_and_apply_update()
        self._start_periodic_check()

    def check_and_apply_update(self):
        updated, msg = check_and_apply_update()
        if updated:
            logger.info(msg)
            restart_application()
        return updated, msg


def setup_auto_update(application):
    """Setup auto-update to run on bot startup and periodically."""
    try:
        updater = AutoUpdater()
        application.bot_data['auto_updater'] = updater
        logger.info("Auto-update scheduler started")
    except Exception as e:
        logger.error(f"Failed to setup auto-update: {e}")
