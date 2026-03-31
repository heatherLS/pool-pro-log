from typing import Any, Dict
from reference_dosing import STANDARD_DOSES, green_pool_slam_dose, clarifier_dose, metal_sequestrant_dose, flocculant_dose, algaecide_dose


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


def get_pool_size_bucket(visit: Dict[str, Any]) -> str:
    size = normalize_text(visit.get("pool_size_bucket"))
    if size in {"small", "medium", "large"}:
        return size
    return "medium"


def chlorine_text(pool_size: str, chlorine_bucket: str) -> str:
    """Maintenance chlorine dose for non-green-pool modes."""
    chlorine_bucket = normalize_text(chlorine_bucket)
    # For very low / low FC in balance or clear mode, use a modest top-up
    doses = {
        "very_low": {"small": "Add 1 gallon liquid chlorine (10%).", "medium": "Add 1.5 gallons liquid chlorine (10%).", "large": "Add 2 gallons liquid chlorine (10%)."},
        "low":      {"small": "Add 0.5 gallon liquid chlorine (10%).", "medium": "Add 1 gallon liquid chlorine (10%).", "large": "Add 1.5 gallons liquid chlorine (10%)."},
    }
    return doses.get(chlorine_bucket, {}).get(pool_size, "")


def shock_text(pool_size: str) -> str:
    # Used in sanitize mode — delegate to SLAM dose with unknown CYA
    return STANDARD_DOSES.get("slam_unknown_cya", {}).get(pool_size, "Add shock per pool size (see SLAM dosing).")


def alkalinity_text(pool_size: str) -> str:
    return STANDARD_DOSES.get("alkalinity_low", {}).get(pool_size, "Add 1.5 lbs baking soda (sodium bicarbonate).")


def stabilizer_text(pool_size: str) -> str:
    return STANDARD_DOSES.get("cya_low", {}).get(pool_size, "Add 1.5 lbs granular stabilizer (CYA) in a mesh sock in the skimmer.")


def ph_minus_text(pool_size: str) -> str:
    return STANDARD_DOSES.get("ph_down_high", {}).get(pool_size, "Add muriatic acid to lower pH — check label for your pool size.")


def ph_plus_text(pool_size: str) -> str:
    return STANDARD_DOSES.get("ph_up_low", {}).get(pool_size, "Add soda ash (pH Up) to raise pH — check label for your pool size.")


def build_action_output(
    visit: Dict[str, Any],
    account: Dict[str, Any],
    rules_result: Dict[str, Any],
) -> Dict[str, Any]:

    mode = normalize_text(rules_result.get("ai_primary_mode"))
    progress_status = normalize_text(rules_result.get("rules_progress_status"))
    escalation_flag = as_bool(rules_result.get("rules_escalation_flag"))
    escalation_reason = normalize_text(rules_result.get("rules_escalation_reason"))

    strip_fc = normalize_text(visit.get("strip_free_chlorine_bucket"))
    strip_ph = normalize_text(visit.get("strip_ph_bucket"))
    strip_alk = normalize_text(visit.get("strip_alkalinity_bucket"))
    strip_cya = normalize_text(visit.get("strip_cya_bucket"))

    severity = rules_result.get("ai_severity", 0)

    can_vacuum_to_waste = as_bool(visit.get("can_vacuum_to_waste"))
    vacuumed_bottom_today = as_bool(visit.get("vacuumed_bottom_today"))
    chlorine_added_before_photo = as_bool(visit.get("chlorine_added_before_photo"))
    filled_with_well_water_flag = as_bool(visit.get("filled_with_well_water_flag"))
    recent_fill_flag = as_bool(visit.get("recent_fill_flag"))

    pool_size = get_pool_size_bucket(visit)

    result = {
        "ai_today_priority": "",
        "ai_action_plan": [],
        "ai_safety_notes": [],
        "ai_chemistry_guidance": [],
        "ai_expected_result_next_visit": [],
        "ai_escalate_if": [],
        "ai_field_workaround": [],
        "ai_customer_note": [],
    }

    # =====================================================
    # GREEN / SANITIZE
    # =====================================================
    if mode == "sanitize":
        result["ai_today_priority"] = "Kill algae and remove debris using the exact recovery sequence."

        steps = []
        n = 1  # sequential step counter

        steps.append(f"Step {n} — Remove Debris First")
        n += 1
        if not vacuumed_bottom_today:
            if can_vacuum_to_waste:
                steps.append("Vacuum EVERYTHING from the bottom using vacuum-to-waste.")
            else:
                steps.append("Vacuum EVERYTHING from the bottom slowly. If vacuum-to-waste is not available, expect the filter to need frequent cleaning.")
        steps.append("Skim all floating debris.")
        steps.append("Brush the entire pool (walls, floor, steps, corners).")
        steps.append("Immediately clean or backwash the filter.")

        if strip_ph in {"high", "very_high"}:
            steps.append(f"Step {n} — Lower pH FIRST")
            n += 1
            steps.append(ph_minus_text(pool_size))
            steps.append("→ Wait 30–60 minutes with the pump running before adding anything else.")
        elif strip_ph == "low":
            steps.append(f"Step {n} — Raise pH FIRST")
            n += 1
            steps.append(ph_plus_text(pool_size))
            steps.append("→ Wait 30–60 minutes with the pump running before adding anything else.")

        steps.append(f"Step {n} — Add SLAM Dose")
        n += 1
        slam = STANDARD_DOSES.get(f"slam_{strip_cya}_cya", {}).get(pool_size) or STANDARD_DOSES["slam_unknown_cya"][pool_size]
        steps.append(slam)

        if strip_cya == "low":
            steps.append(f"Step {n} — Add Stabilizer")
            n += 1
            steps.append(stabilizer_text(pool_size))

        steps.append(f"Step {n} — Circulate")
        n += 1
        steps.append("Run the pump continuously for 24 hours.")

        steps.append(f"Step {n} — Filter Maintenance")
        steps.append("Clean or backwash the filter again in 1–2 hours if algae load is heavy.")

        steps.append("⚠️ SAFETY — Never mix chemicals together.")
        steps.append("Add each chemical separately, directly into the pool.")
        steps.append("Never mix chlorine and acid together.")

        result["ai_action_plan"] = steps

        result["ai_chemistry_guidance"] = [
            "Chlorine kills algae.",
            "Shock boosts cleanup during heavy green-pool recovery.",
            "High pH can weaken chlorine performance.",
            "Low stabilizer can make chlorine burn off too quickly.",
            "The biggest reasons green pools stall are skipped vacuuming, skipped filter cleaning, and not enough chlorine.",
        ]

        if chlorine_added_before_photo:
            result["ai_chemistry_guidance"].append(
                "Chlorine was already added before this photo, so review the strip carefully before adding more."
            )

        result["ai_expected_result_next_visit"] = [
            "Water should begin shifting lighter green or toward cloudy blue.",
            "Dead algae may begin settling to the floor.",
            "Filter will likely collect more algae and need cleaning again.",
            "Upload a new pool photo and strip photo next visit for updated steps.",
        ]

        result["ai_escalate_if"] = [
            "Pool remains the same green or darker by next visit.",
            "No visible improvement after 2 visits.",
            "Filter repeatedly clogs with no visible progress.",
            "Pump or circulation appears weak or inconsistent.",
        ]

        result["ai_customer_note"] = [
            "The pool is currently battling algae and low sanitizer.",
            "We are treating it in stages and expect visible improvement over the next 1–2 visits.",
            "If the pump continues running and the filter is cleaned between visits, recovery may move faster.",
        ]

    # =====================================================
    # CLEAR / CLOUDY BLUE
    # =====================================================
    elif mode == "clear":
        result["ai_today_priority"] = "Clear remaining particles and finish the cleanup."

        n = 1
        steps = []

        steps.append(f"Step {n} — Prep the Pool")
        n += 1
        steps.extend([
            "Skim visible debris.",
            "Brush the pool to lift fine material into circulation.",
            "Vacuum settled material if present.",
            "Clean or backwash the filter.",
        ])

        if strip_ph in {"high", "very_high"}:
            steps.append(f"Step {n} — Lower pH FIRST")
            n += 1
            steps.append(ph_minus_text(pool_size))
            steps.append("→ Wait 30–60 minutes with the pump running before adding chlorine or clarifier.")

        if strip_fc in {"very_low", "low"}:
            steps.append(f"Step {n} — Add Chlorine")
            n += 1
            steps.append(chlorine_text(pool_size, strip_fc) or "Add liquid chlorine (10%) for this pool size.")
            steps.append("→ Wait 15–30 minutes after chlorine before adding clarifier.")

        steps.append(f"Step {n} — Add Clarifier")
        n += 1
        steps.append(clarifier_dose(pool_size))

        steps.append(f"Step {n} — Circulate")
        steps.append("Run the pump 8–12 hours or continuously until clarity improves.")


        steps.append("⚠️ SAFETY — Add chemicals separately. Do not mix them together.")

        result["ai_action_plan"] = steps

        result["ai_chemistry_guidance"] = [
            "This phase is mainly about filtration and clarity, not heavy algae killing.",
            "Clarifier helps tiny particles clump together so the filter can catch them.",
            "Do not stack clarifier repeatedly without checking progress.",
        ]

        result["ai_expected_result_next_visit"] = [
            "Water should look clearer and brighter.",
            "Bottom visibility should improve.",
            "Less suspended cloudiness should remain.",
        ]

        result["ai_escalate_if"] = [
            "Pool stays equally cloudy after repeated filtration-focused visits.",
            "Bottom visibility does not improve.",
            "Water starts turning green again.",
        ]

        result["ai_customer_note"] = [
            "The pool is in the clearing phase now.",
            "We are focusing on filtration and fine-particle removal to finish the cleanup.",
        ]

    # =====================================================
    # BALANCE / CLEAR POOL BAD STRIP
    # =====================================================
    elif mode == "balance":
        result["ai_today_priority"] = "Correct chemistry in the proper order without mixing chemicals."

        steps = [
            "Step 1 — Prep the Pool",
            "Skim any debris.",
            "Do a quick brush of the pool walls and steps.",
        ]

        step_number = 2

        # --- pH + Alkalinity conflict resolution ---
        # Muriatic acid lowers BOTH pH and TA. Never prescribe acid twice in one visit.
        ph_needs_acid = strip_ph in {"high", "very_high"}
        ph_needs_base = strip_ph == "low"
        alk_needs_acid = strip_alk == "high"
        alk_needs_base = strip_alk == "low"

        if ph_needs_acid and alk_needs_acid:
            # One acid dose handles both — skip separate TA step
            steps.append(f"Step {step_number} — Lower pH (will also help lower Alkalinity)")
            steps.append("→ Wait 30–60 minutes with the pump running before adding anything else.")
            steps.append("→ Note: muriatic acid lowers both pH and TA — retest both next visit before adding more acid.")
            step_number += 1
            # Mark TA as handled so the step below is skipped
            alk_needs_acid = False

        elif ph_needs_acid and alk_needs_base:
            # Acid for pH, but TA is low — acid will drop TA further. Add bicarb AFTER acid settles.
            steps.append(f"Step {step_number} — Lower pH FIRST")
            steps.append("→ Wait 30–60 minutes with the pump running before adding anything else.")
            step_number += 1
            # TA step will still fire below (bicarb for low TA is safe after acid)

        elif ph_needs_acid:
            steps.append(f"Step {step_number} — Lower pH FIRST")
            steps.append("→ Wait 30–60 minutes with the pump running before adding anything else.")
            step_number += 1

        elif ph_needs_base and alk_needs_acid:
            # Conflict: pH is low (needs soda ash) but TA is high (needs acid). Acid would make pH worse.
            # Fix pH only this visit — note that TA should be rechecked after pH is stable.
            steps.append(f"Step {step_number} — Raise pH FIRST")
            steps.append("→ Wait 30–60 minutes with the pump running before adding anything else.")
            steps.append("→ Note: TA is also high, but do NOT add acid this visit — it will lower pH further. Recheck TA next visit once pH is stable.")
            step_number += 1
            alk_needs_acid = False  # Skip separate TA step

        elif ph_needs_base:
            steps.append(f"Step {step_number} — Raise pH FIRST")
            steps.append("→ Wait 30–60 minutes with the pump running before adding anything else.")
            step_number += 1

        if strip_fc in {"very_low", "low"}:
            steps.append(f"Step {step_number} — Add Chlorine")
            step_number += 1

        if alk_needs_acid:
            steps.append(f"Step {step_number} — Lower Alkalinity")
            steps.append("Note: this acid dose will also nudge pH down slightly — retest pH after.")
            step_number += 1
        elif alk_needs_base:
            steps.append(f"Step {step_number} — Raise Alkalinity")
            step_number += 1

        if strip_cya == "low":
            steps.append(f"Step {step_number} — Add Stabilizer (CYA)")
            step_number += 1
        elif strip_cya == "high":
            steps.append(f"Step {step_number} — Lower Stabilizer (CYA) — Partial Drain Required")
            step_number += 1

        steps.append(f"Step {step_number} — Circulate")
        steps.append("Run the pump 4-6 hours after treatment.")
        step_number += 1

        result["ai_action_plan"] = steps

        result["ai_safety_notes"] = [
            "Never mix chemicals together.",
            "Add each chemical separately directly into the pool.",
            "Always wait 30-60 minutes after pH adjustment before adding chlorine.",
        ]

        guidance = []

        if strip_ph in {"high", "very_high"}:
            guidance.append("High pH weakens chlorine effectiveness.")
        elif strip_ph == "low":
            guidance.append("Low pH should be corrected first.")

        if strip_fc in {"very_low", "low"}:
            guidance.append("Low chlorine means the pool is not properly protected.")

        if strip_alk == "low":
            guidance.append("Low alkalinity causes unstable water chemistry.")
        elif strip_alk == "high":
            guidance.append("High alkalinity can make water harder to balance.")

        if strip_cya == "low":
            guidance.append("Stabilizer is like sunscreen for your chlorine — it helps it last longer in the sun.")
        elif strip_cya == "high":
            if strip_fc in {"very_low", "low"}:
                guidance.append("⚠️ High CYA + low chlorine is a compound problem — chlorine will NOT stabilize until CYA is brought down by draining. Adding more chlorine without draining first is largely wasted effort.")
            else:
                guidance.append("High stabilizer reduces how effective chlorine is, even if the FC reading looks acceptable.")

        result["ai_chemistry_guidance"] = guidance

        result["ai_expected_result_next_visit"] = [
            "Water should remain clear.",
            "Chemistry should begin stabilizing.",
            "Future adjustments should become smaller and more maintenance-focused.",
        ]

        result["ai_escalate_if"] = [
            "Chemistry remains unstable across repeated visits.",
            "The pool begins clouding or discoloring.",
            "Chlorine will not hold after stabilizer is corrected.",
        ]

        result["ai_customer_note"] = [
            "The pool looks clear, but the chemistry needs correction to stay safe and stable.",
            "We are adjusting levels in the proper order to prevent future issues.",
        ]
    # =====================================================
    # METALS
    # =====================================================
    elif mode == "metals":
        result["ai_today_priority"] = "Treat this as a likely metals issue, not a standard algae cleanup."

        steps = [
            "Step 1 — Document the Problem",
            "Take photos of the water color and any visible staining.",
            "Step 2 — Add Metal Treatment",
            metal_sequestrant_dose(pool_size),
        ]

        steps.extend([
            "Step 3 — Circulate",
            "Run the pump continuously for at least 24 hours.",
            "Step 4 — Recheck Next Visit BEFORE Adding Chlorine",
            "Do NOT add shock or high-dose chlorine until water color is reassessed next visit.",
            "⚠️ SAFETY — Adding shock or high chlorine immediately after metal sequestrant can oxidize dissolved metals, causing them to precipitate and permanently stain the pool surface.",
            "⚠️ SAFETY — Do not treat this pool like a standard algae pool. Avoid all shock until metals are under control.",
        ])

        result["ai_action_plan"] = steps

        result["ai_chemistry_guidance"] = [
            "Metal treatment helps bind or control metals in the water.",
            "Recent fill or known well water use makes metals more likely." if (filled_with_well_water_flag or recent_fill_flag) else "Watch for staining or tea-colored water.",
        ]

        result["ai_field_workaround"] = [
            "If approved metal treatment is unavailable, use the approved temporary fine-filtration workaround to trap iron/metals.",
            "Continue circulation and document color improvement closely.",
        ]

        result["ai_expected_result_next_visit"] = [
            "Water should begin looking less brown, rusty, or tea-colored.",
            "Staining patterns should become easier to identify.",
        ]

        result["ai_escalate_if"] = [
            "The same brown, rusty, or tea-colored appearance persists across repeated visits.",
            "Surface staining becomes more obvious or widespread.",
            "Pool does not improve after approved metals treatment steps.",
        ]

        result["ai_customer_note"] = [
            "The pool appears to have a metals-related discoloration issue rather than a normal algae-only problem.",
            "This requires a different treatment path than a standard chlorine cleanup.",
        ]

    # =====================================================
    # FALLBACK
    # =====================================================
    else:
        result["ai_today_priority"] = "Review the pool manually because the visit could not be mapped confidently."
        result["ai_action_plan"] = [
            "Verify the uploaded photo and strip values.",
            "Confirm pool condition manually.",
            "Re-run the analysis after correcting unclear inputs.",
        ]
        result["ai_chemistry_guidance"] = [
            "The current inputs do not support a confident treatment path."
        ]
        result["ai_expected_result_next_visit"] = [
            "A clearer diagnosis should be possible once better inputs are collected."
        ]
        result["ai_escalate_if"] = [
            "Inputs remain unclear or contradictory."
        ]
        result["ai_customer_note"] = [
            "We need a clearer reading before making a safe recommendation."
        ]

    # PROGRESS NOTE
    if progress_status == "stalled":
        result["ai_action_plan"].insert(
            0,
            "Progress note — This pool appears stalled, so follow every step exactly and document the visit carefully."
        )
    elif progress_status == "worse":
        result["ai_action_plan"].insert(
            0,
            "Progress note — This pool appears worse than the prior visit, so verify the previous treatment path was fully completed before repeating it."
        )
    elif progress_status == "improving_well":
        result["ai_action_plan"].insert(
            0,
            "Progress note — Pool is improving, so stay consistent and do not overcorrect what is already working."
        )

    if escalation_flag:
        result["ai_escalate_if"].insert(
            0,
            f"Escalation triggered: {escalation_reason.replace('_', ' ')}"
        )

    return result