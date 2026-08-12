"""
intake/case_builder.py

Orchestrator: "connect phone -> one command -> case file folder created ->
InvestigationState ready for the AI agent pipeline."

Folder structure created for each case:

    cases/
    └── CASE_<case_id>/
        ├── manifest.json                  <- full evidence_metadata dict
        ├── device_info.json
        ├── call_logs/call_log.json
        ├── contacts/contacts.json
        ├── sms/sms.json
        ├── notifications/notifications.json
        ├── media/                         <- pulled photos/videos (files)
        └── chat_exports/                  <- investigator-uploaded
                                              WhatsApp/Telegram export .txt
                                              files go here (copy them in
                                              manually or via your backend
                                              upload API before calling
                                              build_case_from_folder)

Usage:
    from intake.adb_fetch import ADBFetcher
    from intake.case_builder import CaseBuilder

    fetcher = ADBFetcher()  # assumes single device on USB
    builder = CaseBuilder(case_id="CASE001", cases_root="cases")

    builder.run_full_intake(fetcher)                 # pulls everything from phone
    # ... investigator drops WhatsApp_Chat_with_Rahul.txt into
    #     cases/CASE001/chat_exports/  ...
    builder.ingest_chat_exports()                     # parses any .txt exports present

    state = builder.build_initial_state()              # -> InvestigationState
    # pass `state` into your LangGraph pipeline (agent_1_ingestion onwards)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from intake.adb_fetch import ADBFetcher, sha256_of_file, sha256_of_text
from intake.whatsapp_parser import chat_to_raw_text, detect_platform, parse_chat_export

from core.state import InvestigationState, get_initial_state


class CaseBuilder:
    def __init__(self, case_id: str, cases_root: str = "cases", investigator: str = "unknown"):
        self.case_id = case_id
        self.investigator = investigator
        self.case_dir = Path(cases_root) / f"CASE_{case_id}"
        self.call_logs_dir = self.case_dir / "call_logs"
        self.contacts_dir = self.case_dir / "contacts"
        self.sms_dir = self.case_dir / "sms"
        self.notifications_dir = self.case_dir / "notifications"
        self.media_dir = self.case_dir / "media"
        self.chat_exports_dir = self.case_dir / "chat_exports"

        for d in [
            self.case_dir, self.call_logs_dir, self.contacts_dir, self.sms_dir,
            self.notifications_dir, self.media_dir, self.chat_exports_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

        # In-memory accumulators; also persisted to manifest.json
        self.evidence_metadata: Dict[str, Dict[str, Any]] = {}
        self.raw_texts: List[str] = []
        self._evidence_counter = 0

        manifest_path = self.case_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                self.evidence_metadata = saved.get("evidence_metadata", {})
                self.raw_texts = saved.get("raw_texts", [])
                self._evidence_counter = saved.get("evidence_counter", 0)

    # ------------------------------------------------------------------
    def _next_evidence_id(self) -> str:
        self._evidence_counter += 1
        return f"EVD{self._evidence_counter:03d}"

    def _register_evidence(
        self,
        file_name: str,
        file_type: str,
        source: str,
        content_hash: str,
        file_size: int = 0,
    ) -> str:
        evidence_id = self._next_evidence_id()
        self.evidence_metadata[evidence_id] = {
            "evidence_id": evidence_id,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "source": source,
            "hash": content_hash,
            "uploaded_by": self.investigator,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        return evidence_id

    def _save_manifest(self) -> None:
        with open(self.case_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "case_id": self.case_id,
                    "evidence_metadata": self.evidence_metadata,
                    "raw_texts": self.raw_texts,
                    "evidence_counter": self._evidence_counter,
                    "updated_at": datetime.utcnow().isoformat(),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    # ------------------------------------------------------------------
    # Step 1: Pull everything ADB can legitimately reach from the phone
    # ------------------------------------------------------------------
    def run_full_intake(self, fetcher: ADBFetcher) -> Dict[str, Any]:
        if not fetcher.check_device_connected():
            raise RuntimeError(
                "No authorized device found. Connect the phone via USB, "
                "enable USB debugging, and accept the RSA-key prompt on the "
                "phone screen, then retry."
            )

        summary = {"device_info": None, "call_log_count": 0, "contacts_count": 0,
                    "sms_count": 0, "notifications_captured": False, "media_files": 0}

        # --- Device info ---
        device_info = fetcher.get_device_info()
        with open(self.case_dir / "device_info.json", "w", encoding="utf-8") as f:
            json.dump(device_info, f, indent=2)
        eid = self._register_evidence(
            "device_info.json", "device_metadata", "ADB device query",
            sha256_of_text(json.dumps(device_info, sort_keys=True)),
        )
        self.raw_texts.append(f"[{eid}] Device info: {json.dumps(device_info)}")
        summary["device_info"] = device_info

        # --- Call log ---
        call_log = fetcher.fetch_call_log()
        self._save_json_evidence(self.call_logs_dir / "call_log.json", call_log,
                                  source="ADB content://call_log/calls", label="Call log")
        summary["call_log_count"] = len(call_log)

        # --- Contacts ---
        contacts = fetcher.fetch_contacts()
        self._save_json_evidence(self.contacts_dir / "contacts.json", contacts,
                                  source="ADB content://contacts/phones", label="Contacts")
        summary["contacts_count"] = len(contacts)

        # --- SMS ---
        sms = fetcher.fetch_sms()
        self._save_json_evidence(self.sms_dir / "sms.json", sms,
                                  source="ADB content://sms", label="SMS messages")
        summary["sms_count"] = len(sms)

        # --- Notifications (best-effort chat previews) ---
        notifications = fetcher.fetch_notifications()
        self._save_json_evidence(self.notifications_dir / "notifications.json", notifications,
                                  source="ADB dumpsys notification", label="Recent notifications")
        summary["notifications_captured"] = bool(notifications)

        # --- Media (photos/videos from shared storage) ---
        pulled_files = fetcher.pull_media(self.media_dir)
        for path in pulled_files:
            file_hash = sha256_of_file(path)
            eid = self._register_evidence(
                path.name, path.suffix.lstrip(".") or "unknown",
                "ADB pull (shared storage)", file_hash, path.stat().st_size,
            )
            self.raw_texts.append(f"[{eid}] Media file: {path.name} (hash={file_hash[:12]}...)")
        summary["media_files"] = len(pulled_files)

        self._save_manifest()
        return summary

    def _save_json_evidence(self, path: Path, data: List[Dict[str, str]], source: str, label: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if not data:
            return
        text_blob = json.dumps(data, ensure_ascii=False)
        eid = self._register_evidence(path.name, "json", source, sha256_of_text(text_blob), path.stat().st_size)
        self.raw_texts.append(f"[{eid}] {label} ({len(data)} entries):\n{text_blob}")

    # ------------------------------------------------------------------
    # Step 2: Ingest investigator-uploaded chat export .txt files
    # ------------------------------------------------------------------
    def ingest_chat_exports(self) -> int:
        """Parses every .txt file currently sitting in chat_exports/ that
        hasn't already been ingested (tracked via manifest hash), and adds
        it to raw_texts + evidence_metadata.
        """
        already_hashed = {v["hash"] for v in self.evidence_metadata.values()}
        ingested_count = 0

        for txt_file in self.chat_exports_dir.glob("*.txt"):
            file_hash = sha256_of_file(txt_file)
            if file_hash in already_hashed:
                continue  # already processed in a previous run

            platform = detect_platform(txt_file)
            messages = parse_chat_export(txt_file, platform=platform)
            if not messages:
                continue

            raw_blob = chat_to_raw_text(messages, chat_label=txt_file.stem)
            eid = self._register_evidence(
                txt_file.name, f"{platform}_chat_export", "Investigator upload (app export)",
                file_hash, txt_file.stat().st_size,
            )
            self.raw_texts.append(f"[{eid}] {raw_blob}")
            ingested_count += 1

        self._save_manifest()
        return ingested_count

    # ------------------------------------------------------------------
    # Step 3: Build the InvestigationState for the AI agent pipeline
    # ------------------------------------------------------------------
    def build_initial_state(self) -> InvestigationState:
        state = get_initial_state()
        state["raw_texts"] = list(self.raw_texts)
        state["evidence_metadata"] = dict(self.evidence_metadata)
        return state