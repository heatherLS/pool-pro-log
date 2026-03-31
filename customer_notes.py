"""
customer_notes.py

Short, plain-language, copy-paste-ready customer messages for each pool situation.
Written at an 8th-grade reading level — no pool jargon.
Format: SMS-length. Customers don't read paragraphs.
"""

from typing import Any, Dict


def get_customer_sms(
    mode: str,
    progress_status: str,
    severity: int,
    escalation_flag: bool,
    visit_number: int = 1,
) -> Dict[str, str]:
    """
    Return a dict with:
      short_sms  — one text message (~160 chars), copy-paste ready
      full_note  — 2–4 sentence version for a more detailed update
      subject    — one-line summary of pool status
    """
    mode = (mode or "").lower()
    progress_status = (progress_status or "first_visit").lower()

    # --- GREEN POOL ---
    if mode == "sanitize":
        if progress_status == "first_visit":
            return {
                "subject": "Pool treatment started — green pool recovery underway",
                "short_sms": (
                    "Hi! We visited your pool today and started the green pool recovery process. "
                    "It may look a bit cloudier over the next day or two — that's totally normal and means it's working. "
                    "We'll be back soon to check on it. 🏊"
                ),
                "full_note": (
                    "We visited your pool today and began the green pool recovery treatment. "
                    "We vacuumed debris, brushed the entire pool, cleaned the filter, and added the appropriate chemicals. "
                    "Over the next 24–48 hours the water may look cloudier before it starts clearing — "
                    "this is a normal part of the process as the dead algae gets filtered out. "
                    "Please keep the pump running if possible. We'll be back to check progress and continue treatment."
                ),
            }
        elif progress_status in ("improving_well", "improving_slowly"):
            return {
                "subject": "Pool is improving — continuing recovery treatment",
                "short_sms": (
                    "Great news — your pool is improving! We treated it again today to keep the recovery moving. "
                    "It should continue clearing over the next couple of days. We'll check back soon. 💙"
                ),
                "full_note": (
                    "Your pool is showing good improvement since our last visit. "
                    "We treated it again today — vacuumed, brushed, cleaned the filter, and re-dosed the chemicals. "
                    "The water should continue shifting toward clear over the next 2–3 days. "
                    "We'll be back to finish the job."
                ),
            }
        elif progress_status == "stalled":
            return {
                "subject": "Pool recovery check-in — working through a stubborn case",
                "short_sms": (
                    "We checked your pool today. Recovery is taking a little longer than expected. "
                    "We're adjusting the treatment and will be back soon. "
                    "If you have any questions, don't hesitate to reach out!"
                ),
                "full_note": (
                    "We visited your pool today and noticed the recovery is moving more slowly than expected. "
                    "We've adjusted our treatment approach and are monitoring the situation closely. "
                    "We'll be back within the next day or two to check progress. "
                    "Please keep the pump running continuously if possible — it makes a big difference."
                ),
            }
        elif progress_status == "worse":
            return {
                "subject": "Pool condition update — flagging for supervisor review",
                "short_sms": (
                    "We checked your pool today. We noticed it hasn't improved the way we expected and have flagged it "
                    "for our team to take a closer look. We'll be in touch shortly."
                ),
                "full_note": (
                    "We visited your pool today and unfortunately the condition has not improved as expected. "
                    "We have flagged this for our team supervisor to review and determine the best next steps. "
                    "We will follow up with you shortly. Thank you for your patience."
                ),
            }
        else:
            return {
                "subject": "Pool treatment visit completed",
                "short_sms": "We completed today's pool treatment visit. We'll be back to check on progress soon!",
                "full_note": "We completed today's treatment visit. The pool is actively being treated and monitored.",
            }

    # --- CLOUDY BLUE / CLEARING ---
    elif mode == "clear":
        return {
            "subject": "Pool is clearing up — almost there!",
            "short_sms": (
                "Your pool is in the clearing phase now — the water is turning blue! "
                "We focused on filtration today to finish clearing it up. Looking good! 💙"
            ),
            "full_note": (
                "Great news — your pool has cleared the green stage and is now in the final clearing phase. "
                "We focused on filtration today to remove the remaining cloudiness. "
                "With the pump running continuously, you should see noticeably clearer water within the next day or two. "
                "We'll be back to confirm everything is balanced and looking great."
            ),
        }

    # --- BALANCE ---
    elif mode == "balance":
        return {
            "subject": "Pool chemistry adjusted — water is clear and being balanced",
            "short_sms": (
                "Your pool looks clear! We stopped by today to fine-tune the chemistry to keep it safe and balanced. "
                "Everything is looking good. 👍"
            ),
            "full_note": (
                "Your pool water is clear and we completed a chemistry balance visit today. "
                "We adjusted the water chemistry to make sure your pool stays safe, comfortable, and clear. "
                "We'll continue monitoring on our regular schedule. "
                "If you notice any changes in color or clarity, feel free to reach out."
            ),
        }

    # --- METALS ---
    elif mode == "metals":
        return {
            "subject": "Pool discoloration update — treating for minerals in the water",
            "short_sms": (
                "We visited your pool today. The discoloration appears to be caused by minerals in the water "
                "(common with well water or new fills), not algae. "
                "We're using the right treatment for this — it should start clearing soon."
            ),
            "full_note": (
                "We visited your pool today and assessed the discoloration. "
                "Based on what we observed, the color appears to be caused by minerals (such as iron) in the water "
                "rather than algae — this is common when pools are filled with well water or recently topped off. "
                "We are treating it with the appropriate mineral treatment and monitoring progress. "
                "It's important NOT to shock the pool during this phase, as that can make the discoloration worse. "
                "We'll be back to check progress."
            ),
        }

    # --- FALLBACK ---
    else:
        return {
            "subject": "Pool service visit completed",
            "short_sms": "We completed your pool service visit today. We'll be in touch with an update soon!",
            "full_note": "We completed your scheduled pool service visit today and will follow up with a full update.",
        }


def escalation_add_on() -> str:
    """Additional sentence to append to any customer note when escalation is flagged."""
    return (
        "We have flagged your pool for a supervisor review to make sure we are giving it the right attention. "
        "You may hear from our team directly."
    )
