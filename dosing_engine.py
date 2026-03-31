from typing import Any, Dict, List
from reference_dosing import STANDARD_DOSES, green_pool_slam_dose, alkalinity_down_dose, clarifier_dose, metal_sequestrant_dose, flocculant_dose, algaecide_dose


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "yes", "y", "1"}


def chlorine_dose_by_bucket(pool_size: str, chlorine_bucket: str, cya_bucket: str = "unknown") -> str:
    """
    Return chlorine dose string for balance/maintenance mode.
    For sanitize/SLAM mode use green_pool_slam_dose() from reference_dosing instead.
    """
    from reference_dosing import liquid_chlorine_gallons
    chlorine_bucket = normalize_text(chlorine_bucket)
    pool_size = normalize_text(pool_size) or "medium"

    if chlorine_bucket == "very_low":
        # Raise FC by ~5 ppm for maintenance recovery
        gals = liquid_chlorine_gallons(pool_size, 5.0, pct=10.0)
        return f"Add {gals:.1f} gallons liquid chlorine (10%) — raises FC ~5 ppm."

    if chlorine_bucket == "low":
        # Raise FC by ~2–3 ppm
        gals = liquid_chlorine_gallons(pool_size, 2.5, pct=10.0)
        return f"Add {gals:.1f} gallons liquid chlorine (10%) — raises FC ~2–3 ppm."

    if chlorine_bucket in {"acceptable", "high"}:
        return "No additional chlorine needed at this time."

    return "Check chlorine level manually and adjust if needed."


DOSING_LIBRARY: Dict[str, Dict[str, Any]] = {
    "sanitize_low_chlorine": {
        "treatment_key": "sanitize_low_chlorine",
        "primary_treatment": {
            "small":  green_pool_slam_dose("small",  "unknown") + " — re-dose every 24–48 hrs until water turns cloudy blue.",
            "medium": green_pool_slam_dose("medium", "unknown") + " — re-dose every 24–48 hrs until water turns cloudy blue.",
            "large":  green_pool_slam_dose("large",  "unknown") + " — re-dose every 24–48 hrs until water turns cloudy blue.",
        },
        "support_treatments": [
            "Vacuum all debris from the bottom first. Use vacuum-to-waste if available.",
            "Skim all floating debris.",
            "Brush the entire pool before adding chemicals.",
            "Immediately after brushing, clean or backwash the filter.",
            "Run the pump continuously for 24 hours.",
            "Clean or backwash the filter again in 1–2 hours if algae load is heavy.",
        ],
        "cautions": [
            "Do not skip vacuuming, brushing, or filter cleaning or the pool may stall.",
            "If pH is very high, chlorine may not work effectively until pH is corrected.",
            "If stabilizer/CYA is low, chlorine may burn off too quickly.",
        ],
    },
    "sanitize_high_ph_then_chlorine": {
        "treatment_key": "sanitize_high_ph_then_chlorine",
        "primary_treatment": {
            "small":  f"{STANDARD_DOSES['ph_down_high']['small']} — WAIT 30–60 minutes before adding chlorine. Then: {green_pool_slam_dose('small', 'unknown')}",
            "medium": f"{STANDARD_DOSES['ph_down_high']['medium']} — WAIT 30–60 minutes before adding chlorine. Then: {green_pool_slam_dose('medium', 'unknown')}",
            "large":  f"{STANDARD_DOSES['ph_down_high']['large']} — WAIT 30–60 minutes before adding chlorine. Then: {green_pool_slam_dose('large', 'unknown')}",
        },
        "support_treatments": [
            "Vacuum all debris from the bottom first. Use vacuum-to-waste if available.",
            "Skim all floating debris.",
            "Brush the entire pool before adding chemicals.",
            "Immediately after brushing, clean or backwash the filter.",
            "Run the pump continuously for 24 hours.",
        ],
        "cautions": [
            "⚠️ NEVER add chlorine immediately after acid — always wait 30–60 minutes with the pump running first.",
            "Never mix acid and chlorine together or add them back-to-back without circulating between them.",
            "High pH severely reduces chlorine effectiveness — skipping the pH step means the chlorine may do almost nothing.",
        ],
    },
    "sanitize_yellow_out_candidate": {
        "treatment_key": "sanitize_yellow_out_candidate",
        "primary_treatment": {
            "small": "Add 1 gallon liquid chlorine (10%) + Suncoast Yellow Blast, 21 oz, per label.",
            "medium": "Add 2 gallons liquid chlorine (10%) + Suncoast Yellow Blast, 21 oz, per label.",
            "large": "Add 3 gallons liquid chlorine (10%) + Suncoast Yellow Blast, 21 oz, per label.",
        },
        "support_treatments": [
            "Vacuum all debris from the bottom first.",
            "Skim surface debris.",
            "Brush entire pool aggressively.",
            "Clean or backwash filter immediately after brushing.",
            "Run pump continuously for 24 hours.",
            "Clean filter again in 1–2 hours if heavy load appears.",
        ],
        "cautions": [
            "Use only for suspected mustard/yellow algae cases.",
            "Do not use this as the default for every green pool.",
            "If pH is above 7.6, correct it FIRST before adding chlorine — high pH will make the treatment far less effective.",
        ],
    },
    "clear_filtration_only": {
        "treatment_key": "clear_filtration_only",
        "primary_treatment": {
            "small": "If chlorine is low, add ½–1 gallon liquid chlorine (10%).",
            "medium": "If chlorine is low, add 1 gallon liquid chlorine (10%).",
            "large": "If chlorine is low, add 1–2 gallons liquid chlorine (10%).",
        },
        "support_treatments": [
            "Skim visible debris.",
            "Brush the pool to lift fine particles into circulation.",
            "Vacuum settled material if present.",
            "Clean or backwash the filter.",
            "Run the pump for 8–12 hours or continuously until clarity improves.",
        ],
        "cautions": [
            "This phase is mainly about filtration and clarity, not aggressive algae killing.",
            "Do not keep stacking chemicals if the pool is already moving toward clear.",
        ],
    },
    "clear_clarifier_candidate": {
        "treatment_key": "clear_clarifier_candidate",
        "primary_treatment": {
            "small":  f"If chlorine is low, add ½–1 gallon liquid chlorine (10%). Then: {clarifier_dose('small')}",
            "medium": f"If chlorine is low, add 1 gallon liquid chlorine (10%). Then: {clarifier_dose('medium')}",
            "large":  f"If chlorine is low, add 1–2 gallons liquid chlorine (10%). Then: {clarifier_dose('large')}",
        },
        "support_treatments": [
            "Skim visible debris.",
            "Brush the pool before adding clarifier.",
            "Run the pump continuously or at least 8–12 hours after clarifier is added.",
            "Clean the filter after 6–12 hours if pressure rises or flow drops.",
        ],
        "cautions": [
            "Use clarifier only for cloudy-blue water, not an actively green pool.",
            "Do not repeatedly stack clarifier day after day without checking progress.",
        ],
    },
    "balance_chlorine_low": {
        "treatment_key": "balance_chlorine_low",
        "primary_treatment": {
            "small": "Very low chlorine: add 1 gallon liquid chlorine (10%). Low chlorine: add ½–1 gallon liquid chlorine (10%).",
            "medium": "Very low chlorine: add 1 gallon liquid chlorine (10%). Low chlorine: add ½–1 gallon liquid chlorine (10%).",
            "large": "Very low chlorine: add 2 gallons liquid chlorine (10%). Low chlorine: add 1 gallon liquid chlorine (10%).",
        },
        "support_treatments": [
            "Skim light debris.",
            "Do a quick brush of walls and steps.",
            "Run the pump 4–6 hours after treatment.",
        ],
        "cautions": [
            "Do not assume clear water means chlorine is acceptable.",
        ],
    },
    "balance_alkalinity_low": {
        "treatment_key": "balance_alkalinity_low",
        "primary_treatment": {
            "small":  STANDARD_DOSES["alkalinity_low"]["small"],
            "medium": STANDARD_DOSES["alkalinity_low"]["medium"],
            "large":  STANDARD_DOSES["alkalinity_low"]["large"],
        },
        "support_treatments": [
            "Run the pump 4–6 hours after treatment.",
        ],
        "cautions": [
            "Alkalinity increaser helps stabilize water balance.",
            "Retest next visit before adding more.",
        ],
    },
    "balance_alkalinity_high": {
        "treatment_key": "balance_alkalinity_high",
        "primary_treatment": {
            "small":  STANDARD_DOSES["alkalinity_high"]["small"],
            "medium": STANDARD_DOSES["alkalinity_high"]["medium"],
            "large":  STANDARD_DOSES["alkalinity_high"]["large"],
        },
        "support_treatments": [
            "Run the pump 4–6 hours after treatment.",
        ],
        "cautions": [
            "Check pH first. High alkalinity often overlaps with pH issues.",
            "Retest before making more chemistry changes.",
        ],
    },
    "balance_ph_low": {
        "treatment_key": "balance_ph_low",
        "primary_treatment": {
            "small":  STANDARD_DOSES["ph_up_low"]["small"],
            "medium": STANDARD_DOSES["ph_up_low"]["medium"],
            "large":  STANDARD_DOSES["ph_up_low"]["large"],
        },
        "support_treatments": [
            "Run the pump 4–6 hours after treatment.",
        ],
        "cautions": [
            "pH Plus raises pH when it is too low.",
            "Retest next visit before adding more.",
        ],
    },
    "balance_ph_high": {
        "treatment_key": "balance_ph_high",
        "primary_treatment": {
            "small":  STANDARD_DOSES["ph_down_high"]["small"],
            "medium": STANDARD_DOSES["ph_down_high"]["medium"],
            "large":  STANDARD_DOSES["ph_down_high"]["large"],
        },
        "support_treatments": [
            "Run the pump 4–6 hours after treatment.",
        ],
        "cautions": [
            "Add acid separately and follow product-label safety directions.",
            "Never mix acid with chlorine or other pool chemicals.",
            "Retest next visit before adding more.",
        ],
    },
    "balance_cya_low": {
        "treatment_key": "balance_cya_low",
        "primary_treatment": {
            "small":  STANDARD_DOSES["cya_low"]["small"],
            "medium": STANDARD_DOSES["cya_low"]["medium"],
            "large":  STANDARD_DOSES["cya_low"]["large"],
        },
        "support_treatments": [
            "Run the pump 4–6 hours after treatment.",
        ],
        "cautions": [
            "Stabilizer is like sunscreen for your chlorine — it protects it from burning off too quickly in the sun.",
            "Low stabilizer can make chlorine feel useless because it burns off too quickly.",
        ],
    },
    "balance_cya_high": {
        "treatment_key": "balance_cya_high",
        "primary_treatment": {
            "small":  "Drain ~3,000 gallons (about 1/3 of pool) and refill with fresh water to dilute CYA. Do NOT add any more stabilizer.",
            "medium": "Drain ~6,000 gallons (about 1/3 of pool) and refill with fresh water to dilute CYA. Do NOT add any more stabilizer.",
            "large":  "Drain ~9,000 gallons (about 1/3 of pool) and refill with fresh water to dilute CYA. Do NOT add any more stabilizer.",
        },
        "support_treatments": [
            "Retest CYA after refill — one partial drain typically drops CYA by 30–40%.",
            "If CYA is still high after one drain, repeat with another partial drain on the next visit.",
            "Do not add any CYA or stabilizer products until level is confirmed below 80 ppm.",
        ],
        "cautions": [
            "CYA cannot be chemically removed — dilution by draining is the only fix.",
            "High CYA (above 80–100 ppm) makes chlorine far less effective, even if the FC reading looks fine.",
            "Never drain more than 1/3 at a time — draining too much can damage vinyl liners or cause hydrostatic pressure issues.",
        ],
    },
    "metals_standard": {
        "treatment_key": "metals_standard",
        "primary_treatment": {
            "small":  metal_sequestrant_dose("small"),
            "medium": metal_sequestrant_dose("medium"),
            "large":  metal_sequestrant_dose("large"),
        },
        "support_treatments": [
            "Run the pump continuously.",
            "Monitor whether discoloration is in the water only or also on pool surfaces.",
        ],
        "cautions": [
            "Do not treat this exactly like a normal algae pool.",
            "High chlorine can worsen metal staining if not handled correctly.",
        ],
    },
    "clear_flocculant_candidate": {
        "treatment_key": "clear_flocculant_candidate",
        "primary_treatment": {
            "small":  flocculant_dose("small"),
            "medium": flocculant_dose("medium"),
            "large":  flocculant_dose("large"),
        },
        "support_treatments": [
            "Skim visible debris before adding flocculant.",
            "Run the pump for 2 hours after adding flocculant, then turn OFF the pump.",
            "Allow 8–24 hours for particles to fully settle to the bottom.",
            "Vacuum ALL settled material to WASTE — absolutely do NOT run it through the filter.",
            "After vacuuming, turn the pump back on and check clarity.",
        ],
        "cautions": [
            "Do NOT use flocculant if vacuum-to-waste is unavailable — particles will recirculate and re-cloud.",
            "Do not add chemicals while pump is off during the settling period.",
            "This is a one-time deep-clear step — do not repeat until clarity is assessed first.",
        ],
    },
    "clear_algaecide_maintenance": {
        "treatment_key": "clear_algaecide_maintenance",
        "primary_treatment": {
            "small":  algaecide_dose("small"),
            "medium": algaecide_dose("medium"),
            "large":  algaecide_dose("large"),
        },
        "support_treatments": [
            "Ensure chlorine is at normal maintenance levels before adding algaecide.",
            "Run the pump for at least 4–6 hours after adding algaecide.",
        ],
        "cautions": [
            "Use ONLY polyquat 60% — quat-based algaecides foam and create a bigger mess.",
            "Algaecide prevents algae from returning — it is not a substitute for chlorine.",
            "Do not use this during active green-pool recovery — wait until water is clear.",
        ],
    },
    "metals_field_workaround": {
        "treatment_key": "metals_field_workaround",
        "primary_treatment": {
            "small": "Use temporary fine-filtration (cotton/polyfill bucket method) to trap iron.",
            "medium": "Use temporary fine-filtration (cotton/polyfill bucket method) to trap iron.",
            "large": "Use temporary fine-filtration (cotton/polyfill bucket method) to trap iron.",
        },
        "support_treatments": [
            "Run water through the filter setup continuously.",
            "Check and replace or clean the material as it collects iron.",
            "Continue until water visibly clears.",
        ],
        "cautions": [
            "Use only if metal treatment is unavailable or as an approved backup workaround.",
            "This is a temporary workaround, not a permanent fix.",
        ],
    },
}


def get_pool_size_bucket(visit: Dict[str, Any]) -> str:
    size_bucket = normalize_text(visit.get("pool_size_bucket"))
    if size_bucket in {"small", "medium", "large"}:
        return size_bucket
    return "medium"


def get_treatment_record(treatment_key: str) -> Dict[str, Any]:
    return DOSING_LIBRARY.get(treatment_key, {})


def should_use_yellow_out_path(visit: Dict[str, Any], rules_result: Dict[str, Any]) -> bool:
    mode = normalize_text(rules_result.get("ai_primary_mode"))
    blocker = normalize_text(rules_result.get("rules_main_blocker"))
    notes = normalize_text(visit.get("visit_notes"))
    water_color = normalize_text(visit.get("water_color_input"))

    if mode != "sanitize":
        return False

    possible_keywords = ["yellow algae", "mustard algae", "yellow out"]
    keyword_match = any(k in notes for k in possible_keywords)

    return keyword_match and water_color in {"light_green", "dark_green"} and blocker in {
        "insufficient_chlorine",
        "active_algae_recovery",
        "process_compliance_failure",
    }


def should_use_clarifier_path(visit: Dict[str, Any], rules_result: Dict[str, Any]) -> bool:
    mode = normalize_text(rules_result.get("ai_primary_mode"))
    blocker = normalize_text(rules_result.get("rules_main_blocker"))
    chlorine = normalize_text(visit.get("strip_free_chlorine_bucket"))
    water_color = normalize_text(visit.get("water_color_input"))

    if mode != "clear":
        return False

    return (
        water_color == "cloudy_blue"
        and blocker in {"filtration_and_particle_removal", "dirty_filter", "dead_algae_not_removed"}
        and chlorine in {"acceptable", "high"}
    )


def should_use_flocculant_path(visit: Dict[str, Any], rules_result: Dict[str, Any]) -> bool:
    """
    Flocculant is appropriate when:
    - Pool is in clear mode (cloudy-blue)
    - Progress is stalled or worse after at least 2 visits
    - Vacuum-to-waste is available (required for flocculant to work)
    """
    mode = normalize_text(rules_result.get("ai_primary_mode"))
    progress = normalize_text(rules_result.get("rules_progress_status"))
    can_vacuum_to_waste = as_bool(visit.get("can_vacuum_to_waste"))
    visits_in_recovery = int(visit.get("visits_in_recovery", 0) or 0)

    if mode != "clear":
        return False
    return (
        can_vacuum_to_waste
        and progress in {"stalled", "worse"}
        and visits_in_recovery >= 2
    )


def should_use_algaecide_maintenance(visit: Dict[str, Any], rules_result: Dict[str, Any]) -> bool:
    """
    Algaecide (polyquat 60%) is appropriate as a prevention dose when:
    - Pool is in clear or balance mode
    - Progress is improving or pool is already clear
    - At least visit 3+ (pool has been through the recovery process)
    """
    mode = normalize_text(rules_result.get("ai_primary_mode"))
    progress = normalize_text(rules_result.get("rules_progress_status"))
    visits_in_recovery = int(visit.get("visits_in_recovery", 0) or 0)

    if mode not in {"clear", "balance"}:
        return False
    return (
        progress in {"improving_well", "resolved"}
        and visits_in_recovery >= 3
    )


def should_use_metals_workaround(
    visit: Dict[str, Any],
    rules_result: Dict[str, Any],
    allow_field_workarounds: bool = True,
) -> bool:
    mode = normalize_text(rules_result.get("ai_primary_mode"))
    if not allow_field_workarounds or mode != "metals":
        return False

    return as_bool(visit.get("filled_with_well_water_flag"))


def _balance_bundle_keys(visit: Dict[str, Any]) -> List[str]:
    keys: List[str] = []

    strip_fc = normalize_text(visit.get("strip_free_chlorine_bucket"))
    strip_ph = normalize_text(visit.get("strip_ph_bucket"))
    strip_alk = normalize_text(visit.get("strip_alkalinity_bucket"))
    strip_cya = normalize_text(visit.get("strip_cya_bucket"))

    if strip_ph == "low":
        keys.append("balance_ph_low")
    elif strip_ph in {"high", "very_high"}:
        keys.append("balance_ph_high")

    if strip_fc in {"very_low", "low"}:
        keys.append("balance_chlorine_low")

    if strip_alk == "low":
        keys.append("balance_alkalinity_low")
    elif strip_alk == "high":
        keys.append("balance_alkalinity_high")

    if strip_cya == "low":
        keys.append("balance_cya_low")
    elif strip_cya == "high":
        keys.append("balance_cya_high")

    return keys


def _build_balance_bundle_output(visit: Dict[str, Any], pool_size_bucket: str) -> Dict[str, Any]:
    strip_fc = normalize_text(visit.get("strip_free_chlorine_bucket"))
    strip_ph = normalize_text(visit.get("strip_ph_bucket"))
    strip_alk = normalize_text(visit.get("strip_alkalinity_bucket"))
    strip_cya = normalize_text(visit.get("strip_cya_bucket"))

    dosing_steps: Dict[str, str] = {}
    support_steps: List[str] = []
    cautions: List[str] = []

    chlorine_instruction = chlorine_dose_by_bucket(pool_size_bucket, strip_fc)
    if "No additional chlorine" not in chlorine_instruction:
        dosing_steps["chlorine"] = chlorine_instruction

    # Muriatic acid lowers BOTH pH and TA. Never prescribe acid for both in one visit.
    ph_needs_acid = strip_ph in {"high", "very_high"}
    ph_needs_base = strip_ph == "low"
    alk_needs_acid = strip_alk == "high"
    alk_needs_base = strip_alk == "low"

    if ph_needs_acid and alk_needs_acid:
        # One acid dose handles both — inject pH dose only, skip TA dose
        dosing_steps["ph"] = DOSING_LIBRARY["balance_ph_high"]["primary_treatment"][pool_size_bucket]
        cautions.append("Muriatic acid lowers both pH AND alkalinity — do NOT add acid again for TA. Retest both next visit.")

    elif ph_needs_base and alk_needs_acid:
        # Conflict: pH low needs soda ash, TA high needs acid. Adding acid would worsen pH.
        # Fix pH only; defer TA correction.
        dosing_steps["ph"] = DOSING_LIBRARY["balance_ph_low"]["primary_treatment"][pool_size_bucket]
        cautions.append("TA is high but do NOT add acid this visit — it would lower pH further. Recheck TA next visit once pH is stable.")

    else:
        if ph_needs_acid:
            dosing_steps["ph"] = DOSING_LIBRARY["balance_ph_high"]["primary_treatment"][pool_size_bucket]
        elif ph_needs_base:
            dosing_steps["ph"] = DOSING_LIBRARY["balance_ph_low"]["primary_treatment"][pool_size_bucket]

        if alk_needs_acid:
            dosing_steps["alkalinity"] = DOSING_LIBRARY["balance_alkalinity_high"]["primary_treatment"][pool_size_bucket]
            cautions.append("This acid dose will also nudge pH down slightly — retest pH after.")
        elif alk_needs_base:
            dosing_steps["alkalinity"] = DOSING_LIBRARY["balance_alkalinity_low"]["primary_treatment"][pool_size_bucket]

    if strip_cya == "low":
        dosing_steps["cya"] = DOSING_LIBRARY["balance_cya_low"]["primary_treatment"][pool_size_bucket]
    elif strip_cya == "high":
        dosing_steps["cya"] = DOSING_LIBRARY["balance_cya_high"]["primary_treatment"][pool_size_bucket]

    support_steps.extend([
        "Skim light debris.",
        "Do a quick brush of the pool walls and steps.",
        "Run the pump 4-6 hours after treatment.",
        "Retest next visit before making more chemistry changes.",
    ])

    cautions.extend([
        "Do not stack unnecessary chemicals if the strip does not call for them.",
        "Correct only what is off.",
    ])

    if strip_cya == "low":
        cautions.append("Low stabilizer can make chlorine burn off too quickly.")
    if strip_ph in {"high", "very_high"}:
        cautions.append("High pH can weaken chlorine performance.")
    if strip_ph == "low":
        cautions.append("Low pH should be corrected before the water becomes irritating or unstable.")

    return {
        "dosing_treatment_key": "balance_bundle",
        "dosing_primary_treatment": "",
        "dosing_step_map": dosing_steps,
        "dosing_support_treatments": support_steps,
        "dosing_cautions": cautions,
        "dosing_optional_workaround": [],
    }

def select_primary_treatment_key(
    visit: Dict[str, Any],
    account: Dict[str, Any],
    rules_result: Dict[str, Any],
) -> str:
    mode = normalize_text(rules_result.get("ai_primary_mode"))
    blocker = normalize_text(rules_result.get("rules_main_blocker"))
    ph = normalize_text(visit.get("strip_ph_bucket"))
    alk = normalize_text(visit.get("strip_alkalinity_bucket"))
    cya = normalize_text(visit.get("strip_cya_bucket"))

    if mode == "sanitize":
        if should_use_yellow_out_path(visit, rules_result):
            return "sanitize_yellow_out_candidate"
        if blocker == "high_ph_reducing_chlorine_effectiveness":
            return "sanitize_high_ph_then_chlorine"
        return "sanitize_low_chlorine"

    if mode == "clear":
        if should_use_flocculant_path(visit, rules_result):
            return "clear_flocculant_candidate"
        if should_use_clarifier_path(visit, rules_result):
            return "clear_clarifier_candidate"
        if should_use_algaecide_maintenance(visit, rules_result):
            return "clear_algaecide_maintenance"
        return "clear_filtration_only"

    if mode == "balance":
        if should_use_algaecide_maintenance(visit, rules_result):
            return "clear_algaecide_maintenance"
        bundle_keys = _balance_bundle_keys(visit)
        if bundle_keys:
            return bundle_keys[0]
        if ph == "low":
            return "balance_ph_low"
        if ph in {"high", "very_high"}:
            return "balance_ph_high"
        if alk == "low":
            return "balance_alkalinity_low"
        if alk == "high":
            return "balance_alkalinity_high"
        if cya == "low":
            return "balance_cya_low"
        if cya == "high":
            return "balance_cya_high"
        return "balance_chlorine_low"

    if mode == "metals":
        return "metals_standard"

    return "clear_filtration_only"


def build_dosing_output(
    visit: Dict[str, Any],
    account: Dict[str, Any],
    rules_result: Dict[str, Any],
    allow_field_workarounds: bool = True,
) -> Dict[str, Any]:
    pool_size_bucket = get_pool_size_bucket(visit)
    mode = normalize_text(rules_result.get("ai_primary_mode"))

    if mode == "balance":
        return _build_balance_bundle_output(visit, pool_size_bucket)

    treatment_key = select_primary_treatment_key(visit, account, rules_result)
    treatment_record = get_treatment_record(treatment_key)

    primary_treatment_text = treatment_record.get("primary_treatment", {}).get(
        pool_size_bucket,
        "Use the approved treatment for this pool size and condition.",
    )

    support_treatments = list(treatment_record.get("support_treatments", []))
    cautions = list(treatment_record.get("cautions", []))

    output = {
        "dosing_treatment_key": treatment_key,
        "dosing_primary_treatment": primary_treatment_text,
        "dosing_support_treatments": support_treatments,
        "dosing_cautions": cautions,
        "dosing_optional_workaround": [],
    }

    if should_use_metals_workaround(visit, rules_result, allow_field_workarounds):
        workaround = get_treatment_record("metals_field_workaround")
        output["dosing_optional_workaround"] = [
            workaround.get("primary_treatment", {}).get(
                pool_size_bucket,
                "Use the approved temporary fine-filtration workaround for suspected metals.",
            ),
            *workaround.get("support_treatments", []),
        ]
        output["dosing_cautions"].extend(workaround.get("cautions", []))

    return output


def merge_dosing_into_action_output(
    action_result: Dict[str, Any],
    dosing_result: Dict[str, Any],
) -> Dict[str, Any]:
    updated = dict(action_result)

    action_plan = list(updated.get("ai_action_plan", []))
    dosing_step_map = dosing_result.get("dosing_step_map", {})
    dosing_text = dosing_result.get("dosing_primary_treatment", "")

    new_plan = []

    for step in action_plan:
        new_plan.append(step)

        step_lower = step.lower()

        if "step" in step_lower and "ph" in step_lower and dosing_step_map.get("ph"):
            new_plan.append(f"-> {dosing_step_map['ph']}")

        elif "step" in step_lower and "chlorine" in step_lower and dosing_step_map.get("chlorine"):
            new_plan.append(f"-> {dosing_step_map['chlorine']}")

        elif "step" in step_lower and "alkalinity" in step_lower and dosing_step_map.get("alkalinity"):
            new_plan.append(f"-> {dosing_step_map['alkalinity']}")

        elif "step" in step_lower and "stabilizer" in step_lower and dosing_step_map.get("cya"):
            new_plan.append(f"-> {dosing_step_map['cya']}")

    updated["ai_action_plan"] = new_plan
    updated["ai_chemistry_guidance"] = []
    updated["dosing_treatment_key"] = dosing_result.get("dosing_treatment_key", "")

    return updated