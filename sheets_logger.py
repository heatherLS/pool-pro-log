"""
sheets_logger.py

Logs pool visit results to a Google Sheet for recovery tracking.
Gracefully no-ops if credentials are not configured.

Setup (one-time):
  1. pip install gspread google-auth
  2. Create a Google Service Account at https://console.cloud.google.com/
     OR run once with OAuth: gspread.oauth() — see README
  3. Set env var: GOOGLE_SHEETS_CREDENTIALS_FILE=/path/to/credentials.json
  4. Share your Google Sheet with the service account email

Sheet ID: 1vwfa29qUD3fa3obXPVGTcwoXp8EubUajYMK-vfs6fN4
"""

import io
import os
import json
from datetime import date, datetime
from typing import Any, Dict, Optional

SHEET_ID = "1vwfa29qUD3fa3obXPVGTcwoXp8EubUajYMK-vfs6fN4"
DRIVE_FOLDER_NAME = "Pool Pro Log — Visit Photos"
TAB_ACCOUNTS = "Accounts"
TAB_VISITS = "Visits"
TAB_PROVIDERS = "Providers"

# Columns written to the Accounts tab (upsert by account_id)
ACCOUNT_COLUMNS = [
    "account_id", "customer_name", "service_address", "city", "state", "zip",
    "provider_id", "provider_name", "status_active", "recovery_status",
    "recovery_mode_current", "first_recovery_date", "latest_visit_date",
    "visits_in_recovery", "days_in_recovery", "billing_started", "billing_start_date",
    "still_not_clear_flag", "billing_risk_flag", "likely_equipment_issue_flag",
    "likely_metals_flag", "water_source", "pool_type", "pool_shape",
    "pool_size_bucket", "estimated_gallons",
]

# Columns written to the Visits tab (always append)
VISIT_COLUMNS = [
    "visit_id", "account_id", "provider_id", "provider_name", "visit_date",
    "visit_timestamp", "pool_type", "pool_shape", "pool_size_bucket",
    "estimated_gallons", "water_source", "water_level", "filter_type",
    "visible_debris_level", "surface_algae_level", "water_color_input",
    "bottom_visibility", "filled_with_well_water_flag",
    "strip_free_chlorine_bucket", "strip_ph_bucket", "strip_alkalinity_bucket",
    "strip_cya_bucket", "strip_confidence",
    "ai_primary_mode", "ai_severity", "ai_today_priority", "ai_expected_result_next_visit",
    "rules_progress_status", "rules_escalation_flag", "rules_escalation_reason",
    "checklist_debris_removed", "checklist_pool_brushed", "checklist_filter_cleaned",
    "checklist_chemicals_added", "checklist_pump_running", "checklist_before_after_photos",
    "pool_photo_url", "strip_chart_photo_url",
    "visit_notes", "created_at",
]


def _get_creds_from_secrets(scopes: list):
    """Return Google OAuth Credentials from st.secrets, or None if not available."""
    try:
        import streamlit as st
        from google.oauth2.service_account import Credentials
        if "google_credentials" in st.secrets:
            creds_dict = dict(st.secrets["google_credentials"])
            # Streamlit escapes newlines in private_key — unescape them
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            return Credentials.from_service_account_info(creds_dict, scopes=scopes)
    except Exception:
        pass
    return None


def _get_client():
    """Return an authenticated gspread client, or None if not configured."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None, "gspread not installed. Run: pip install gspread google-auth"

    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    # 1. Streamlit Cloud secrets (st.secrets["google_credentials"])
    creds = _get_creds_from_secrets(scopes)
    if creds:
        try:
            client = gspread.authorize(creds)
            return client, None
        except Exception as e:
            return None, f"Credentials error (st.secrets): {e}"

    # 2. Explicit env var path (service account JSON)
    creds_file = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE")
    if creds_file and os.path.exists(creds_file):
        try:
            creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
            client = gspread.authorize(creds)
            return client, None
        except Exception as e:
            return None, f"Credentials error: {e}"

    # 3. Default gspread service account (~/.config/gspread/service_account.json)
    try:
        client = gspread.service_account()
        return client, None
    except Exception:
        pass

    # 4. OAuth browser flow (prompts once, caches token)
    try:
        client = gspread.oauth()
        return client, None
    except Exception as e:
        return None, f"No credentials configured. Set GOOGLE_SHEETS_CREDENTIALS_FILE or add ~/.config/gspread/service_account.json. Error: {e}"


def _get_drive_service():
    """Return an authenticated Google Drive service using the same service account."""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
    except ImportError:
        return None

    drive_scopes = ["https://www.googleapis.com/auth/drive"]

    # 1. Streamlit Cloud secrets
    creds = _get_creds_from_secrets(drive_scopes)
    if creds:
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    # 2. Local file fallback
    creds_file = (
        os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE")
        or os.path.expanduser("~/.config/gspread/service_account.json")
    )
    if not os.path.exists(creds_file):
        return None

    creds = Credentials.from_service_account_file(creds_file, scopes=drive_scopes)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _get_or_create_drive_folder(service) -> Optional[str]:
    """Return the Drive folder ID for visit photos, creating it if needed."""
    query = f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    folder = service.files().create(
        body={"name": DRIVE_FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder"},
        fields="id",
    ).execute()
    # Make the folder readable by anyone with the link
    service.permissions().create(
        fileId=folder["id"],
        body={"role": "reader", "type": "anyone"},
    ).execute()
    return folder["id"]


def upload_photo_to_drive(file_bytes: bytes, filename: str, mime_type: str = "image/jpeg") -> Optional[str]:
    """
    Upload a photo to Google Drive and return its shareable URL.
    Returns None if Drive is not configured or upload fails.
    """
    try:
        from googleapiclient.http import MediaIoBaseUpload
        service = _get_drive_service()
        if not service:
            return None

        folder_id = _get_or_create_drive_folder(service)
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=False)
        file_meta = {"name": filename, "parents": [folder_id]}
        uploaded = service.files().create(body=file_meta, media_body=media, fields="id").execute()
        file_id = uploaded.get("id")
        # Make publicly readable
        service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()
        return f"https://drive.google.com/file/d/{file_id}/view"
    except Exception:
        return None


def _build_row(visit: Dict[str, Any], result: Dict[str, Any], account: Dict[str, Any]) -> Dict[str, Any]:
    """Map visit + result data into sheet column values."""
    today = date.today().isoformat()
    mode = result.get("ai_primary_mode", result.get("recovery_mode_current", ""))
    severity = result.get("ai_severity", 0)
    progress = result.get("rules_progress_status", "first_visit")
    escalation = result.get("rules_escalation_flag", False)

    still_not_clear = (
        visit.get("water_color_input", "") not in {"clear", "cloudy_blue"}
        or severity >= 4
    )
    billing_risk = escalation or (
        result.get("billing_started") and still_not_clear
    )

    return {
        "account_id":                account.get("account_id", visit.get("account_id", "")),
        "customer_name":             account.get("customer_name", ""),
        "service_address":           account.get("service_address", ""),
        "city":                      account.get("city", ""),
        "state":                     account.get("state", ""),
        "zip":                       account.get("zip", ""),
        "provider_id":               account.get("provider_id", visit.get("provider_id", "")),
        "provider_name":             account.get("provider_name", ""),
        "status_active":             account.get("status_active", "active"),
        "recovery_status":           progress,
        "recovery_mode_current":     mode,
        "first_recovery_date":       account.get("first_recovery_date", today),
        "latest_visit_date":         today,
        "visits_in_recovery":        account.get("visits_in_recovery", 0) + 1,
        "days_in_recovery":          account.get("days_in_recovery", 0),
        "billing_started":           str(visit.get("billing_started", False)),
        "billing_start_date":        account.get("billing_start_date", ""),
        "still_not_clear_flag":      str(still_not_clear),
        "billing_risk_flag":         str(billing_risk),
        "likely_equipment_issue_flag": str(escalation and "equipment" in result.get("rules_escalation_reason", "").lower()),
        "likely_metals_flag":        str(mode == "metals" or visit.get("filled_with_well_water_flag", False)),
        "water_source":              "well" if visit.get("filled_with_well_water_flag") else "municipal",
        "pool_type":                 visit.get("pool_type", ""),
        "pool_shape":                visit.get("pool_shape", ""),
        "pool_size_bucket":          visit.get("pool_size_bucket", ""),
        "estimated_gallons":         visit.get("estimated_gallons", ""),
    }


def upsert_recovery_row(
    visit: Dict[str, Any],
    result: Dict[str, Any],
    account: Dict[str, Any],
    checklist: Optional[Dict[str, bool]] = None,
    visit_notes: str = "",
    pool_photo: Optional[bytes] = None,
    strip_photo: Optional[bytes] = None,
) -> tuple[bool, str]:
    """
    1. Upsert the Accounts tab (update recovery status for this account).
    2. Append a new row to the Visits tab (full visit record).
    Returns (success: bool, message: str).
    """
    client, err = _get_client()
    if client is None:
        return False, f"Sheets not configured — skipping log. ({err})"

    checklist = checklist or {}
    today = date.today().isoformat()
    now = datetime.now().isoformat(timespec="seconds")

    try:
        ss = client.open_by_key(SHEET_ID)
        account_id = str(account.get("account_id", visit.get("account_id", "")))

        # --- 1. Upsert Accounts tab ---
        acct_sheet = ss.worksheet(TAB_ACCOUNTS)
        acct_data = acct_sheet.get_all_records()
        row_data = _build_row(visit, result, account)
        acct_values = [str(row_data.get(col, "")) for col in ACCOUNT_COLUMNS]

        existing_row_idx = None
        for i, record in enumerate(acct_data):
            if str(record.get("account_id", "")) == account_id:
                existing_row_idx = i + 2
                break

        if existing_row_idx:
            acct_sheet.update(f"A{existing_row_idx}", [acct_values])
        else:
            acct_sheet.append_row(acct_values)

        # --- 2. Append to Visits tab ---
        visit_sheet = ss.worksheet(TAB_VISITS)
        visit_row = {
            "visit_id":                   f"VIS-{now.replace(':', '').replace('-', '').replace('T', '')}",
            "account_id":                 account_id,
            "provider_id":                visit.get("provider_id", ""),
            "provider_name":              visit.get("provider_name", ""),
            "visit_date":                 today,
            "visit_timestamp":            now,
            "pool_type":                  visit.get("pool_type", ""),
            "pool_shape":                 visit.get("pool_shape", ""),
            "pool_size_bucket":           visit.get("pool_size_bucket", ""),
            "estimated_gallons":          visit.get("estimated_gallons", ""),
            "water_source":               visit.get("water_source", ""),
            "water_level":                visit.get("water_level", ""),
            "filter_type":                visit.get("filter_type", ""),
            "visible_debris_level":       visit.get("visible_debris_level", ""),
            "surface_algae_level":        visit.get("surface_algae_level", ""),
            "water_color_input":          visit.get("water_color_input", ""),
            "bottom_visibility":          visit.get("bottom_visibility", ""),
            "filled_with_well_water_flag": str(visit.get("filled_with_well_water_flag", False)),
            "strip_free_chlorine_bucket": visit.get("strip_free_chlorine_bucket", ""),
            "strip_ph_bucket":            visit.get("strip_ph_bucket", ""),
            "strip_alkalinity_bucket":    visit.get("strip_alkalinity_bucket", ""),
            "strip_cya_bucket":           visit.get("strip_cya_bucket", ""),
            "strip_confidence":           visit.get("strip_confidence", ""),
            "ai_primary_mode":            result.get("ai_primary_mode", ""),
            "ai_severity":                str(result.get("ai_severity", "")),
            "ai_today_priority":          result.get("ai_today_priority", ""),
            "ai_expected_result_next_visit": " | ".join(result.get("ai_expected_result_next_visit", [])),
            "rules_progress_status":      result.get("rules_progress_status", ""),
            "rules_escalation_flag":      str(result.get("rules_escalation_flag", False)),
            "rules_escalation_reason":    result.get("rules_escalation_reason", ""),
            "checklist_debris_removed":   str(checklist.get("debris", False)),
            "checklist_pool_brushed":     str(checklist.get("brushed", False)),
            "checklist_filter_cleaned":   str(checklist.get("filter", False)),
            "checklist_chemicals_added":  str(checklist.get("chems", False)),
            "checklist_pump_running":     str(checklist.get("pump", False)),
            "checklist_before_after_photos": str(checklist.get("photos", False)),
            "pool_photo_url":             upload_photo_to_drive(pool_photo, f"{account_id}_{today}_pool.jpg") if pool_photo else "",
            "strip_chart_photo_url":      upload_photo_to_drive(strip_photo, f"{account_id}_{today}_strip.jpg") if strip_photo else "",
            "visit_notes":                visit_notes,
            "created_at":                 now,
        }
        visit_values = [str(visit_row.get(col, "")) for col in VISIT_COLUMNS]
        visit_sheet.append_row(visit_values)

        return True, f"Visit logged for account {account_id}."

    except Exception as e:
        return False, f"Sheet write failed: {e}"


# ---------------------------------------------------------------------------
# READ FUNCTIONS — load accounts / providers / visit history from sheet
# ---------------------------------------------------------------------------

def load_accounts_from_sheet() -> list[Dict[str, Any]]:
    """Return all rows from the Accounts tab, or [] if unavailable."""
    client, _ = _get_client()
    if client is None:
        return []
    try:
        ws = client.open_by_key(SHEET_ID).worksheet(TAB_ACCOUNTS)
        return ws.get_all_records()
    except Exception:
        return []


def load_providers_from_sheet() -> list[Dict[str, Any]]:
    """Return all rows from the Providers tab, or [] if unavailable."""
    client, _ = _get_client()
    if client is None:
        return []
    try:
        ws = client.open_by_key(SHEET_ID).worksheet(TAB_PROVIDERS)
        return ws.get_all_records()
    except Exception:
        return []


def load_visit_history_from_sheet(account_id: str) -> list[Dict[str, Any]]:
    """Return all visits for account_id from the Visits tab, sorted by date."""
    client, _ = _get_client()
    if client is None:
        return []
    try:
        ws = client.open_by_key(SHEET_ID).worksheet(TAB_VISITS)
        all_values = ws.get_all_values()
        if not all_values:
            return []

        # Detect whether row 1 is a header row or data.
        # A header row starts with "visit_id"; a data row starts with "VIS-".
        first_row = all_values[0]
        if first_row and str(first_row[0]).startswith("visit_id"):
            data_rows = all_values[1:]
        else:
            # No header row — data starts at row 1, written in VISIT_COLUMNS order.
            data_rows = all_values

        # Map each row to a dict using VISIT_COLUMNS as the schema.
        records = []
        for row in data_rows:
            padded = list(row) + [""] * max(0, len(VISIT_COLUMNS) - len(row))
            record = {VISIT_COLUMNS[i]: padded[i] for i in range(len(VISIT_COLUMNS))}
            records.append(record)

        visits = [r for r in records if str(r.get("account_id", "")) == str(account_id)]
        return sorted(visits, key=lambda v: v.get("visit_date", ""))
    except Exception:
        return []


def get_prior_recovery_context(account_id: str) -> Optional[Dict[str, Any]]:
    """Pull prior recovery data for an account from the Accounts tab."""
    client, _ = _get_client()
    if client is None:
        return None
    try:
        ws = client.open_by_key(SHEET_ID).worksheet(TAB_ACCOUNTS)
        for record in ws.get_all_records():
            if str(record.get("account_id", "")) == str(account_id):
                return record
        return None
    except Exception:
        return None
