import json
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st

from rules_engine import evaluate_visit
from action_mapping import build_action_output
from dosing_engine import build_dosing_output, merge_dosing_into_action_output
from image_detection import analyze_pool_images, build_detection_preview
from reference_dosing import GREEN_POOL_VISIT_CADENCE
from sheets_logger import (
    upsert_recovery_row,
    load_accounts_from_sheet,
    load_providers_from_sheet,
    load_visit_history_from_sheet,
)
from customer_notes import get_customer_sms, escalation_add_on
from field_tips import get_tips_for_mode, get_warning_tips_for_mode

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


st.set_page_config(
    page_title="DoseLogic",
    page_icon="⚡",
    layout="wide",
)


# -----------------------------
# HELPERS
# -----------------------------
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@st.cache_data
def load_sample_account() -> Dict[str, Any]:
    return {
        "account_id": "ACC-10001",
        "customer_name": "Sample Customer",
        "provider_id": "PRO-30001",
        "provider_name": "Sample Provider",
        "recovery_status": "new_recovery",
        "visits_in_recovery": 0,
        "days_in_recovery": 0,
        "billing_started": False,
        "billing_start_date": "",
        "current_severity": "",
        "progress_status": "",
        "escalation_status": "none",
        "escalation_reason": "",
    }


@st.cache_data
def load_sample_prior_visit() -> Dict[str, Any]:
    return {
        "visit_id": "VIS-20000",
        "account_id": "ACC-10001",
        "visit_date": "2026-03-20",
        "provider_name": "Sample Provider",
        "water_color_input": "dark_green",
        "surface_algae_level": "heavy",
        "visible_debris_level": "heavy",
        "bottom_visibility": "no",
        "strip_free_chlorine_bucket": "very_low",
        "strip_ph_bucket": "high",
        "strip_alkalinity_bucket": "acceptable",
        "strip_cya_bucket": "low",
        "brushed_last_visit": True,
        "filter_cleaned_last_visit": True,
        "vacuumed_to_waste_last_visit": "yes",
        "last_plan_summary": "Vacuumed debris, brushed entire pool, backwashed filter, added chlorine/shock, ran pump 24 hours.",
        "expected_next_result": "Pool should shift from dark green toward lighter green or cloudy blue.",
    }


@st.cache_data
def get_dropdowns() -> Dict[str, list[str]]:
    return {
        "pool_type": ["in_ground", "above_ground"],
        "pool_shape": ["rectangle", "kidney", "freeform", "other"],
        "pool_size_bucket": ["small", "medium", "large"],
        "water_source": ["municipal", "well", "unknown"],
        "water_level": ["low", "normal", "high"],
        "filter_type": ["cartridge", "sand", "DE", "unknown"],
        "yes_no_unknown": ["yes", "no", "unknown"],
        "debris": ["none", "light", "heavy", "unknown"],
        "algae": ["none", "light", "moderate", "heavy", "unknown"],
        "water_color": ["clear", "cloudy_blue", "light_green", "dark_green", "brown", "rusty", "tea_colored", "unknown"],
        "bottom_visibility": ["yes", "partial", "no", "unknown"],
        "chlorine_bucket": ["very_low", "low", "acceptable", "high", "unknown"],
        "ph_bucket": ["low", "acceptable", "high", "very_high", "unknown"],
        "alkalinity_bucket": ["low", "acceptable", "high", "unknown"],
        "cya_bucket": ["low", "acceptable", "high", "unclear", "unknown"],
        "strip_confidence": ["high", "medium", "low"],
    }


_DEMO_ACCOUNTS = [
    {
        "account_id": "DEMO-001",
        "customer_name": "Demo Customer A",
        "service_address": "123 Palm Tree Ln",
        "provider_id": "DEMO-PRO-01",
        "provider_name": "Demo Provider",
        "billing_started": False,
    },
    {
        "account_id": "DEMO-002",
        "customer_name": "Demo Customer B",
        "service_address": "456 Blue Water Dr",
        "provider_id": "DEMO-PRO-02",
        "provider_name": "Demo Provider 2",
        "billing_started": True,
    },
]

_DEMO_PROVIDERS = [
    {"provider_id": "DEMO-PRO-01", "provider_name": "Demo Provider"},
    {"provider_id": "DEMO-PRO-02", "provider_name": "Demo Provider 2"},
]

_DEMO_VISIT_HISTORY: Dict[str, list[Dict[str, Any]]] = {
    "DEMO-001": [
        {
            "visit_id": "VIS-DEMO-0",
            "visit_date": "2026-03-20",
            "provider_name": "Demo Provider",
            "water_color_input": "dark_green",
            "surface_algae_level": "heavy",
            "visible_debris_level": "heavy",
            "bottom_visibility": "no",
            "strip_free_chlorine_bucket": "very_low",
            "strip_ph_bucket": "high",
            "strip_alkalinity_bucket": "acceptable",
            "strip_cya_bucket": "low",
            "last_plan_summary": "Vacuumed debris, brushed entire pool, backwashed filter, added chlorine/shock.",
            "expected_next_result": "Pool should shift from dark green toward lighter green or cloudy blue.",
        }
    ],
    "DEMO-002": [],
}


@st.cache_data(ttl=60)
def _load_accounts() -> list[Dict[str, Any]]:
    rows = load_accounts_from_sheet()
    return rows if rows else _DEMO_ACCOUNTS


@st.cache_data(ttl=60)
def _load_providers() -> list[Dict[str, Any]]:
    rows = load_providers_from_sheet()
    return rows if rows else _DEMO_PROVIDERS


@st.cache_data(ttl=30)
def _load_visit_history(account_id: str) -> list[Dict[str, Any]]:
    return load_visit_history_from_sheet(account_id)


def get_account_display(account: Dict[str, Any]) -> str:
    return f"{account['customer_name']} — {account['service_address']} ({account['account_id']})"


def get_latest_visit_for_account(
    account_id: str,
    visit_history: Dict[str, list[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    visits = visit_history.get(account_id, [])
    if not visits:
        return None
    return visits[-1]


def build_visit_setup_section() -> Dict[str, Any]:
    accounts = _load_accounts()
    providers = _load_providers()

    st.subheader("🧾 Start Visit")
    st.caption("Select the customer — visit history loads automatically.")

    account_options = [get_account_display(a) for a in accounts]
    selected_account_display = st.selectbox(
        "Select Customer / Account",
        account_options,
        key="visit_setup_account",
    )

    selected_account = next(
        a for a in accounts if get_account_display(a) == selected_account_display
    )

    provider_names = [p["provider_name"] for p in providers]
    default_provider_index = 0
    if selected_account.get("provider_name") in provider_names:
        default_provider_index = provider_names.index(selected_account["provider_name"])

    selected_provider_name = st.selectbox(
        "Provider Performing This Visit",
        provider_names,
        index=default_provider_index,
        key="visit_setup_provider",
    )

    selected_provider = next(
        p for p in providers if p["provider_name"] == selected_provider_name
    )

    account_id = selected_account.get("account_id", "")
    visit_history = _load_visit_history(str(account_id))
    latest_visit = visit_history[-1] if visit_history else None

    visit_type = "Follow-Up Visit" if latest_visit else "First Visit"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Visit Type", visit_type)
    with c2:
        st.metric("Account ID", str(account_id))
    with c3:
        st.metric("Assigned Provider", selected_provider["provider_name"])

    if not latest_visit:
        st.info("No prior visits on record — this will be treated as a first visit.")

    return {
        "selected_account": selected_account,
        "selected_provider": selected_provider,
        "latest_visit": latest_visit,
        "visit_type": visit_type,
    }


def _safe_index(options: list[str], value: str, fallback: int = 0) -> int:
    try:
        return options.index(value)
    except ValueError:
        return fallback


def _build_vision_defaults(detection: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not detection:
        return {
            "water_color_input": "dark_green",
            "surface_algae_level": "heavy",
            "visible_debris_level": "heavy",
            "bottom_visibility": "no",
            "strip_free_chlorine_bucket": "very_low",
            "strip_ph_bucket": "high",
            "strip_alkalinity_bucket": "acceptable",
            "strip_cya_bucket": "unclear",
            "strip_confidence": "medium",
            "vision_reasoning_summary": "",
        }

    return {
        "water_color_input": detection.get("pool_condition", "unknown"),
        "surface_algae_level": detection.get("surface_algae_level", "unknown"),
        "visible_debris_level": detection.get("visible_debris_level", "unknown"),
        "bottom_visibility": detection.get("bottom_visibility", "unknown"),
        "strip_free_chlorine_bucket": detection.get("free_chlorine_bucket", "unknown"),
        "strip_ph_bucket": detection.get("ph_bucket", "unknown"),
        "strip_alkalinity_bucket": detection.get("alkalinity_bucket", "unknown"),
        "strip_cya_bucket": detection.get("cya_bucket", "unknown"),
        "strip_confidence": detection.get("strip_confidence", "low"),
        "vision_reasoning_summary": detection.get("reasoning_summary", ""),
    }


def render_summary_cards(final_result: Dict[str, Any]) -> None:
    a, b, c, d = st.columns(4)
    a.metric("Mode", str(final_result.get("ai_primary_mode", "")).replace("_", " ").title())
    b.metric("Severity", final_result.get("ai_severity", ""))
    c.metric("Progress", str(final_result.get("rules_progress_status", "")).replace("_", " ").title())
    d.metric("Escalation", "Yes" if final_result.get("rules_escalation_flag") else "No")

def render_bullets(title: str, items: list[str]) -> None:
    if not items:
        return

    st.markdown(f"### {title}")

    for item in items:
        # STEP HEADER
        if item.lower().startswith("step"):
            st.markdown(f"<br><b style='font-size:18px'>{item}</b>", unsafe_allow_html=True)
        
        # DOSING LINE (arrow)
        elif item.startswith("→"):
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{item}", unsafe_allow_html=True)

        # NORMAL INSTRUCTION
        else:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• {item}", unsafe_allow_html=True)

def run_image_detection_ui() -> Optional[Dict[str, Any]]:
    st.subheader("📸 Read Photos")
    st.caption("Snap the pool and test strip — we'll fill in the fields for you.")

    col1, col2 = st.columns(2)

    with col1:
        pool_photo = st.file_uploader(
            "Pool Photo",
            type=["jpg", "jpeg", "png", "webp"],
            key="vision_pool_photo",
        )

    with col2:
        strip_photo = st.file_uploader(
            "Test Strip Photo (Optional)",
            type=["jpg", "jpeg", "png", "webp"],
            key="vision_strip_photo",
        )

    analyze_clicked = st.button("📷 Read Photos", use_container_width=True)

    if analyze_clicked:
        if not pool_photo:
            st.error("Please upload at least a pool photo.")
        elif OpenAI is None:
            st.error("The openai package is not installed. Run: pip install openai")
        else:
            try:
                with st.spinner("Analyzing photos..."):
                    client = OpenAI()
                    detection = analyze_pool_images(
                        pool_image_bytes=pool_photo.getvalue(),
                        pool_filename=pool_photo.name,
                        strip_image_bytes=strip_photo.getvalue() if strip_photo else None,
                        strip_filename=strip_photo.name if strip_photo else None,
                        client=client,
                    )
                st.session_state["vision_result"] = detection
                _prepopulate_form_from_detection(detection)
            except Exception as e:
                st.error(f"Photo read failed — tap the button again to retry. ({e})")

    detection = st.session_state.get("vision_result")
    if detection:
        if detection.get("strip_confidence") == "low":
            st.warning("⚠️ Strip confidence is low — double-check the chemistry fields before submitting.")

        reasoning = detection.get("reasoning_summary", "")
        if reasoning:
            st.info(f"📸 AI read your photos: {reasoning}")

    return detection


def _prepopulate_form_from_detection(detection: Dict[str, Any]) -> None:
    """
    Set form widget session state to friendly label strings from detection results.
    Must be called BEFORE the form renders so the selectboxes show detected values.
    Streamlit selectboxes store the selected label string in session state — setting
    the key here overrides the index parameter on the next render.
    """
    defs = _build_vision_defaults(detection)
    _slots = {
        "wc_color":  (_WATER_COLOR,   defs["water_color_input"]),
        "wc_debris": (_DEBRIS,        defs["visible_debris_level"]),
        "wc_algae":  (_ALGAE,         defs["surface_algae_level"]),
        "wc_vis":    (_VISIBILITY,    defs["bottom_visibility"]),
        "strip_cl":  (_CHLORINE,      defs["strip_free_chlorine_bucket"]),
        "strip_ph":  (_PH,            defs["strip_ph_bucket"]),
        "strip_alk": (_ALKALINITY,    defs["strip_alkalinity_bucket"]),
        "strip_cya": (_CYA,           defs["strip_cya_bucket"]),
    }
    for widget_key, (mapping, raw_val) in _slots.items():
        label = mapping.get(raw_val, list(mapping.values())[-1])
        st.session_state[widget_key] = label


def _labeled_select(label: str, mapping: Dict[str, str], default_val: str, key: str) -> str:
    """Selectbox with friendly labels that returns the raw internal value."""
    keys = list(mapping.keys())
    labels = list(mapping.values())
    # If session state already holds a value for this key (e.g. from photo prepopulation),
    # don't also pass index= — Streamlit raises a warning when both are set.
    if key in st.session_state:
        chosen = st.selectbox(label, labels, key=key)
    else:
        idx = keys.index(default_val) if default_val in keys else len(keys) - 1
        chosen = st.selectbox(label, labels, index=idx, key=key)
    return keys[labels.index(chosen)]


# Friendly label maps — what the pro sees vs. what the app uses internally
_WATER_COLOR = {
    "clear":        "Clear ✅ — looks great",
    "cloudy_blue":  "Cloudy Blue — hazy but not green",
    "light_green":  "Light Green — starting to turn",
    "dark_green":   "Dark Green — full algae bloom",
    "brown":        "Brown — possible metals/iron",
    "rusty":        "Rusty / Orange — likely iron",
    "tea_colored":  "Tea-Colored — tannins or metals",
    "unknown":      "Not sure",
}
_CHLORINE = {
    "very_low":   "Very Low  (0–1 ppm) 🔴",
    "low":        "Low  (1–2 ppm) 🟡",
    "acceptable": "Good  (2–4 ppm) 🟢",
    "high":       "High  (4+ ppm)",
    "unknown":    "Didn't test / Unknown",
}
_PH = {
    "low":        "Low  (below 7.2)",
    "acceptable": "Good  (7.2–7.6) 🟢",
    "high":       "High  (7.6–8.0) 🟡",
    "very_high":  "Very High  (above 8.0) 🔴",
    "unknown":    "Didn't test / Unknown",
}
_ALKALINITY = {
    "low":        "Low  (below 80 ppm)",
    "acceptable": "Good  (80–120 ppm) 🟢",
    "high":       "High  (above 120 ppm)",
    "unknown":    "Didn't test / Unknown",
}
_CYA = {
    "low":        "Low  (below 30 ppm)",
    "acceptable": "Good  (30–80 ppm) 🟢",
    "high":       "High  (above 80 ppm)",
    "unclear":    "Hard to read on the strip",
    "unknown":    "Didn't test / Unknown",
}
_DEBRIS = {
    "none":    "None",
    "light":   "Light — a few leaves or debris",
    "heavy":   "Heavy — lots of debris",
    "unknown": "Unknown",
}
_ALGAE = {
    "none":     "None",
    "light":    "Light — some green spots",
    "moderate": "Moderate — algae visible on surfaces",
    "heavy":    "Heavy — walls and floor covered",
    "unknown":  "Unknown",
}
_VISIBILITY = {
    "yes":     "Yes — can see the bottom clearly",
    "partial": "Partial — bottom is faint/hazy",
    "no":      "No — can't see the bottom at all",
    "unknown": "Unknown",
}
_POOL_SIZE = {
    "small":  "Small  (~10,000 gal)",
    "medium": "Medium  (~18,000 gal)",
    "large":  "Large  (~28,000 gal)",
}
_FILTER = {
    "cartridge": "Cartridge",
    "sand":      "Sand",
    "DE":        "DE (Diatomaceous Earth)",
    "unknown":   "Unknown",
}
_WATER_SOURCE = {
    "municipal": "City / Municipal water",
    "well":      "Well water",
    "unknown":   "Unknown",
}


def build_visit_payload(
    detection: Optional[Dict[str, Any]] = None,
    selected_account: Optional[Dict[str, Any]] = None,
    selected_provider: Optional[Dict[str, Any]] = None,
    latest_visit: Optional[Dict[str, Any]] = None,
    visit_type: str = "First Visit",
) -> Dict[str, Any]:
    defaults = _build_vision_defaults(detection)

    # ── Account banner (outside the form, read-only) ─────────────────────────
    acct = selected_account or {}
    prov = selected_provider or {}
    visit_date_default = datetime.now().date()

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Customer", acct.get("customer_name", "—"))
    b2.metric("Provider", prov.get("provider_name", "—"))
    b3.metric("Visit Type", visit_type)
    b4.metric("Account", acct.get("account_id", "—"))

    if latest_visit:
        # Field names differ between demo data and sheet-loaded visits.
        # Also handle sheet rows saved before header row was initialized
        # (in that case all keys are numeric indices or data-values from row 1).
        summary = (
            latest_visit.get("last_plan_summary")
            or latest_visit.get("ai_today_priority")
            or ""
        )
        expected = (
            latest_visit.get("expected_next_result")
            or latest_visit.get("ai_expected_result_next_visit")
            or ""
        )
        # Sheet may store lists as strings; clean up if needed
        if isinstance(expected, list):
            expected = " | ".join(expected)
        # Fallback: if summary/expected are empty, show mode + progress info
        if not summary:
            mode_raw = latest_visit.get("ai_primary_mode", "")
            progress_raw = latest_visit.get("rules_progress_status", "")
            if mode_raw:
                summary = f"Mode: {mode_raw.replace('_', ' ').title()}"
                if progress_raw:
                    summary += f" — {progress_raw.replace('_', ' ')}"
            else:
                summary = "Visit logged — details will appear on the next follow-up."
        if not expected:
            expected = "Upload new photos next visit for updated recommendations."
        visit_date = latest_visit.get("visit_date", "")
        st.info(
            f"**Last visit {visit_date}:** {summary}  \n"
            f"**Expected today:** {expected}"
        )

    if detection:
        st.success("📸 Fields filled from your photos — adjust anything that looks off.")

    # ── FORM ─────────────────────────────────────────────────────────────────
    with st.form("visit_form"):

        visit_date = st.date_input("Visit Date", value=visit_date_default)

        # ── SECTION 1: What does the pool look like today? ───────────────────
        st.markdown("---")
        st.markdown("### 🌊 Pool Condition")

        s1c1, s1c2 = st.columns(2)
        with s1c1:
            water_color_input = _labeled_select(
                "Water Color",
                _WATER_COLOR,
                defaults["water_color_input"],
                "wc_color",
            )
            visible_debris_level = _labeled_select(
                "Debris on bottom / floating",
                _DEBRIS,
                defaults["visible_debris_level"],
                "wc_debris",
            )
        with s1c2:
            surface_algae_level = _labeled_select(
                "Algae visible on surfaces",
                _ALGAE,
                defaults["surface_algae_level"],
                "wc_algae",
            )
            bottom_visibility = _labeled_select(
                "Can you see the bottom?",
                _VISIBILITY,
                defaults["bottom_visibility"],
                "wc_vis",
            )

        pump_running_input = st.selectbox(
            "Is the pump running?",
            ["yes", "no", "unknown"],
            index=0,
            key="pump_running",
        )

        # ── SECTION 2: Test Strip Results ────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🧪 Test Strip")
        st.caption("Select the closest match for each reading.")

        s2c1, s2c2 = st.columns(2)
        with s2c1:
            strip_free_chlorine_bucket = _labeled_select(
                "Free Chlorine",
                _CHLORINE,
                defaults["strip_free_chlorine_bucket"],
                "strip_cl",
            )
            strip_alkalinity_bucket = _labeled_select(
                "Alkalinity (TA)",
                _ALKALINITY,
                defaults["strip_alkalinity_bucket"],
                "strip_alk",
            )
        with s2c2:
            strip_ph_bucket = _labeled_select(
                "pH",
                _PH,
                defaults["strip_ph_bucket"],
                "strip_ph",
            )
            strip_cya_bucket = _labeled_select(
                "Stabilizer (CYA / Sunscreen)",
                _CYA,
                defaults["strip_cya_bucket"],
                "strip_cya",
            )

        strip_confidence = st.select_slider(
            "How confident are you in this strip reading?",
            options=["low", "medium", "high"],
            value=defaults.get("strip_confidence", "medium"),
        )

        # ── SECTION 3: Pool Details (collapsed) — affects plan output ────────
        with st.expander("⚙️ Pool Details", expanded=False):
            st.caption("Affects chemical amounts — update if different from the defaults.")
            pd1, pd2 = st.columns(2)
            with pd1:
                pool_size_bucket = _labeled_select("Pool Size", _POOL_SIZE, "medium", "ps_size")
                estimated_gallons = st.number_input("Estimated Gallons", min_value=0, value=15000, step=1000)
                pool_type = st.selectbox("Pool Type", ["in_ground", "above_ground"],
                                         format_func=lambda x: "In-Ground" if x == "in_ground" else "Above-Ground")
                pool_shape = st.selectbox("Pool Shape", ["rectangle", "kidney", "freeform", "other"],
                                          format_func=str.title)
            with pd2:
                filter_type   = _labeled_select("Filter Type", _FILTER, "cartridge", "pd_filter")
                water_source  = _labeled_select("Water Source", _WATER_SOURCE, "unknown", "pd_wsrc")
                water_level   = st.selectbox("Water Level", ["low", "normal", "high"],
                                             index=1, format_func=str.title)
                recent_fill_flag           = st.checkbox("Pool was recently filled")
                filled_with_well_water_flag = st.checkbox("Well water was used")
                chlorine_added_before_photo = st.checkbox("Chlorine was already added before this photo")

        submitted = st.form_submit_button("⚡ Calculate Dose", use_container_width=True, type="primary")

        # Checklist & notes defaults — collected on results page instead
        checklist_debris_removed = checklist_pool_brushed = False
        checklist_filter_cleaned = checklist_chemicals_added = False
        checklist_pump_running = checklist_before_after_photos = False
        vacuumed_bottom_today = can_vacuum_to_waste = False
        visit_notes = ""
        closeup_photo = strip_chart_photo = None

        # Last visit defaults
        chlorine_added_last_visit = ph_adjuster_added_last_visit = False
        alkalinity_adjuster_added_last_visit = metal_treatment_last_visit = False
        brushed_last_visit = filter_cleaned_last_visit = False
        pump_left_running_last_visit = "unknown"
        vacuumed_to_waste_last_visit = "not possible"
        chlorine_added_last_visit_notes = ""
        ph_adjuster_notes = ""
        alkalinity_adjuster_notes = ""
        metal_treatment_notes = ""

    if not submitted:
        return {}

    vision_result = detection or st.session_state.get("vision_result") or {}

    pool_photo_obj = st.session_state.get("vision_pool_photo")
    strip_photo_obj = st.session_state.get("vision_strip_photo")

    return {
        "visit_id": f"VIS-{int(datetime.now().timestamp())}",
        "account_id": acct.get("account_id", ""),
        "customer_name": acct.get("customer_name", ""),
        "provider_id": prov.get("provider_id", ""),
        "provider_name": prov.get("provider_name", ""),
        "visit_type": visit_type,
        "visit_date": str(visit_date),
        "visit_timestamp": now_iso(),
        "pool_photo_url": pool_photo_obj.name if pool_photo_obj else "",
        "closeup_photo_url": closeup_photo.name if closeup_photo else "",
        "test_strip_photo_url": strip_photo_obj.name if strip_photo_obj else "",
        "strip_chart_photo_url": strip_chart_photo.name if strip_chart_photo else "",
        "pool_type": pool_type,
        "pool_shape": pool_shape,
        "pool_size_bucket": pool_size_bucket,
        "estimated_gallons": estimated_gallons,
        "water_source": water_source,
        "water_level": water_level,
        "filter_type": filter_type,
        "pump_running_input": pump_running_input,
        "visible_debris_level": visible_debris_level,
        "surface_algae_level": surface_algae_level,
        "water_color_input": water_color_input,
        "bottom_visibility": bottom_visibility,
        "recent_fill_flag": recent_fill_flag,
        "filled_with_well_water_flag": filled_with_well_water_flag,
        "chlorine_added_before_photo": chlorine_added_before_photo,
        "can_vacuum_to_waste": can_vacuum_to_waste,
        "vacuumed_bottom_today": vacuumed_bottom_today,
        "chlorine_added_last_visit": chlorine_added_last_visit,
        "chlorine_added_last_visit_notes": chlorine_added_last_visit_notes,
        "ph_adjuster_added_last_visit": ph_adjuster_added_last_visit,
        "ph_adjuster_notes": ph_adjuster_notes,
        "alkalinity_adjuster_added_last_visit": alkalinity_adjuster_added_last_visit,
        "alkalinity_adjuster_notes": alkalinity_adjuster_notes,
        "metal_treatment_last_visit": metal_treatment_last_visit,
        "metal_treatment_notes": metal_treatment_notes,
        "brushed_last_visit": brushed_last_visit,
        "filter_cleaned_last_visit": filter_cleaned_last_visit,
        "vacuumed_to_waste_last_visit": vacuumed_to_waste_last_visit,
        "pump_left_running_last_visit": pump_left_running_last_visit,
        "strip_free_chlorine_bucket": strip_free_chlorine_bucket,
        "strip_ph_bucket": strip_ph_bucket,
        "strip_alkalinity_bucket": strip_alkalinity_bucket,
        "strip_cya_bucket": strip_cya_bucket,
        "strip_confidence": strip_confidence,
        "checklist_debris_removed": checklist_debris_removed,
        "checklist_pool_brushed": checklist_pool_brushed,
        "checklist_filter_cleaned": checklist_filter_cleaned,
        "checklist_chemicals_added": checklist_chemicals_added,
        "checklist_pump_running": checklist_pump_running,
        "checklist_before_after_photos": checklist_before_after_photos,
        "visit_completed_flag": False,
        "visit_notes": visit_notes,
        "vision_result": vision_result,
        "created_at": now_iso(),
    }


def main() -> None:
    st.title("⚡ DoseLogic")
    st.caption("Field Dosing Calculator — Snap a photo, get your plan, copy-paste the customer text. Done in under a minute.")

    import os
    show_debug = os.environ.get("POOL_DEBUG", "").lower() in ("1", "true", "yes")

    allow_field_workarounds = True

    visit_setup = build_visit_setup_section()
    selected_account = visit_setup["selected_account"]
    selected_provider = visit_setup["selected_provider"]
    latest_visit = visit_setup["latest_visit"]
    visit_type = visit_setup["visit_type"]

    detection = run_image_detection_ui()

    visit_data = build_visit_payload(
        detection=detection or st.session_state.get("vision_result"),
        selected_account=selected_account,
        selected_provider=selected_provider,
        latest_visit=latest_visit,
        visit_type=visit_type,
    )

    if visit_data:
        # Fresh form submission — compute and cache results
        account_data = {
            "account_id":       visit_data["account_id"],
            "customer_name":    visit_data["customer_name"],
            "provider_id":      visit_data["provider_id"],
            "provider_name":    visit_data["provider_name"],
            "recovery_status":  "new_recovery",
            "visits_in_recovery": 0,
            "days_in_recovery": 0,
            "billing_started":  False,
            "billing_start_date": "",
            "current_severity": "",
            "progress_status":  "",
            "escalation_status": "none",
            "escalation_reason": "",
        }
        # Merge any richer account data from the selected account dict
        account_data.update({k: v for k, v in selected_account.items() if v})

        prior_visit: Optional[Dict[str, Any]] = latest_visit

        rules_result = evaluate_visit(visit_data, account_data, prior_visit)
        action_result = build_action_output(visit_data, account_data, rules_result)
        dosing_result = build_dosing_output(
            visit_data,
            account_data,
            rules_result,
            allow_field_workarounds=allow_field_workarounds,
        )

        final_result = merge_dosing_into_action_output(action_result, dosing_result)
        final_result.update(rules_result)

        # Persist so checkbox clicks don't wipe the results
        st.session_state["cached_final_result"] = final_result
        st.session_state["cached_account_data"] = account_data
        st.session_state["cached_visit_data"] = visit_data

    elif "cached_final_result" in st.session_state:
        # Re-run triggered by checkbox — restore from cache
        final_result = st.session_state["cached_final_result"]
        account_data = st.session_state["cached_account_data"]
        visit_data   = st.session_state["cached_visit_data"]

    else:
        st.info("Select the account, fill in the condition, and tap **Calculate Dose**.")
        return

    st.divider()
    st.header("Visit Summary")
    render_summary_cards(final_result)

    mode = final_result.get("ai_primary_mode", "")
    progress = final_result.get("rules_progress_status", "first_visit")
    severity = final_result.get("ai_severity", 1)
    escalation = final_result.get("rules_escalation_flag", False)
    visit_num = account_data.get("visits_in_recovery", 0)

    st.markdown("### 🎯 Focus for This Visit")
    st.success(final_result.get("ai_today_priority", ""))

    _safety_phrases = ("never mix", "add each chemical", "do not add", "wait 15", "wait 30")

    # -----------------------------------------------------------------
    # RECOVERY ROADMAP
    # Show whenever the pool is in any stage of green-pool recovery:
    #   - mode == "sanitize"  (actively green this visit), OR
    #   - mode in {clear, balance} AND visits_done > 0  (progressing through recovery)
    # The current visit always shows the engine's live action plan.
    # Past visits show the static cadence description.
    # Future visits show what's coming.
    # -----------------------------------------------------------------
    visits_done = account_data.get("visits_in_recovery", 0)
    in_recovery = mode == "sanitize" or (mode in {"clear", "balance"} and visits_done > 0)
    action_steps = final_result.get("ai_action_plan", [])

    def _render_action_steps(steps):
        for i, item in enumerate(steps):
            if item.lower().startswith("step") or item.startswith("Progress note"):
                st.markdown(f"<br><b>{item}</b>", unsafe_allow_html=True)
            elif item.startswith("⚠️") or item.startswith("→") or item.lower().startswith(_safety_phrases):
                prefix = "<br>" if item.startswith("⚠️") else ""
                st.markdown(f"{prefix}&nbsp;&nbsp;&nbsp;&nbsp;{item}", unsafe_allow_html=True)
            else:
                st.checkbox(item, key=f"step_{i}")

    if in_recovery:
        st.divider()
        current_visit_num = visits_done + 1
        total_cadence = len(GREEN_POOL_VISIT_CADENCE)
        progress_pct = min(visits_done / total_cadence, 1.0)

        # Headline: which visit + mode context
        mode_label = {"sanitize": "Active Green Recovery", "clear": "Clearing Phase", "balance": "Balance & Finish"}.get(mode, "Recovery")
        st.markdown(f"### 🗓️ Recovery Roadmap — Visit {current_visit_num} · {mode_label}")
        st.progress(progress_pct, text=f"Visit {current_visit_num} of {total_cadence} • {int(progress_pct*100)}% through expected recovery")
        st.caption("Full green pool recovery — 4–7 days when every step is done right. Check off as you go.")

        for cadence_visit in GREEN_POOL_VISIT_CADENCE:
            vnum = cadence_visit["visit"]
            is_current = (vnum == current_visit_num)
            is_done = (vnum < current_visit_num)

            if is_current:
                label = f"👉 Visit {vnum} — {cadence_visit['label'].split('—',1)[-1].strip()}  ← You Are Here"
            elif is_done:
                label = f"✅ Visit {vnum} — {cadence_visit['label'].split('—',1)[-1].strip()}"
            else:
                label = f"⏳ Visit {vnum} — {cadence_visit['label'].split('—',1)[-1].strip()}"

            with st.expander(label, expanded=is_current):
                st.markdown(f"**Goal:** {cadence_visit['goal']}")

                if is_current and action_steps:
                    st.markdown("**Today's steps — tap as you go:**")
                    _render_action_steps(action_steps)
                else:
                    st.markdown("**Steps:**")
                    for step in cadence_visit["steps"]:
                        st.markdown(f"- {step}")

                st.markdown(f"**What to expect:** {cadence_visit['what_to_expect']}")

        # If we're past the last cadence visit, still show the checklist
        if current_visit_num > total_cadence and action_steps:
            st.markdown(f"#### Visit {current_visit_num} — Extended Recovery")
            st.caption("Pool is taking longer than typical. Keep following the engine's plan.")
            _render_action_steps(action_steps)

    else:
        # Metals mode or first-visit non-recovery: simple checklist
        if action_steps:
            st.markdown("### Checklist")
            st.caption("Tap each step as you go.")
            _render_action_steps(action_steps)

    render_bullets("Chemistry Guidance", final_result.get("ai_chemistry_guidance", []))
    render_bullets("Expected Result by Next Visit", final_result.get("ai_expected_result_next_visit", []))

    field_workaround = final_result.get("ai_field_workaround", [])
    if field_workaround:
        render_bullets("Field Workaround", field_workaround)

    # -----------------------------------------------------------------
    # VISIT NOTES + PHOTOS
    # -----------------------------------------------------------------
    st.divider()
    st.markdown("### 📝 Visit Notes & Photos")
    st.session_state.setdefault("visit_notes_post", "")
    st.text_area(
        "Anything unusual, observations, or questions from this visit",
        height=80,
        key="visit_notes_post",
    )
    vn1, vn2 = st.columns(2)
    with vn1:
        st.file_uploader("Close-up Photo (optional)", type=["jpg", "jpeg", "png"], key="closeup_photo_post")
    with vn2:
        st.file_uploader("Strip Chart Photo (optional)", type=["jpg", "jpeg", "png"], key="strip_chart_post")

    # -----------------------------------------------------------------
    # CUSTOMER TEXT — copy-paste ready
    # -----------------------------------------------------------------
    st.divider()
    st.markdown("### 📱 Ready-to-Send Customer Text")

    sms_data = get_customer_sms(mode, progress, severity, escalation, visit_num)
    st.caption(f"**Status:** {sms_data['subject']}")

    col_sms, col_full = st.columns(2)
    with col_sms:
        st.markdown("**Quick SMS / Text Message**")
        sms_text = sms_data["short_sms"]
        if escalation:
            sms_text += " " + escalation_add_on()
        st.text_area("Copy and paste this to the customer:", value=sms_text, height=120, key="sms_note")

    with col_full:
        st.markdown("**Full Service Note**")
        full_text = sms_data["full_note"]
        if escalation:
            full_text += " " + escalation_add_on()
        st.text_area("For internal notes or longer updates:", value=full_text, height=120, key="full_note_area")

    # -----------------------------------------------------------------
    # INTERNAL ESCALATION ALERT
    # -----------------------------------------------------------------
    if final_result.get("rules_escalation_flag"):
        escalation_reason = final_result.get("rules_escalation_reason", "").replace("_", " ")
        st.divider()
        st.error(
            f"🚨 **Internal Flag — Review Required**\n\n"
            f"This visit has been automatically flagged: *{escalation_reason}*\n\n"
            f"This will be logged to the recovery tracker. A supervisor should follow up."
        )

    # -----------------------------------------------------------------
    # GOOGLE SHEET LOGGING
    # -----------------------------------------------------------------
    st.divider()
    st.markdown("### 📊 Log This Visit")
    if st.button("✅ Save to Recovery Tracker", type="primary"):
        action_steps = final_result.get("ai_action_plan", [])
        checked_steps = [
            item for i, item in enumerate(action_steps)
            if st.session_state.get(f"step_{i}", False)
        ]
        checklist = {
            "debris":  any("debris" in s.lower() or "vacuum" in s.lower() for s in checked_steps),
            "brushed": any("brush" in s.lower() for s in checked_steps),
            "filter":  any("filter" in s.lower() or "backwash" in s.lower() for s in checked_steps),
            "chems":   any("chlorine" in s.lower() or "chemical" in s.lower() or "shock" in s.lower() or "acid" in s.lower() for s in checked_steps),
            "pump":    any("pump" in s.lower() for s in checked_steps),
            "photos":  any("photo" in s.lower() for s in checked_steps),
        }
        notes = st.session_state.get("visit_notes_post", "")
        # Read photo bytes from uploaded files (stored in session state by file_uploader)
        pool_photo_file = st.session_state.get("closeup_photo_post")
        strip_photo_file = st.session_state.get("strip_chart_post")
        pool_photo_bytes = pool_photo_file.read() if pool_photo_file else None
        strip_photo_bytes = strip_photo_file.read() if strip_photo_file else None
        success, msg = upsert_recovery_row(
            visit_data, final_result, account_data, checklist, notes,
            pool_photo=pool_photo_bytes, strip_photo=strip_photo_bytes,
        )
        if success:
            st.success(f"✅ {msg}")
        else:
            st.warning(f"⚠️ {msg}")

    # -----------------------------------------------------------------
    # PRO TIPS
    # -----------------------------------------------------------------
    st.divider()
    st.markdown("### 💡 Pro Tips")
    st.caption("Peer knowledge for edge cases — the stuff that isn't in any manual.")

    warning_tips = get_warning_tips_for_mode(mode)
    all_tips = get_tips_for_mode(mode)

    if warning_tips:
        for tip in warning_tips:
            with st.expander(f"⚠️ {tip['title']}", expanded=True):
                st.markdown(tip["body"])
                st.caption(f"*{tip['source']}*")

    non_warning_tips = [t for t in all_tips if not t.get("warning")]
    for tip in non_warning_tips:
        with st.expander(f"💡 {tip['title']}", expanded=False):
            st.markdown(tip["body"])
            st.caption(f"*{tip['source']}*")

    if show_debug:
        with st.expander("Debug: Vision Result"):
            st.code(json.dumps(st.session_state.get("vision_result", {}), indent=2), language="json")
        with st.expander("Debug: Visit Payload"):
            st.code(json.dumps(visit_data, indent=2), language="json")
        with st.expander("Debug: Rules Result"):
            st.code(json.dumps(rules_result, indent=2), language="json")
        with st.expander("Debug: Action Result"):
            st.code(json.dumps(action_result, indent=2), language="json")
        with st.expander("Debug: Dosing Result"):
            st.code(json.dumps(dosing_result, indent=2), language="json")
        with st.expander("Debug: Final Result"):
            st.code(json.dumps(final_result, indent=2), language="json")


if __name__ == "__main__":
    main()