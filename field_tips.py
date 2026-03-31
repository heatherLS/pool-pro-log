"""
field_tips.py

Field-proven tips and tricks organized by pool situation.
These come from real pro experience — the kind of things that aren't in any manual.

To add a tip: append a dict to the relevant list.
Fields:
  title     — short headline
  body      — explanation in plain language (write for a brand new pro)
  source    — "From an experienced pro" or "From the LawnStarter team" etc.
  tags      — list of strings for filtering (optional)
  warning   — True if this tip includes a critical safety or mistake-avoidance note
"""

from typing import Dict, List, Any

FIELD_TIPS: Dict[str, List[Dict[str, Any]]] = {

    # -------------------------------------------------------------------------
    # METALS / WELL WATER
    # -------------------------------------------------------------------------
    "metals": [
        {
            "title": "Well Water + Chlorine = Green. Don't Panic — It's Not Algae.",
            "body": (
                "If a customer filled their pool with well water and the water looks brown, rusty, or tea-colored, "
                "there's a good chance it has iron or other metals in it.\n\n"
                "Here's the trap new pros fall into: you see brown water, you add chlorine, and the pool turns GREEN. "
                "That's not algae. That's the chlorine oxidizing the iron and turning it a different color. "
                "More chlorine will make it worse, not better.\n\n"
                "**What to do instead:**\n"
                "1. Do NOT shock the pool.\n"
                "2. Add a metal sequestrant product first — it binds the metals so they don't stain or discolor.\n"
                "3. Run the filter continuously.\n"
                "4. Let the sequestrant work 24–48 hours before touching the chlorine.\n\n"
                "The key question to ask: Was this pool recently filled with well water? If yes, treat for metals first."
            ),
            "source": "From the LawnStarter team — personal experience",
            "tags": ["well_water", "iron", "metals", "new_fill"],
            "warning": True,
        },
        {
            "title": "The Bucket + Cotton Filter Method (No Sequestrant on Hand?)",
            "body": (
                "If you don't have metal sequestrant available and the pool has iron from well water, "
                "here's a field workaround that actually works:\n\n"
                "**What you need:**\n"
                "- A 5-gallon bucket from Home Depot or Lowes (~$5)\n"
                "- A bag of cotton or polyfill stuffing (craft stores, Walmart)\n"
                "- Your pool vacuum hose\n\n"
                "**How to set it up:**\n"
                "1. Fill the bucket with cotton/polyfill tightly packed.\n"
                "2. Run your vacuum hose in through the top of the bucket.\n"
                "3. Drill several holes in the bottom/front of the bucket.\n"
                "4. As water flows through the hose into the cotton, the iron particles get trapped. "
                "Clean water flows out through the holes back into the pool.\n"
                "5. Replace the cotton when it turns brown/orange — usually every few hours.\n\n"
                "This is a temporary fix, not a permanent solution. Get sequestrant on the next visit. "
                "But this can make a real visible difference same-day."
            ),
            "source": "Field-tested by the LawnStarter team",
            "tags": ["well_water", "iron", "diy_workaround", "field_fix"],
            "warning": False,
        },
    ],

    # -------------------------------------------------------------------------
    # SANITIZE / GREEN POOL
    # -------------------------------------------------------------------------
    "sanitize": [
        {
            "title": "The Pool Gets Worse Before It Gets Better — Tell the Customer.",
            "body": (
                "When you first treat a green pool, the water often turns cloudy grey or murky before it clears. "
                "This is normal and actually a GOOD sign — the algae is dying and dead material is being filtered out.\n\n"
                "New pros sometimes panic and add more chemicals when this happens. Don't. "
                "The water looking worse on day 2 means the treatment is working.\n\n"
                "Set this expectation with the customer before you leave: "
                "'The pool may look a little cloudier in the next day or two as the dead algae clears out. "
                "That's normal and means it's working. It should start looking blue within a few days.'"
            ),
            "source": "From an experienced pro",
            "tags": ["green_pool", "customer_communication", "expectations"],
            "warning": False,
        },
        {
            "title": "Brushing Isn't Optional — It's Half the Treatment.",
            "body": (
                "A lot of new pros brush once and move on. But brushing is one of the most important things you do "
                "on a green pool visit.\n\n"
                "Algae grips onto surfaces — walls, steps, corners, behind ladders. When you brush, you:\n"
                "1. Break the algae loose from the surface so the chlorine can reach it.\n"
                "2. Push the algae into the water column where the filter can catch it.\n"
                "3. Circulate dead algae toward the drain and filter instead of letting it settle.\n\n"
                "Brush BEFORE adding chemicals. Brush EVERYTHING — not just the obvious spots. "
                "The corners behind steps and around the main drain are where algae hides longest."
            ),
            "source": "From an experienced pro",
            "tags": ["green_pool", "brushing", "technique"],
            "warning": False,
        },
        {
            "title": "Filter Cleaning = The Secret Weapon Most Pros Underuse.",
            "body": (
                "On a green pool, the filter is catching massive amounts of dead algae. "
                "It will clog faster than you've ever seen on a maintenance visit.\n\n"
                "Clean or backwash the filter:\n"
                "- BEFORE adding chemicals (start fresh)\n"
                "- 1–2 hours AFTER adding chemicals (it will be full again)\n"
                "- Every single visit during recovery\n\n"
                "A clogged filter means dirty water is just recirculating. "
                "If the pool isn't clearing after 2–3 visits, the first question is always: "
                "Was the filter actually getting cleaned?"
            ),
            "source": "From an experienced pro",
            "tags": ["green_pool", "filter", "technique"],
            "warning": False,
        },
        {
            "title": "Chlorine Won't Work If pH Is Too High.",
            "body": (
                "Here's something the pool manual doesn't make obvious: "
                "chlorine becomes almost useless when the pH is above 8.0.\n\n"
                "At pH 7.5 — about 50% of your chlorine is working.\n"
                "At pH 8.0 — only about 20% is working.\n"
                "At pH 8.5 — almost nothing.\n\n"
                "So if you add 2 gallons of chlorine and the pool doesn't improve, check the pH FIRST. "
                "If it's high, lower the pH before adding more chlorine — otherwise you're pouring money "
                "(and chemicals) down the drain.\n\n"
                "Always test pH before treating a green pool."
            ),
            "source": "From the LawnStarter team",
            "tags": ["green_pool", "ph", "chlorine_effectiveness"],
            "warning": True,
        },
        {
            "title": "Vacuum to Waste — Why It Matters for a Swamp Pool.",
            "body": (
                "On a bad green pool (dark green, can't see the bottom), there can be inches of debris "
                "and dead algae sitting on the floor.\n\n"
                "If you vacuum that into the filter, you'll clog it within minutes. "
                "Vacuum to WASTE instead — this routes the dirty water directly out of the system "
                "without going through the filter.\n\n"
                "Yes, this drops the water level. That's fine. You can refill with the hose. "
                "It's much faster and more effective than trying to filter your way through a swamp.\n\n"
                "Check if the pump and valve setup allows vacuum-to-waste before you start. "
                "Not every system has it — if not, vacuum slowly and clean the filter every 15–20 minutes."
            ),
            "source": "From an experienced pro",
            "tags": ["green_pool", "vacuum", "debris", "swamp"],
            "warning": False,
        },
    ],

    # -------------------------------------------------------------------------
    # CLEAR / CLOUDY BLUE
    # -------------------------------------------------------------------------
    "clear": [
        {
            "title": "Cloudy Blue Is a Win — Don't Over-Treat It.",
            "body": (
                "When a green pool turns cloudy blue, new pros sometimes think they failed because it's not clear. "
                "Cloudy blue is actually a major milestone — the algae is dead, you're just filtering out the corpses.\n\n"
                "At this stage, the job is mostly filtration:\n"
                "1. Keep the pump running.\n"
                "2. Clean the filter frequently (it's working hard).\n"
                "3. Maintain chlorine in the normal range (don't SLAM-dose a cloudy-blue pool).\n"
                "4. Add clarifier if it's not clearing after 1–2 days of filtration.\n\n"
                "What NOT to do: add more shock, add more algaecide, or start changing chemistry. "
                "The chemistry is probably fine. Let the filter do its job."
            ),
            "source": "From an experienced pro",
            "tags": ["cloudy_blue", "clearing", "patience"],
            "warning": False,
        },
    ],

    # -------------------------------------------------------------------------
    # BALANCE / CHEMISTRY
    # -------------------------------------------------------------------------
    "balance": [
        {
            "title": "CYA: The Sunscreen Your Chlorine Desperately Needs.",
            "body": (
                "Stabilizer (CYA) protects chlorine from being burned off by sunlight. "
                "Without it, chlorine in a sunny Florida pool can disappear within a few hours.\n\n"
                "If a customer says 'we keep adding chlorine and it doesn't last' — check CYA first.\n\n"
                "Target: 30–50 ppm for most outdoor pools.\n\n"
                "Important: CYA goes INTO the skimmer in a mesh sock or pre-dissolved in a bucket. "
                "NEVER pour it directly into the pool — it can bleach the surface. "
                "Also, it takes 24–48 hours to fully register on a test strip. "
                "Don't add more the same day thinking it didn't work."
            ),
            "source": "From the LawnStarter team",
            "tags": ["cya", "stabilizer", "chlorine_loss"],
            "warning": False,
        },
        {
            "title": "Never Mix Chemicals — Even 'Just a Little.'",
            "body": (
                "This one is non-negotiable. NEVER mix pool chemicals together — not in a bucket, "
                "not on a surface, not 'just to see what happens.'\n\n"
                "Chlorine + acid = toxic chlorine gas. Instantly dangerous.\n"
                "Shock + other shock = fire or explosion risk.\n\n"
                "Always:\n"
                "1. Add chemicals separately, directly into the pool with the pump running.\n"
                "2. Wait 15–30 minutes between adding different chemicals.\n"
                "3. Add acid near the return jets (away from the skimmer).\n"
                "4. Never add chemicals to the skimmer basket at the same time.\n\n"
                "If you're ever unsure about chemical order, the safe sequence is: "
                "pH adjustment → wait → then chlorine."
            ),
            "source": "From the LawnStarter team",
            "tags": ["safety", "chemical_mixing", "critical"],
            "warning": True,
        },
    ],

    # -------------------------------------------------------------------------
    # GENERAL / ALL SITUATIONS
    # -------------------------------------------------------------------------
    "general": [
        {
            "title": "Take a Photo Every Single Visit — For You, Not Just the App.",
            "body": (
                "Photos protect you as much as they help the customer.\n\n"
                "If a pool doesn't recover and the customer disputes the service, "
                "your dated photo trail shows exactly what the pool looked like each visit and what was done.\n\n"
                "Photo both the overall pool AND the test strip, every time. "
                "It takes 30 seconds and can save hours of headache later."
            ),
            "source": "From the LawnStarter team",
            "tags": ["documentation", "photos", "protection"],
            "warning": False,
        },
        {
            "title": "When in Doubt, Do Less Chemistry — Not More.",
            "body": (
                "A common mistake for new pros is to add more chemicals when something isn't working. "
                "Over-treating a pool can create new problems that are harder to fix than the original one.\n\n"
                "If you're not sure what's going on:\n"
                "1. Test the water and write down what you see.\n"
                "2. Look at the last visit's results — what changed?\n"
                "3. If something seems off, flag it and ask before adding more chemicals.\n\n"
                "It's always better to do less and retest than to add the wrong thing."
            ),
            "source": "From an experienced pro",
            "tags": ["chemistry", "over_treatment", "caution"],
            "warning": False,
        },
    ],
}


def get_tips_for_mode(mode: str) -> List[Dict[str, Any]]:
    """Return field tips relevant to the current pool mode, plus general tips."""
    tips = list(FIELD_TIPS.get(mode.lower(), []))
    tips += FIELD_TIPS.get("general", [])
    return tips


def get_warning_tips_for_mode(mode: str) -> List[Dict[str, Any]]:
    """Return only the warning-level tips for this mode."""
    return [t for t in get_tips_for_mode(mode) if t.get("warning")]
