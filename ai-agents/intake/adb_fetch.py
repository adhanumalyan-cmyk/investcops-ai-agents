"""
intake/adb_fetch.py — Direct ADB subprocess wrapper for INVESTCOPS AI.
"""

from __future__ import annotations

import hashlib
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("investcops.adb_fetch")


class ADBError(Exception):
    """Raised when an ADB command fails or the device is unreachable."""


class ADBFetcher:
    def __init__(self, adb_path: str = "adb", device_serial: Optional[str] = None):
        self.adb_path = adb_path
        self.device_serial = device_serial
        self._root_available: Optional[bool] = None

    # ------------------------------------------------------------------
    # Low-level command runner with UTF-8 + ignore errors
    # ------------------------------------------------------------------
    def _run(self, args: List[str], timeout: int = 30) -> str:
        cmd = [self.adb_path]
        if self.device_serial:
            cmd += ["-s", self.device_serial]
        cmd += args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                encoding='utf-8',      # Force UTF-8
                errors='ignore'        # Skip bad characters
            )
        except FileNotFoundError as e:
            raise ADBError(
                f"'{self.adb_path}' not found. Install Android platform-tools."
            ) from e
        except subprocess.TimeoutExpired as e:
            raise ADBError(f"ADB command timed out: {' '.join(args)}") from e

        if result.returncode != 0 and result.stderr:
            if "Permission Denial" in result.stderr:
                raise ADBError(f"Permission Denial: {result.stderr.strip()}")
            raise ADBError(f"ADB command failed: {' '.join(args)}\n{result.stderr.strip()}")

        return result.stdout or ""   # Always return string, never None

    # ------------------------------------------------------------------
    # Device info
    # ------------------------------------------------------------------
    def check_device_connected(self) -> bool:
        out = self._run(["devices"])
        lines = [l for l in out.splitlines()[1:] if l.strip()]
        return any("device" in line and "unauthorized" not in line for line in lines)

    def get_android_sdk(self) -> int:
        try:
            sdk = self._run(["shell", "getprop", "ro.build.version.sdk"]).strip()
            return int(sdk)
        except (ADBError, ValueError):
            return 0

    def is_root_available(self) -> bool:
        if self._root_available is not None:
            return self._root_available
        try:
            out = self._run(["shell", "su", "-c", "id"], timeout=10)
            self._root_available = "uid=0" in out
        except ADBError:
            self._root_available = False
        return self._root_available

    def get_device_info(self) -> Dict[str, str]:
        props = {}
        for key, prop in {
            "model": "ro.product.model",
            "manufacturer": "ro.product.manufacturer",
            "android_version": "ro.build.version.release",
            "sdk": "ro.build.version.sdk",
            "build_id": "ro.build.id",
            "serial": "ro.serialno",
        }.items():
            try:
                props[key] = self._run(["shell", "getprop", prop]).strip()
            except ADBError:
                props[key] = "unknown"
        props["fetched_at"] = datetime.utcnow().isoformat()
        return props

    # ------------------------------------------------------------------
    # Content provider queries
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_content_query(raw: str) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        if not raw:   # Guard against empty/None
            return rows
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("Row:"):
                continue
            body = re.sub(r"^Row:\s*\d+\s*", "", line)
            row: Dict[str, str] = {}
            for part in body.split(", "):
                if "=" in part:
                    k, _, v = part.partition("=")
                    row[k.strip()] = v.strip()
            if row:
                rows.append(row)
        return rows

    def _fetch_protected_content(self, uri: str, data_type: str) -> List[Dict[str, str]]:
        try:
            raw = self._run(["shell", "content", "query", "--uri", uri])
            if not raw.strip():
                return []
            return self._parse_content_query(raw)
        except ADBError as e:
            if "Permission Denial" not in str(e):
                logger.warning("ADB error fetching %s: %s", data_type, e)
                return []

        if self.is_root_available():
            try:
                logger.info("Root detected, retrying %s via su -c ...", data_type)
                raw = self._run(["shell", "su", "-c", f"content query --uri {uri}"])
                if not raw.strip():
                    return []
                return self._parse_content_query(raw)
            except ADBError as e:
                logger.warning("Root fetch also failed for %s: %s", data_type, e)
                return []

        logger.warning("%s: permission denied and no root available. Skipping.", data_type)
        return []

    def fetch_call_log(self) -> List[Dict[str, str]]:
        return self._fetch_protected_content("content://call_log/calls", "Call Logs")

    def fetch_contacts(self) -> List[Dict[str, str]]:
        return self._fetch_protected_content("content://contacts/phones", "Contacts")

    def fetch_sms(self) -> List[Dict[str, str]]:
        return self._fetch_protected_content("content://sms", "SMS")

    def fetch_notifications(self) -> List[Dict[str, str]]:
        try:
            raw = self._run(["shell", "dumpsys", "notification", "--noredact"], timeout=20)
            return [{"raw_notification_block": raw}] if raw.strip() else []
        except ADBError:
            return []

    # ------------------------------------------------------------------
    # Media pull with collision fix
    # ------------------------------------------------------------------
    def pull_media(self, dest_dir: Path, max_files: int = 500, scan_timeout: int = 120) -> List[Path]:
        dest_dir.mkdir(parents=True, exist_ok=True)

        extensions = [
            "*.jpg", "*.jpeg", "*.png", "*.gif", "*.webp", "*.bmp",
            "*.mp4", "*.mkv", "*.3gp", "*.mov", "*.avi", "*.wmv",
        ]
        name_clauses = " -o ".join(f"-iname '{ext}'" for ext in extensions)

        find_cmd = (
            f"find /sdcard/ -type f \\( {name_clauses} \\) "
            f"-not -path '*/Android/data/*' -not -path '*/Android/obb/*' "
            f"2>/dev/null | head -n {max_files}"
        )

        logger.info("Scanning internal storage for media files...")
        try:
            output = self._run(["shell", find_cmd], timeout=scan_timeout)
        except ADBError as e:
            logger.warning("Media scan failed: %s", e)
            return []

        remote_paths = [line.strip() for line in output.splitlines() if line.strip()]
        logger.info("Found %d media files, pulling...", len(remote_paths))

        before_pull = {f for f in dest_dir.rglob("*") if f.is_file()}

        for remote_path in remote_paths:
            relative = remote_path.replace("/sdcard/", "").replace("/", "_")
            dest_path = dest_dir / relative
            try:
                subprocess.run(
                    [self.adb_path]
                    + (["-s", self.device_serial] if self.device_serial else [])
                    + ["pull", remote_path, str(dest_path)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='utf-8',
                    errors='ignore'
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("Failed to pull: %s", remote_path)
                continue

        after_pull = {f for f in dest_dir.rglob("*") if f.is_file()}
        pulled = sorted(after_pull - before_pull, key=lambda p: p.name)

        logger.info("Successfully pulled %d new files.", len(pulled))
        return pulled


# Helpers
def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()