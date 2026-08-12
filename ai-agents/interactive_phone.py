"""
interactive_phone.py — Full interactive evidence-intake + AI-analysis demo.

Guided menu: choose what to fetch from the phone -> everything gets
PROPERLY saved into the case folder (JSON + evidence_metadata + hashes,
same as the automated pipeline would do) -> optionally ingest any
WhatsApp/Telegram chat exports -> optionally run the full AI agent
pipeline right here and see risk score + FIR draft.

For a fully automated (zero-prompt) run, use graph_builder.run_investigation()
instead. This script is for live demos / manual case building.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from intake.adb_fetch import ADBFetcher, ADBError, sha256_of_file
from intake.case_builder import CaseBuilder

CASES_ROOT = Path(__file__).parent / "cases"
# Default ADB path — CHANGE THIS TO YOUR EXACT PATH (full path to adb.exe)
DEFAULT_ADB_PATH = r"D:\Android\platform-tools\adb.exe"


# ------------------------------------------------------------------
# Helper Functions (Moved to top so they are defined before use)
# ------------------------------------------------------------------
def sha256_of_text_safe(obj) -> str:
    """Small local helper to hash a dict/object safely."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()


def ask_user(prompt: str, default: str = "n") -> bool:
    """Ask user a yes/no question. Returns True if user says yes."""
    resp = input(f"{prompt} (y/n) [{default}]: ").strip().lower()
    if resp == "":
        return default == "y"
    return resp in ["y", "yes"]


def ask_text(prompt: str, default: str = "") -> str:
    resp = input(f"{prompt}" + (f" [{default}]" if default else "") + ": ").strip()
    return resp or default


# ------------------------------------------------------------------
# Main Interactive Intake Function
# ------------------------------------------------------------------
def interactive_intake() -> None:
    print("=" * 60)
    print("🔍 INVESTCOPS AI — Interactive Phone Evidence Intake")
    print("=" * 60)

    # ---- Case setup ----
    case_id = ask_text("\n📁 Case ID", default="DEMO001")
    investigator = ask_text("👮 Investigator name", default="unknown")

    # ---- ADB Path ----
    default_adb = os.getenv("ADB_PATH", DEFAULT_ADB_PATH)
    adb_path = ask_text("\n📌 ADB path", default=default_adb)

    fetcher = ADBFetcher(adb_path=adb_path)

    # ---- Check Connection ----
    print("\n📱 Checking device connection...")
    try:
        if not fetcher.check_device_connected():
            print("❌ No device connected! Check USB cable and USB debugging.")
            return
        print("✅ Device connected!")
    except ADBError as e:
        print(f"❌ ADB Error: {e}")
        return

    # ---- Case folder is created the moment CaseBuilder is instantiated ----
    builder = CaseBuilder(case_id=case_id, cases_root=str(CASES_ROOT), investigator=investigator)
    print(f"📁 Case folder ready: {builder.case_dir.resolve()}")

    # ---- Device info: always captured, no permission concern ----
    print("\n📱 Device Info (auto-fetched):")
    info = fetcher.get_device_info()
    for k, v in info.items():
        print(f"   {k}: {v}")
    
    (builder.case_dir / "device_info.json").write_text(json.dumps(info, indent=2))
    eid = builder._register_evidence(
        "device_info.json", "device_metadata", "ADB device query",
        sha256_of_text_safe(info),
    )
    builder.raw_texts.append(f"[{eid}] Device info: {json.dumps(info)}")

    fetched_counts = {"call_logs": 0, "contacts": 0, "sms": 0, "notifications": 0, "media": 0}

    # ---- 1. Call Logs ----
    if ask_user("\n📞 Fetch Call Logs?"):
        print("   Fetching call logs...")
        call_log = fetcher.fetch_call_log()
        builder._save_json_evidence(
            builder.call_logs_dir / "call_log.json", call_log,
            source="ADB content://call_log/calls", label="Call log",
        )
        fetched_counts["call_logs"] = len(call_log)
        print(f"   ✅ {len(call_log)} call records found and saved to case file.")
        if call_log:
            print(f"   Sample: {call_log[0]}")
    else:
        print("   ⏭️  Skipped call logs.")

    # ---- 2. Contacts ----
    if ask_user("\n👤 Fetch Contacts?"):
        print("   Fetching contacts...")
        contacts = fetcher.fetch_contacts()
        builder._save_json_evidence(
            builder.contacts_dir / "contacts.json", contacts,
            source="ADB content://contacts/phones", label="Contacts",
        )
        fetched_counts["contacts"] = len(contacts)
        print(f"   ✅ {len(contacts)} contacts found and saved to case file.")
        if contacts:
            print(f"   Sample: {contacts[0]}")
    else:
        print("   ⏭️  Skipped contacts.")

    # ---- 3. SMS ----
    if ask_user("\n✉️  Fetch SMS?"):
        print("   Fetching SMS...")
        sms = fetcher.fetch_sms()
        builder._save_json_evidence(
            builder.sms_dir / "sms.json", sms,
            source="ADB content://sms", label="SMS messages",
        )
        fetched_counts["sms"] = len(sms)
        print(f"   ✅ {len(sms)} SMS found and saved to case file.")
        if sms:
            print(f"   Sample: {sms[0]}")
    else:
        print("   ⏭️  Skipped SMS.")

    # ---- 4. Notifications ----
    if ask_user("\n🔔 Fetch Notifications?"):
        print("   Fetching notifications...")
        notifications = fetcher.fetch_notifications()
        builder._save_json_evidence(
            builder.notifications_dir / "notifications.json", notifications,
            source="ADB dumpsys notification", label="Recent notifications",
        )
        fetched_counts["notifications"] = len(notifications)
        print(f"   ✅ {len(notifications)} notification block(s) found and saved.")
    else:
        print("   ⏭️  Skipped notifications.")

    # ---- 5. Media (Photos/Videos) ----
    if ask_user("\n🖼️  Pull Media files (photos/videos)?"):
        max_files_str = ask_text("   Max files to pull", default="100")
        max_files = int(max_files_str) if max_files_str.isdigit() else 100

        print(f"   Scanning + pulling up to {max_files} media files (this may take a while)...")
        pulled_files = fetcher.pull_media(builder.media_dir, max_files=max_files)
        for path in pulled_files:
            file_hash = sha256_of_file(path)
            m_eid = builder._register_evidence(
                path.name, path.suffix.lstrip(".") or "unknown",
                "ADB pull (internal storage scan)", file_hash, path.stat().st_size,
            )
            builder.raw_texts.append(f"[{m_eid}] Media file: {path.name} (hash={file_hash[:12]}...)")
        fetched_counts["media"] = len(pulled_files)
        print(f"   ✅ Pulled {len(pulled_files)} media files.")
        print(f"   📁 Saved in: {builder.media_dir.resolve()}")
    else:
        print("   ⏭️  Skipped media pull.")

    builder._save_manifest()

    # ---- 6. Chat exports (WhatsApp/Telegram) ----
    print(f"\n📄 Chat exports folder: {builder.chat_exports_dir.resolve()}")
    if ask_user("   Have you placed any WhatsApp/Telegram 'Export Chat' .txt files there?"):
        count = builder.ingest_chat_exports()
        print(f"   ✅ Ingested {count} chat export file(s).")
    else:
        print("   ⏭️  No chat exports ingested. (You can drop .txt files in that folder "
              "and re-run this script anytime — already-ingested files won't be duplicated.)")

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("📊 INTAKE SUMMARY")
    print("=" * 60)
    print(f"   Case ID:       {case_id}")
    print(f"   Case folder:   {builder.case_dir.resolve()}")
    print(f"   Call Logs:     {fetched_counts['call_logs']} records")
    print(f"   Contacts:      {fetched_counts['contacts']} records")
    print(f"   SMS:           {fetched_counts['sms']} records")
    print(f"   Notifications: {fetched_counts['notifications']} block(s)")
    print(f"   Media files:   {fetched_counts['media']} files")
    print(f"   Total evidence items registered: {len(builder.evidence_metadata)}")

    # ---- 7. Optionally run the full AI pipeline right now ----
    if ask_user("\n🤖 Run the AI agent pipeline on this case now?"):
        run_pipeline(builder)
    else:
        print(f"\n👉 Run it later with: python orchestrator/graph_builder.py {case_id}")

    print("\n✅ Interactive intake complete!")


# ------------------------------------------------------------------
# AI Pipeline Runner (Corrected function name)
# ------------------------------------------------------------------
def run_pipeline(builder: CaseBuilder) -> None:
    """Runs the full 11-agent LangGraph pipeline on the case just built,
    and prints the key results (risk score, contradictions, FIR draft).
    """
    print("\n🤖 Running AI agent pipeline (this calls Ollama qwen3:8b for each "
          "agent — may take a few minutes depending on evidence volume)...")
    try:
        # FIX: Correct function name is build_case_pipeline
        from orchestrator.graph_builder import build_case_pipeline
    except ImportError as e:
        print(f"❌ Could not import the pipeline: {e}")
        print("   Make sure orchestrator/graph_builder.py and langgraph are set up.")
        return

    try:
        initial_state = builder.build_initial_state()
        app = build_case_pipeline()  # 👈 FIXED
        result = app.invoke(initial_state)
    except Exception as e:
        print(f"❌ Pipeline run failed: {e}")
        print("   Check that `ollama serve` is running and qwen3:8b is pulled.")
        return

    print("\n" + "=" * 60)
    print("🧠 AI ANALYSIS RESULTS")
    print("=" * 60)
    entity_counts = {k: len(v) for k, v in result.get("entities", {}).items()}
    print(f"   Entities found: {entity_counts}")
    print(f"   Contradictions: {len(result.get('contradictions', []))}")
    print(f"   Risk score:     {result.get('risk_score')}/100")
    fir = result.get("fir_draft", "")
    print(f"   FIR draft:      {len(fir)} characters generated")
    print(f"\n   Full case folder (all evidence + manifest.json): {builder.case_dir.resolve()}")


# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------
if __name__ == "__main__":
    interactive_intake()