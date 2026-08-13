"""
Evidence processing pipeline: turn raw files into analyzable text/artifacts.

Dispatch by MIME type. Each processor is a real implementation; modules that
require optional tooling (whisper, OCR, video tools) fail with a clear
message instead of returning fake output.
"""

import json
import os
import re
import zipfile
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ProcessingError, UnsupportedEvidenceError
from app.core.logging import get_logger
from app.models.models import Evidence, EvidenceProcessing

logger = get_logger("processing")


class EvidenceProcessor:
    """Dispatches a stored evidence file to the right processor."""

    def process(self, db: Session, evidence: Evidence, file_path: str) -> EvidenceProcessing:
        rec = EvidenceProcessing(evidence_id=evidence.evidence_id, processor="")
        db.add(rec)
        db.flush()
        name = evidence.file_name.lower()
        try:
            output_text, output_json, processor = self._dispatch(evidence, file_path, name)
            rec.processor = processor
            rec.output_text = output_text
            rec.output_json = output_json
            rec.status = "COMPLETED"
            logger.info("Processed %s (%s): %d chars", evidence.evidence_id, processor, len(output_text))
        except Exception as exc:
            rec.status = "FAILED"
            rec.error_message = str(exc)
            rec.output_text = ""
            rec.output_json = {}
            logger.error("Processing failed for %s: %s", evidence.evidence_id, exc)
            raise ProcessingError(f"Evidence processing failed: {exc}") from exc
        return rec

    def _dispatch(self, evidence: Evidence, file_path: str, name: str):
        mime = evidence.mime_type
        if mime.startswith("text/") or name.endswith((".txt", ".json", ".csv", ".html", ".eml")):
            return extract_text_file(file_path, mime), {}, "text"
        if mime == "application/pdf" or name.endswith(".pdf"):
            return extract_pdf(file_path), {}, "pdf"
        if mime.startswith("image/"):
            return extract_image(file_path), extract_image_metadata(file_path), "image"
        if mime.startswith("audio/"):
            return transcribe_audio(file_path), {}, "transcription"
        if mime.startswith("video/"):
            return extract_video_metadata(file_path), {"metadata": extract_video_metadata_json(file_path)}, "video_metadata"
        if mime == "application/vnd.android.package-archive" or name.endswith(".apk"):
            return analyze_apk(file_path), {}, "apk"
        if mime == "application/zip" or name.endswith(".zip"):
            return extract_text_file(file_path, mime), {}, "text"
        raise UnsupportedEvidenceError(f"Unsupported MIME type for analysis: {mime}")


# --- text --------------------------------------------------------------------


def extract_text_file(file_path: str, mime: str) -> str:
    data = Path(file_path).read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = data.decode("latin-1")
        except UnicodeDecodeError:
            raise ProcessingError("Unable to decode text file (unsupported encoding)")
    if mime == "application/json" or file_path.lower().endswith(".json"):
        try:
            return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            return text
    if file_path.lower().endswith(".eml"):
        return _parse_eml(data)
    if file_path.lower().endswith(".html"):
        return _html_to_text(text)
    return text


def _parse_eml(data: bytes) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(data)
    lines = [
        f"From: {msg.get('From', '')}",
        f"To: {msg.get('To', '')}",
        f"Subject: {msg.get('Subject', '')}",
        f"Date: {msg.get('Date', '')}",
        f"Message-ID: {msg.get('Message-ID', '')}",
        "",
    ]
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                lines.append(part.get_content())
                break
    else:
        lines.append(msg.get_content())
    return "\n".join(lines)


def _html_to_text(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# --- pdf ---------------------------------------------------------------------


def extract_pdf(file_path: str) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ProcessingError("PDF support requires PyMuPDF (pip install pymupdf)") from exc
    try:
        doc = fitz.open(file_path)
    except Exception as exc:
        raise ProcessingError(f"PDF unreadable/corrupt: {exc}") from exc
    if doc.page_count == 0:
        raise ProcessingError("PDF has no pages")
    parts: list[str] = []
    for page_no in range(doc.page_count):
        page = doc.load_page(page_no)
        parts.append(f"--- PAGE {page_no + 1} ---\n{page.get_text('text')}")
    doc.close()
    return "\n\n".join(parts)


# --- images / OCR ------------------------------------------------------------


def _module(name: str):
    try:
        import importlib

        return importlib.import_module(name)
    except ImportError:
        return None


def self_ocr_available() -> bool:
    """True when pytesseract + TESSERACT_CMD are available."""
    return _module("pytesseract") is not None and bool(os.getenv("TESSERACT_CMD"))


def extract_image(file_path: str) -> str:
    """OCR an image when tesseract is configured; else return a clear limitation."""
    from PIL import Image

    try:
        Image.open(file_path).verify()
    except Exception as exc:
        raise ProcessingError(f"Image corrupt or unsupported: {exc}") from exc
    if self_ocr_available():
        import pytesseract

        try:
            return pytesseract.image_to_string(Image.open(file_path))
        except Exception as exc:
            raise ProcessingError(f"OCR failed: {exc}") from exc
    return "OCR unavailable - tesseract not configured. Image metadata only."


def extract_image_metadata(file_path: str) -> dict:
    from PIL import Image
    from PIL.ExifTags import TAGS

    try:
        img = Image.open(file_path)
        info: dict[str, Any] = {"format": img.format, "mode": img.mode, "size": [img.width, img.height]}
        exif = img.getexif()
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, str(tag_id))
            if tag in ("DateTime", "DateTimeOriginal", "Make", "Model", "Software"):
                info[tag] = str(value)
        img.close()
        return info
    except Exception as exc:
        raise ProcessingError(f"Metadata extraction failed: {exc}") from exc


# --- audio / video -----------------------------------------------------------


def transcribe_audio(file_path: str) -> str:
    """Whisper transcription via an OpenAI-compatible API endpoint.

    No API key configured -> clear error, never fake transcripts.
    """
    api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY")
    endpoint = os.getenv("WHISPER_API_URL") or "https://api.openai.com/v1/audio/transcriptions"
    model = os.getenv("WHISPER_MODEL") or "whisper-1"
    if not api_key:
        raise ProcessingError("Audio transcription unavailable: set WHISPER_API_KEY to enable it.")
    try:
        import httpx

        with open(file_path, "rb") as fh:
            resp = httpx.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (Path(file_path).name, fh)},
                data={"model": model},
                timeout=600,
            )
        resp.raise_for_status()
        return resp.json().get("text", "")
    except Exception as exc:
        raise ProcessingError(f"Transcription failed: {exc}") from exc


def _ffprobe() -> str | None:
    import shutil

    return shutil.which("ffprobe")


def extract_video_metadata(file_path: str) -> str:
    return json.dumps(extract_video_metadata_json(file_path), indent=2)


def extract_video_metadata_json(file_path: str) -> dict:
    probe = _ffprobe()
    if not probe:
        return {"note": "ffprobe not installed - video metadata limited to file basics", "size": os.path.getsize(file_path)}
    import subprocess

    try:
        out = subprocess.run(
            [probe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path],
            capture_output=True, text=True, timeout=120,
        )
        data = json.loads(out.stdout)
        streams = []
        for s in data.get("streams", []):
            streams.append({k: s.get(k) for k in ("codec_type", "codec_name", "width", "height", "duration", "nb_frames") if k in s})
        return {"format": data.get("format"), "streams": streams}
    except Exception as exc:
        raise ProcessingError(f"ffprobe failed: {exc}") from exc


# --- APK static analysis -----------------------------------------------------

PERMISSION_RE = re.compile(rb"android\.permission\.([A-Z0-9_.]+)")
DOMAIN_RE = re.compile(rb"https?://([a-zA-Z0-9.\-]+)|([a-zA-Z0-9\-]+\.(com|org|net|io|app|tech|info))\b")


def analyze_apk(file_path: str) -> str:
    """Isolated static analysis of an APK: never executed, only read."""
    report: dict[str, Any] = {"package": "", "permissions": [], "files": [], "domains": [], "signing": "", "suspicious_indicators": []}
    try:
        with zipfile.ZipFile(file_path) as zf:
            names = zf.namelist()
            report["files"] = [n for n in names if not n.endswith("/")][:500]
            manifest = zf.read("AndroidManifest.xml") if "AndroidManifest.xml" in names else b""
            report["permissions"] = sorted({m.decode() for m in PERMISSION_RE.findall(manifest)})
            raw_bytes = b"".join(
                zf.read(n)
                for n in names
                if n.endswith((".txt", ".json", ".xml", ".csv", ".js", ".html")) or "assets" in n
            )[: 3 * 1024 * 1024]
            report["domains"] = sorted({(m[0] or m[1]).decode() for m in DOMAIN_RE.findall(raw_bytes)})
        report["signing"] = "signature block present (deep verification requires apksigner)" if any(
            n.startswith("META-INF/") for n in names if n
        ) else "no signature block found"
        report["suspicious_indicators"] = [
            i for i in ("android.permission.RECORD_AUDIO", "android.permission.CAMERA", "android.permission.SEND_SMS")
            if i in report["permissions"]
        ]
        report["strings"] = _readable_strings(manifest, max_items=200)
    except zipfile.BadZipFile as exc:
        raise ProcessingError(f"APK is not a valid zip archive: {exc}") from exc
    except Exception as exc:
        raise ProcessingError(f"APK static analysis failed: {exc}") from exc
    return json.dumps(report, indent=2)


def _readable_strings(data: bytes, max_items: int = 200) -> list[str]:
    found = re.findall(rb"[\x20-\x7e]{6,}", data)
    out: list[str] = []
    for f in found:
        s = f.decode("latin-1")
        if not s.startswith(("android", "http")):
            out.append(s)
        if len(out) >= max_items:
            break
    return out


# --- media authenticity (experimental) ---------------------------------------


def screen_media_authenticity(file_path: str) -> dict:
    """
    EXPERIMENTAL media authenticity screening (images only).

    Outputs EXIF-based signals with explicitly tentative language. Never
    claims definitive deepfake detection.
    """
    signals: list[str] = []
    try:
        meta = extract_image_metadata(file_path)
    except Exception as exc:
        return {"model": "experimental-exif-screening-v1", "verdict": "INCONCLUSIVE", "signals": [], "disclaimer": str(exc)}
    if meta.get("DateTimeOriginal"):
        signals.append("timestamp metadata present")
    else:
        signals.append("no capture timestamp metadata (possible re-encode)")
    if len(meta) <= 3:
        signals.append("minimal EXIF footprint (may indicate stripping or repackaging)")
    return {
        "model": "experimental-exif-screening-v1",
        "verdict": "REVIEW_MANUALLY",
        "signals": signals,
        "extracted_metadata": meta,
        "has_software_tag": bool(meta.get("Software")),
        "disclaimer": "EXPERIMENTAL SCREENING ONLY - not a deepfake detection model. Manual expert review required.",
    }