"""
USB Field Extractor - One-Click Logical Extraction.

Connects to an Android device over ADB and pulls logical evidence
(chats, photos, contacts, browser data). Falls back to a deterministic
MOCK demo when ADB or a device is unavailable so the frontend always
gets a valid response.

Response shapes match the React frontend contract exactly:
  DeviceInfo    {connected, mock, reason?, device_id?, model?, android?, adb_available?}
  ExtractResult {success, mock, out_dir, files: [{path, size, sha256, desc?}], log, manifest?, device?}
"""

import hashlib
import json
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

ADB = shutil.which("adb") or "adb"
BACKUP_DIR = Path(__file__).resolve().parent.parent.parent / "field_backups"
BACKUP_DIR.mkdir(exist_ok=True)

_SAFE_CASE_RE = re.compile(r"[^A-Za-z0-9_-]")
_SAFE_DEVICE_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


def sanitize_case_id(case_id) -> str:
    """Sanitize a case id for safe use in filesystem paths. Never trust caller input."""
    cleaned = _SAFE_CASE_RE.sub("_", str(case_id)).strip("_")[:64]
    return cleaned or "CASE"


def is_safe_device_id(device_id: str) -> bool:
    """Reject adb device ids containing shell metacharacters or path separators."""
    return bool(_SAFE_DEVICE_RE.match(device_id or ""))


def run(args, timeout=30):
    """Run a command as an argument list (no shell) and return combined output."""
    try:
        out = subprocess.check_output(args, stderr=subprocess.STDOUT, timeout=timeout, text=True)
        return out.strip()
    except subprocess.CalledProcessError as e:
        return e.output or ""
    except Exception as e:
        return str(e)


def is_adb_available() -> bool:
    return shutil.which("adb") is not None


def device_info() -> dict:
    """Get connected device info (mock when ADB unavailable)."""
    if not is_adb_available():
        return {"connected": False, "mock": True, "reason": "ADB not installed - using MOCK demo"}
    out = run([ADB, "devices"])
    lines = [line for line in out.splitlines() if "\tdevice" in line]
    if not lines:
        return {"connected": False, "mock": False, "reason": "No device connected. Enable USB Debugging & Authorize."}
    dev = lines[0].split()[0]
    if not is_safe_device_id(dev):
        return {"connected": False, "mock": False, "reason": "Unrecognized device id."}
    model = run([ADB, "-s", dev, "shell", "getprop", "ro.product.model"])
    android = run([ADB, "-s", dev, "shell", "getprop", "ro.build.version.release"])
    return {"connected": True, "device_id": dev, "model": model or "Android Device", "android": android or "?", "mock": False}


def logical_extract(case_id: str = "KPC-2026-8941") -> dict:
    """Perform a logical (no-root) extraction; MOCK demo when no device connected."""
    case_id = sanitize_case_id(case_id)
    info = device_info()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = BACKUP_DIR.resolve()
    out_dir = (root / f"{case_id}_{ts}").resolve()
    try:
        out_dir.relative_to(root)
    except ValueError:
        out_dir = root / f"case_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log = []

    if not info.get("connected"):
        log.append(f"[{datetime.now().strftime('%H:%M:%S')}] MOCK MODE - No device, generating demo data...")
        time.sleep(0.5)
        mock_files = [
            ("WhatsApp/chat_export.txt", "WhatsApp chats - 342 messages"),
            ("DCIM/Camera/photo_001.jpg", "Photo with EXIF GPS"),
            ("Contacts/contacts.vcf", "127 contacts"),
            ("Browser/history.json", "89 URLs"),
            ("CallLogs/calls.json", "54 calls"),
            ("SMS/sms.json", "210 SMS"),
        ]
        extracted = []
        for rel, desc in mock_files:
            p = out_dir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = f"MOCK {desc} for {case_id} at {ts}\n" + "X" * 200
            p.write_text(data)
            h = hashlib.sha256(data.encode()).hexdigest()
            extracted.append({"path": rel, "size": len(data), "sha256": h, "desc": desc})
            log.append(f"  OK {rel} ({len(data)} bytes) sha256:{h[:16]}...")
            time.sleep(0.2)
        manifest = {
            "case_id": case_id,
            "timestamp": ts,
            "device": info,
            "files": extracted,
            "mock": True,
            "hash_chain": hashlib.sha256(json.dumps(extracted).encode()).hexdigest(),
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        log.append(f"[{datetime.now().strftime('%H:%M:%S')}] MOCK extraction done: {len(extracted)} files -> {out_dir}")
        return {"success": True, "mock": True, "out_dir": str(out_dir), "files": extracted, "log": log, "manifest": manifest, "device": info}

    dev = info["device_id"]
    log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Device {dev} ({info['model']} Android {info['android']}) connected")
    extracted = []

    pulls = [
        ("sdcard/DCIM/Camera", "DCIM"),
        ("sdcard/Pictures", "Pictures"),
        ("sdcard/Download", "Download"),
        ("sdcard/WhatsApp/Databases/msgstore.db", "WhatsApp/msgstore.db"),
        ("sdcard/WhatsApp/Media", "WhatsApp/Media"),
    ]
    for remote, local in pulls:
        log.append(f"  -> Pulling {remote} ...")
        out = run([ADB, "-s", dev, "pull", f"/{remote}", str(out_dir / local)], timeout=60)
        log.append(f"    {out[:120]}")
        lp = out_dir / local
        if lp.exists():
            for f in lp.rglob("*"):
                if f.is_file():
                    rel = f.relative_to(out_dir).as_posix()
                    h = hashlib.sha256(f.read_bytes()).hexdigest()
                    extracted.append({"path": rel, "size": f.stat().st_size, "sha256": h})

    log.append("  -> ADB backup (contacts/sms) ...")
    ab = out_dir / "backup.ab"
    run([ADB, "-s", dev, "backup", "-f", str(ab), "-apk", "-shared", "-all"], timeout=30)
    if ab.exists():
        h = hashlib.sha256(ab.read_bytes()).hexdigest()
        extracted.append({"path": "backup.ab", "size": ab.stat().st_size, "sha256": h})

    manifest = {
        "case_id": case_id,
        "timestamp": ts,
        "device": info,
        "files": extracted,
        "mock": False,
        "hash_chain": hashlib.sha256(json.dumps(extracted).encode()).hexdigest(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Extraction done: {len(extracted)} files -> {out_dir}")
    return {"success": True, "mock": False, "out_dir": str(out_dir), "files": extracted, "log": log, "manifest": manifest, "device": info}