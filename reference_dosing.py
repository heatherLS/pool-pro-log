"""
reference_dosing.py

Industry-standard pool chemical dosing constants.
Sources: Trouble Free Pool (TFP), Pinch a Penny, Clorox Pool & Spa, PHTA/ANSI-APSP-11.

All math is based on cross-referenced published data:
  - Liquid chlorine (10%): ~13 fl oz per 10,000 gal raises FC 1 ppm
  - Liquid chlorine (12.5%): ~10.4 fl oz per 10,000 gal raises FC 1 ppm
  - Cal-hypo (68%): ~2 oz dry per 10,000 gal raises FC 1 ppm  → 1 lb bag ≈ +8 ppm in 10k gal
  - Sodium bicarbonate: 1.4 lbs per 10,000 gal raises TA 10 ppm
  - Cyanuric acid (CYA): 13 oz per 10,000 gal raises CYA 10 ppm
  - Muriatic acid (31.45%): 6.4 fl oz per 10,000 gal lowers pH ~0.2
  - Soda ash: 6 oz per 10,000 gal raises pH ~0.2
"""

from typing import Dict, Any

# ---------------------------------------------------------------------------
# Pool size → estimated gallons
# ---------------------------------------------------------------------------
POOL_GALLONS: Dict[str, int] = {
    "small": 10_000,
    "medium": 18_000,
    "large": 28_000,
}

# ---------------------------------------------------------------------------
# Target chemistry ranges (sources noted per parameter)
# ---------------------------------------------------------------------------
TARGET_RANGES: Dict[str, Dict[str, Any]] = {
    "free_chlorine_ppm": {
        "tfp_note": "FC target depends on CYA level — see FC_CYA_TABLE below",
        "clorox": {"min": 1.0, "max": 4.0},
        "pinch_a_penny": {"min": 2.0, "max": 4.0},
        "apsp_min": 1.0,
    },
    "ph": {
        "tfp": {"min": 7.2, "max": 8.0, "ideal_min": 7.4, "ideal_max": 7.6},
        "clorox": {"min": 7.2, "max": 7.6, "ideal": 7.4},
        "pinch_a_penny": {"min": 7.2, "max": 7.8, "ideal": 7.4},
        "apsp": {"min": 7.2, "max": 7.8},
    },
    "total_alkalinity_ppm": {
        "tfp": {"min": 60, "max": 120},
        "clorox": {"min": 80, "max": 125},
        "pinch_a_penny": {"min": 70, "max": 140, "target": 100},
        "apsp": {"min": 60, "max": 180},
    },
    "cya_ppm": {
        "tfp": {"min": 30, "max": 50, "note": "For liquid chlorine pools. SWG pools: 60-80."},
        "pinch_a_penny": {"min": 40, "max": 80, "note": "60-80 recommended for most backyard pools"},
        "apsp_max": 100,
    },
    "calcium_hardness_ppm": {
        "tfp": {"min": 250, "max": 350, "note": "Plaster only. Vinyl/fiberglass: 100+ min"},
        "pinch_a_penny": {"min": 200, "max": 400},
        "apsp": {"min": 150, "max": 1000},
    },
}

# ---------------------------------------------------------------------------
# FC / CYA relationship (TFP methodology)
# Minimum FC = CYA × 0.075   |   Target FC ≈ CYA × 0.115   |   SLAM FC = CYA × 0.40
# ---------------------------------------------------------------------------
FC_CYA_TABLE: Dict[int, Dict[str, float]] = {
    0:   {"min_fc": 0.1,  "target_fc": 0.1,  "slam_fc": 0.6},
    10:  {"min_fc": 0.8,  "target_fc": 1.2,  "slam_fc": 4.5},
    20:  {"min_fc": 1.5,  "target_fc": 2.4,  "slam_fc": 8.3},
    30:  {"min_fc": 2.2,  "target_fc": 3.5,  "slam_fc": 12.0},
    40:  {"min_fc": 2.9,  "target_fc": 4.6,  "slam_fc": 16.0},
    50:  {"min_fc": 3.7,  "target_fc": 5.8,  "slam_fc": 20.0},
    60:  {"min_fc": 4.5,  "target_fc": 7.0,  "slam_fc": 24.0},
    70:  {"min_fc": 5.2,  "target_fc": 8.0,  "slam_fc": 28.0},
    80:  {"min_fc": 6.0,  "target_fc": 9.0,  "slam_fc": 32.0},
    90:  {"min_fc": 6.8,  "target_fc": 10.0, "slam_fc": 36.0},
    100: {"min_fc": 7.5,  "target_fc": 11.0, "slam_fc": 40.0},
}

# ---------------------------------------------------------------------------
# Dosing constants per 10,000 gallons
# ---------------------------------------------------------------------------
DOSING_CONSTANTS = {
    "liquid_chlorine_10pct_oz_per_10k_per_1ppm_fc": 13.0,
    "liquid_chlorine_12_5pct_oz_per_10k_per_1ppm_fc": 10.4,
    "cal_hypo_68pct_oz_dry_per_10k_per_1ppm_fc": 2.0,
    "cal_hypo_1lb_bag_fc_raise_10k_gal": 8.0,     # 1 lb at 68% ≈ +8 ppm FC in 10k gal
    "sodium_bicarb_lbs_per_10k_per_10ppm_ta": 1.4,
    "cya_oz_dry_per_10k_per_10ppm_cya": 13.0,
    "muriatic_acid_31pct_oz_per_10k_per_0_2ph": 6.4,
    "soda_ash_oz_per_10k_per_0_2ph": 6.0,
    "calcium_chloride_77pct_lbs_per_10k_per_10ppm_ch": 1.2,
}


def gallons_for_size(pool_size: str) -> int:
    """Return estimated pool gallons for a size bucket."""
    return POOL_GALLONS.get(pool_size.lower(), POOL_GALLONS["medium"])


def liquid_chlorine_gallons(pool_size: str, target_fc_raise_ppm: float, pct: float = 10.0) -> float:
    """
    Return gallons of liquid chlorine needed to raise FC by target_fc_raise_ppm.
    pct: chlorine concentration (10.0 or 12.5)
    """
    gallons = gallons_for_size(pool_size)
    if pct == 12.5:
        oz_per_10k = DOSING_CONSTANTS["liquid_chlorine_12_5pct_oz_per_10k_per_1ppm_fc"]
    else:
        oz_per_10k = DOSING_CONSTANTS["liquid_chlorine_10pct_oz_per_10k_per_1ppm_fc"]
    total_oz = oz_per_10k * (gallons / 10_000) * target_fc_raise_ppm
    return round(total_oz / 128, 2)  # fl oz → gallons


def shock_bags_needed(pool_size: str, target_fc_raise_ppm: float) -> float:
    """Return number of 1-lb cal-hypo (68%) bags to raise FC by target_fc_raise_ppm."""
    gallons = gallons_for_size(pool_size)
    fc_per_bag = DOSING_CONSTANTS["cal_hypo_1lb_bag_fc_raise_10k_gal"] * (10_000 / gallons)
    return round(target_fc_raise_ppm / fc_per_bag, 1)


def bicarb_lbs(pool_size: str, ta_raise_ppm: float) -> float:
    """Return lbs of sodium bicarbonate to raise TA by ta_raise_ppm."""
    gallons = gallons_for_size(pool_size)
    return round(DOSING_CONSTANTS["sodium_bicarb_lbs_per_10k_per_10ppm_ta"] * (gallons / 10_000) * (ta_raise_ppm / 10), 1)


def cya_ounces(pool_size: str, cya_raise_ppm: float) -> float:
    """Return oz of granular CYA to raise stabilizer by cya_raise_ppm."""
    gallons = gallons_for_size(pool_size)
    return round(DOSING_CONSTANTS["cya_oz_dry_per_10k_per_10ppm_cya"] * (gallons / 10_000) * (cya_raise_ppm / 10), 1)


def muriatic_acid_oz(pool_size: str, ph_lower_by: float) -> float:
    """Return fl oz of muriatic acid (31.45%) to lower pH by ph_lower_by."""
    gallons = gallons_for_size(pool_size)
    return round(DOSING_CONSTANTS["muriatic_acid_31pct_oz_per_10k_per_0_2ph"] * (gallons / 10_000) * (ph_lower_by / 0.2), 1)


def soda_ash_oz(pool_size: str, ph_raise_by: float) -> float:
    """Return oz of soda ash to raise pH by ph_raise_by."""
    gallons = gallons_for_size(pool_size)
    return round(DOSING_CONSTANTS["soda_ash_oz_per_10k_per_0_2ph"] * (gallons / 10_000) * (ph_raise_by / 0.2), 1)


# ---------------------------------------------------------------------------
# Pre-calculated dose strings for common scenarios by pool size
# ---------------------------------------------------------------------------

def _fmt_liquid_cl(gals: float) -> str:
    if gals < 0.5:
        return f"Add {int(gals * 128)} fl oz liquid chlorine (10%)"
    elif gals <= 1.0:
        return f"Add {gals:.1f} gallon liquid chlorine (10%)"
    else:
        return f"Add {gals:.1f} gallons liquid chlorine (10%)"


def green_pool_slam_dose(pool_size: str, cya_bucket: str = "acceptable") -> str:
    """
    Return SLAM-level chlorine dose for a green pool.
    Assumes CYA bucket:
      low       → CYA ~20 ppm → SLAM FC = 8 ppm
      acceptable → CYA ~40 ppm → SLAM FC = 16 ppm
      high      → CYA ~70 ppm → SLAM FC = 28 ppm
      unknown   → assume CYA ~30 ppm → SLAM FC = 12 ppm (conservative)
    """
    cya_map = {"low": 20, "acceptable": 40, "high": 70, "unclear": 30, "unknown": 30}
    cya_ppm = cya_map.get(cya_bucket.lower(), 30)
    slam_fc = cya_ppm * 0.40

    liq_gal = liquid_chlorine_gallons(pool_size, slam_fc, pct=10.0)
    gallons = gallons_for_size(pool_size)
    fc_per_shock_bag = DOSING_CONSTANTS["cal_hypo_1lb_bag_fc_raise_10k_gal"] * (10_000 / gallons)
    shock_bags_low = int(slam_fc / fc_per_shock_bag)
    shock_bags_high = shock_bags_low + 1

    if shock_bags_low == shock_bags_high or shock_bags_low == 0:
        bags_str = f"{shock_bags_high} lb bag(s) cal-hypo shock"
    else:
        bags_str = f"{shock_bags_low}–{shock_bags_high} lb bags cal-hypo shock"

    return (
        f"{_fmt_liquid_cl(liq_gal)} OR {bags_str} "
        f"(targeting FC ≈ {slam_fc:.0f} ppm for CYA ~{cya_ppm} ppm)"
    )


def ph_down_dose(pool_size: str, ph_current: float = 7.8, ph_target: float = 7.4) -> str:
    """Return specific muriatic acid dose to lower pH from current to target."""
    drop = round(ph_current - ph_target, 2)
    if drop <= 0:
        return "No pH adjustment needed."
    oz = muriatic_acid_oz(pool_size, drop)
    return f"Add {oz:.1f} fl oz muriatic acid (31%) to lower pH by {drop:.1f} (from ~{ph_current} to ~{ph_target}). Add slowly near return jets with pump running."


def ph_up_dose(pool_size: str, ph_current: float = 7.0, ph_target: float = 7.4) -> str:
    """Return specific soda ash dose to raise pH from current to target."""
    rise = round(ph_target - ph_current, 2)
    if rise <= 0:
        return "No pH adjustment needed."
    oz = soda_ash_oz(pool_size, rise)
    return f"Add {oz:.1f} oz soda ash (pH Up) to raise pH by {rise:.1f} (from ~{ph_current} to ~{ph_target}). Pre-dissolve in a bucket of water first."


def alkalinity_up_dose(pool_size: str, ta_raise_ppm: float = 20.0) -> str:
    """Return sodium bicarbonate dose to raise TA."""
    lbs = bicarb_lbs(pool_size, ta_raise_ppm)
    return f"Add {lbs:.1f} lbs baking soda (sodium bicarbonate) to raise TA by ~{ta_raise_ppm:.0f} ppm. Broadcast it across the pool surface with the pump running."


def alkalinity_down_dose(pool_size: str, ta_lower_ppm: float = 20.0) -> str:
    """
    Return muriatic acid dose to lower TA.
    Uses direct method: ~26 fl oz per 10,000 gal per 10 ppm TA drop.
    """
    gallons = gallons_for_size(pool_size)
    oz_per_10k_per_10ppm = 26.0
    oz = round(oz_per_10k_per_10ppm * (gallons / 10_000) * (ta_lower_ppm / 10), 1)
    return (
        f"Add {oz:.1f} fl oz muriatic acid (31%) to lower TA by ~{ta_lower_ppm:.0f} ppm. "
        f"Pour near the return jets with the pump running. "
        f"Note: this will also lower pH slightly — retest both before adjusting further."
    )


def cya_dose(pool_size: str, cya_raise_ppm: float = 20.0) -> str:
    """Return granular CYA dose."""
    oz = cya_ounces(pool_size, cya_raise_ppm)
    lbs = round(oz / 16, 1)
    return (
        f"Add {oz:.0f} oz ({lbs:.1f} lbs) granular stabilizer (CYA) to raise stabilizer by ~{cya_raise_ppm:.0f} ppm. "
        f"Place in a mesh sock in the skimmer or pre-dissolve — do NOT pour directly into pool. "
        f"Takes 24–48 hrs to fully register."
    )


def clarifier_dose(pool_size: str) -> str:
    """
    Return liquid clarifier dose for cloudy-blue clearing phase.
    Industry standard: ~1–2 fl oz per 5,000 gal (recovery dose).
    Sources: Clorox Pool & Spa, Pinch a Penny, Natural Chemistry.
    """
    gallons = gallons_for_size(pool_size)
    oz = round(1.5 * (gallons / 5_000), 1)  # 1.5 oz per 5,000 gal (mid-range)
    return (
        f"Add {oz:.1f} fl oz liquid clarifier — helps tiny particles clump so the filter can catch them. "
        f"Pour near the return jets with the pump running. "
        f"Do NOT stack clarifier more than once every 48–72 hours."
    )


def metal_sequestrant_dose(pool_size: str) -> str:
    """
    Return metal sequestrant dose for initial metals treatment.
    Industry standard: ~8–16 fl oz per 10,000 gal initial dose.
    Sources: Jack's Magic, Natural Chemistry Metal Free, Pinch a Penny.
    """
    gallons = gallons_for_size(pool_size)
    oz = round(12.0 * (gallons / 10_000), 1)  # 12 oz per 10,000 gal (mid-range)
    return (
        f"Add {oz:.1f} fl oz metal sequestrant — binds and controls dissolved metals (iron, copper, manganese). "
        f"Pour slowly around the perimeter with the pump running. "
        f"Keep pump running continuously and recheck color in 24–48 hours before adding chlorine."
    )


def flocculant_dose(pool_size: str) -> str:
    """
    Return flocculant dose for pools stalled in the cloudy-blue phase.
    Industry standard: ~4–8 fl oz per 10,000 gal.
    Sources: BioGuard, HTH, Pinch a Penny.
    IMPORTANT: Requires vacuum-to-waste after settling — do NOT filter.
    """
    gallons = gallons_for_size(pool_size)
    oz = round(6.0 * (gallons / 10_000), 1)  # 6 oz per 10,000 gal (mid-range)
    return (
        f"Add {oz:.1f} fl oz liquid flocculant — clumps fine particles into large masses that sink to the bottom. "
        f"Pour around the perimeter, run pump 2 hours, then TURN OFF pump and let settle 8–24 hours. "
        f"Vacuum ALL settled material to WASTE — do NOT run through filter. "
        f"Do NOT use if vacuum-to-waste is unavailable."
    )


def algaecide_dose(pool_size: str) -> str:
    """
    Return polyquat 60% algaecide dose for maintenance/prevention.
    Industry standard: ~3–4 fl oz per 10,000 gal maintenance dose.
    Sources: BioGuard Backup, Lo Chlor, Pinch a Penny.
    NOTE: Polyquat does NOT foam; avoid quat-based products in pools.
    """
    gallons = gallons_for_size(pool_size)
    oz = round(3.5 * (gallons / 10_000), 1)  # 3.5 oz per 10,000 gal (mid-range)
    return (
        f"Add {oz:.1f} fl oz polyquat algaecide (60%) — helps prevent algae from returning after recovery. "
        f"Pour directly into the pool near the return jets. "
        f"Use ONLY polyquat 60% — do NOT use quat-based algaecides (they foam)."
    )


# ---------------------------------------------------------------------------
# Standard dose strings by pool size (pre-computed for common adjustments)
# Used by dosing_engine.py to replace "per label" language
# ---------------------------------------------------------------------------

STANDARD_DOSES: Dict[str, Dict[str, str]] = {
    "ph_down_high": {
        # pH ~7.8–8.0, target 7.4
        "small":  ph_down_dose("small",  ph_current=7.8, ph_target=7.4),
        "medium": ph_down_dose("medium", ph_current=7.8, ph_target=7.4),
        "large":  ph_down_dose("large",  ph_current=7.8, ph_target=7.4),
    },
    "ph_down_very_high": {
        # pH ~8.0+, target 7.4
        "small":  ph_down_dose("small",  ph_current=8.2, ph_target=7.4),
        "medium": ph_down_dose("medium", ph_current=8.2, ph_target=7.4),
        "large":  ph_down_dose("large",  ph_current=8.2, ph_target=7.4),
    },
    "ph_up_low": {
        # pH ~7.0, target 7.4
        "small":  ph_up_dose("small",  ph_current=7.0, ph_target=7.4),
        "medium": ph_up_dose("medium", ph_current=7.0, ph_target=7.4),
        "large":  ph_up_dose("large",  ph_current=7.0, ph_target=7.4),
    },
    "alkalinity_low": {
        # Raise TA by 10 ppm (conservative first dose — retest before adding more)
        "small":  alkalinity_up_dose("small",  10),
        "medium": alkalinity_up_dose("medium", 10),
        "large":  alkalinity_up_dose("large",  10),
    },
    "alkalinity_high": {
        # Lower TA by 10 ppm — conservative first dose. Retest before adding more.
        "small":  alkalinity_down_dose("small",  10),
        "medium": alkalinity_down_dose("medium", 10),
        "large":  alkalinity_down_dose("large",  10),
    },
    "cya_low": {
        # Raise CYA by ~20 ppm (from ~10 to ~30)
        "small":  cya_dose("small",  20),
        "medium": cya_dose("medium", 20),
        "large":  cya_dose("large",  20),
    },
    "slam_low_cya": {
        "small":  green_pool_slam_dose("small",  "low"),
        "medium": green_pool_slam_dose("medium", "low"),
        "large":  green_pool_slam_dose("large",  "low"),
    },
    "slam_acceptable_cya": {
        "small":  green_pool_slam_dose("small",  "acceptable"),
        "medium": green_pool_slam_dose("medium", "acceptable"),
        "large":  green_pool_slam_dose("large",  "acceptable"),
    },
    "slam_high_cya": {
        "small":  green_pool_slam_dose("small",  "high"),
        "medium": green_pool_slam_dose("medium", "high"),
        "large":  green_pool_slam_dose("large",  "high"),
    },
    "slam_unknown_cya": {
        "small":  green_pool_slam_dose("small",  "unknown"),
        "medium": green_pool_slam_dose("medium", "unknown"),
        "large":  green_pool_slam_dose("large",  "unknown"),
    },
    "clarifier": {
        "small":  clarifier_dose("small"),
        "medium": clarifier_dose("medium"),
        "large":  clarifier_dose("large"),
    },
    "metal_sequestrant": {
        "small":  metal_sequestrant_dose("small"),
        "medium": metal_sequestrant_dose("medium"),
        "large":  metal_sequestrant_dose("large"),
    },
    "flocculant": {
        "small":  flocculant_dose("small"),
        "medium": flocculant_dose("medium"),
        "large":  flocculant_dose("large"),
    },
    "algaecide": {
        "small":  algaecide_dose("small"),
        "medium": algaecide_dose("medium"),
        "large":  algaecide_dose("large"),
    },
}

# ---------------------------------------------------------------------------
# Green pool recovery visit cadence (what to expect, visit by visit)
# ---------------------------------------------------------------------------
GREEN_POOL_VISIT_CADENCE = [
    {
        "visit": 1,
        "label": "Visit 1 — Day 1 (Green Pool Shock)",
        "goal": "Kill algae aggressively. Water may look worse before it looks better.",
        "steps": [
            "Vacuum all debris to waste (if possible). If not, vacuum slowly and clean filter after.",
            "Skim all floating debris off the surface.",
            "Brush EVERY surface: walls, floor, steps, corners. Algae hides in corners.",
            "Clean or backwash the filter immediately after brushing.",
            "Correct pH FIRST if high (above 7.6). Wait 30 min before adding chlorine.",
            "Add SLAM-level chlorine dose for your pool size and CYA level.",
            "Run the pump CONTINUOUSLY — do not shut it off.",
            "Come back within 24–48 hours.",
        ],
        "what_to_expect": "Water may turn cloudy blue or darker before it clears. This is normal — dead algae is being filtered out.",
        "red_flags": ["Water is same or darker green after 48 hrs", "Pump is not running", "Filter is clogged and no one cleaned it"],
    },
    {
        "visit": 2,
        "label": "Visit 2 — Day 2 or 3 (Recheck & Repeat)",
        "goal": "Assess progress. Re-dose chlorine. Keep filter clean.",
        "steps": [
            "Test chlorine level — it should have dropped significantly (algae consumed it).",
            "Vacuum dead algae off the bottom (cloudy grey/white sediment is dead algae — good sign).",
            "Brush the pool again.",
            "Clean or backwash the filter — it will be dirty.",
            "Re-add chlorine to SLAM level. Do not under-dose.",
            "Keep pump running continuously.",
        ],
        "what_to_expect": "Water should be shifting from green toward cloudy blue or hazy. If still bright green, increase chlorine dose.",
        "red_flags": ["No change at all since Visit 1", "Chlorine is still very high (algae not consuming it — check for other issues)", "Visible green algae still clinging to walls"],
    },
    {
        "visit": 3,
        "label": "Visit 3 — Day 4–5 (Clearing Phase)",
        "goal": "Water should be turning cloudy blue. Now focus on filtration and clarity.",
        "steps": [
            "Vacuum any remaining sediment.",
            "Brush lightly.",
            "Clean or backwash the filter.",
            "Maintain chlorine at normal levels (not SLAM level if water is blue).",
            "Add clarifier if water is hazy blue but not clearing.",
            "Run pump 12–24 hrs/day.",
        ],
        "what_to_expect": "Cloudy blue water and improving bottom visibility. You should be able to see the main drain by Visit 4.",
        "red_flags": ["Water turning green again", "Pool chemistry still unstable", "Filter repeatedly clogging every few hours"],
    },
    {
        "visit": 4,
        "label": "Visit 4 — Day 6–7 (Final Check or Escalate)",
        "goal": "Pool should be clear or nearly clear. If not, escalate.",
        "steps": [
            "Test all chemistry (FC, pH, TA, CYA).",
            "Vacuum and skim any remaining debris.",
            "Brush steps and corners (algae can hide there longest).",
            "Balance all chemistry to target ranges.",
            "If pool is not clear by this visit, flag for supervisor review.",
        ],
        "what_to_expect": "Clear water, visible bottom, chemistry in range. Customer should be happy.",
        "red_flags": ["Still green or dark cloudy after 4 visits", "Customer has complained", "Equipment appears to be the issue (filter, pump, plumbing)"],
    },
]
