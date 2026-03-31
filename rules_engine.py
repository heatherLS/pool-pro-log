from typing import Any, Dict, Optional


COLOR_ORDER = {
    "dark_green": 5,
    "light_green": 4,
    "cloudy_blue": 3,
    "clear": 1,
    "brown": 4,
    "rusty": 4,
    "tea_colored": 4,
}

SEVERITY_LABELS = {
    1: "slight_haze_or_clear",
    2: "mild_cloudiness",
    3: "cloudy_blue",
    4: "green_pool",
    5: "swamp_dark_green",
}


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "yes", "y", "1"}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def normalize_water_color(value: Any) -> str:
    v = normalize_text(value)
    mapping = {
        "green": "light_green",
        "light green": "light_green",
        "dark green": "dark_green",
        "swamp": "dark_green",
        "swampy": "dark_green",
        "cloudy blue": "cloudy_blue",
        "blue cloudy": "cloudy_blue",
        "clear": "clear",
        "brown": "brown",
        "rusty": "rusty",
        "tea": "tea_colored",
        "tea colored": "tea_colored",
        "tea-colored": "tea_colored",
    }
    return mapping.get(v, v)


def determine_primary_mode(visit: Dict[str, Any]) -> str:
    water_color = normalize_water_color(visit.get("water_color_input"))
    algae = normalize_text(visit.get("surface_algae_level"))
    well_water = as_bool(visit.get("filled_with_well_water_flag"))

    if water_color in {"brown", "rusty", "tea_colored"} or (well_water and water_color not in {"clear", ""}):
        return "metals"

    if water_color in {"light_green", "dark_green"} or algae in {"moderate", "heavy"}:
        return "sanitize"

    if water_color == "cloudy_blue":
        return "clear"

    return "balance"


def determine_severity(visit: Dict[str, Any]) -> int:
    water_color = normalize_water_color(visit.get("water_color_input"))
    algae = normalize_text(visit.get("surface_algae_level"))
    debris = normalize_text(visit.get("visible_debris_level"))
    bottom_visibility = normalize_text(visit.get("bottom_visibility"))

    if water_color == "dark_green" or (
        algae == "heavy" and bottom_visibility == "no" and debris == "heavy"
    ):
        return 5

    if water_color == "light_green" or (
        algae in {"moderate", "heavy"} and bottom_visibility == "no"
    ):
        return 4

    if water_color == "cloudy_blue" and bottom_visibility == "no":
        return 3

    if water_color == "cloudy_blue" and bottom_visibility == "partial":
        return 2

    return 1


def determine_main_blocker(visit: Dict[str, Any], mode: str, has_prior_visit: bool) -> str:
    debris = normalize_text(visit.get("visible_debris_level"))
    ph = normalize_text(visit.get("strip_ph_bucket"))
    chlorine = normalize_text(visit.get("strip_free_chlorine_bucket"))
    cya = normalize_text(visit.get("strip_cya_bucket"))
    well_water = as_bool(visit.get("filled_with_well_water_flag"))
    pump_running = normalize_text(visit.get("pump_running_input"))
    brushed_last = as_bool(visit.get("brushed_last_visit"))
    filter_cleaned_last = as_bool(visit.get("filter_cleaned_last_visit"))
    vacuumed_last = normalize_text(visit.get("vacuumed_to_waste_last_visit"))
    water_color = normalize_water_color(visit.get("water_color_input"))
    bottom_visibility = normalize_text(visit.get("bottom_visibility"))

    if mode == "sanitize":
        if debris == "heavy":
            return "debris_load"

        if ph in {"high", "very_high"} and chlorine in {"very_low", "low"}:
            return "high_ph_reducing_chlorine_effectiveness"

        if chlorine in {"very_low", "low"}:
            return "insufficient_chlorine"

        if has_prior_visit and (not brushed_last or not filter_cleaned_last):
            return "process_compliance_failure"

        if pump_running in {"no", "unknown"}:
            return "circulation_issue"

        return "active_algae_recovery"

    if mode == "clear":
        if has_prior_visit and not filter_cleaned_last:
            return "dirty_filter"

        if bottom_visibility in {"partial", "no"} and vacuumed_last in {"no", "not possible", ""}:
            return "dead_algae_not_removed"

        if chlorine in {"acceptable", "high"}:
            return "filtration_and_particle_removal"

        return "light_chemical_support_needed"

    if mode == "balance":
        if ph in {"low", "high", "very_high"}:
            return "ph_out_of_range"

        if normalize_text(visit.get("strip_alkalinity_bucket")) in {"low", "high"}:
            return "alkalinity_out_of_range"

        if cya in {"low", "high"}:
            return "stabilizer_out_of_range"

        return "minor_balance_adjustment"

    if mode == "metals":
        if well_water:
            return "likely_well_water_metals"

        if water_color in {"brown", "rusty", "tea_colored"}:
            return "likely_metals_or_staining"

        return "metals_suspected"

    return "unknown"


def determine_progress_status(
    current_visit: Dict[str, Any],
    prior_visit: Optional[Dict[str, Any]],
    current_severity: int,
) -> str:
    if not prior_visit:
        return "first_visit"

    prior_severity = determine_severity(prior_visit)
    current_color = normalize_water_color(current_visit.get("water_color_input"))
    prior_color = normalize_water_color(prior_visit.get("water_color_input"))
    current_bottom = normalize_text(current_visit.get("bottom_visibility"))
    prior_bottom = normalize_text(prior_visit.get("bottom_visibility"))
    current_debris = normalize_text(current_visit.get("visible_debris_level"))
    prior_debris = normalize_text(prior_visit.get("visible_debris_level"))

    if current_severity < prior_severity:
        return "improving_well"

    improved_visibility = (
        prior_bottom == "no" and current_bottom in {"partial", "yes"}
    ) or (
        prior_bottom == "partial" and current_bottom == "yes"
    )

    improved_debris = (
        prior_debris == "heavy" and current_debris in {"light", "none"}
    ) or (
        prior_debris == "light" and current_debris == "none"
    )

    improved_color = COLOR_ORDER.get(current_color, 99) < COLOR_ORDER.get(prior_color, 99)

    if current_severity == prior_severity and (improved_visibility or improved_debris or improved_color):
        return "improving_slowly"

    if current_severity > prior_severity:
        return "worse"

    return "stalled"


def determine_escalation(
    visit: Dict[str, Any],
    account: Dict[str, Any],
    mode: str,
    severity: int,
    progress_status: str,
) -> Dict[str, Any]:
    visits_in_recovery = int(account.get("visits_in_recovery", 0) or 0)
    billing_started = as_bool(account.get("billing_started"))

    debris_done = as_bool(visit.get("checklist_debris_removed"))
    brushed_done = as_bool(visit.get("checklist_pool_brushed"))
    filter_done = as_bool(visit.get("checklist_filter_cleaned"))
    chems_done = as_bool(visit.get("checklist_chemicals_added"))
    pump_done = as_bool(visit.get("checklist_pump_running"))

    compliant_visit = all([debris_done, brushed_done, filter_done, chems_done, pump_done])

    if visits_in_recovery >= 2 and progress_status in {"stalled", "worse"}:
        return {
            "rules_escalation_flag": True,
            "rules_escalation_reason": "no_improvement_after_two_visits",
            "escalation_type": "stalled_recovery",
        }

    if mode == "sanitize" and severity >= 4 and visits_in_recovery >= 2 and compliant_visit and progress_status != "improving_well":
        return {
            "rules_escalation_flag": True,
            "rules_escalation_reason": "severe_green_pool_not_improving_despite_compliance",
            "escalation_type": "stalled_recovery",
        }

    if billing_started and mode in {"sanitize", "clear", "metals"} and progress_status != "improving_well":
        return {
            "rules_escalation_flag": True,
            "rules_escalation_reason": "billing_started_before_recovery_completed",
            "escalation_type": "billing_risk",
        }

    if visits_in_recovery >= 2 and (not brushed_done or not filter_done):
        return {
            "rules_escalation_flag": True,
            "rules_escalation_reason": "repeated_process_failure",
            "escalation_type": "repeated_process_failure",
        }

    if mode == "metals" and visits_in_recovery >= 2 and progress_status in {"stalled", "worse"}:
        return {
            "rules_escalation_flag": True,
            "rules_escalation_reason": "metals_issue_not_resolving",
            "escalation_type": "likely_metals_issue",
        }

    return {
        "rules_escalation_flag": False,
        "rules_escalation_reason": "",
        "escalation_type": "",
    }


def evaluate_visit(
    visit: Dict[str, Any],
    account: Dict[str, Any],
    prior_visit: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    mode = determine_primary_mode(visit)
    severity = determine_severity(visit)
    blocker = determine_main_blocker(visit, mode, has_prior_visit=prior_visit is not None)
    progress_status = determine_progress_status(visit, prior_visit, severity)
    escalation = determine_escalation(visit, account, mode, severity, progress_status)

    return {
        "ai_primary_mode": mode,
        "ai_severity": severity,
        "rules_main_blocker": blocker,
        "rules_progress_status": progress_status,
        **escalation,
    }