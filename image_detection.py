import base64
import json
import os
from typing import Any, Dict, Optional

from openai import OpenAI


VISION_MODEL = os.getenv("POOL_VISION_MODEL", "gpt-4.1")


SYSTEM_PROMPT = """
You are a pool-condition vision analyzer for a residential pool service platform.

Your job is to inspect 1 or 2 images:
1. a pool photo
2. an optional test strip photo

Return ONLY valid JSON with this schema:
{
  "pool_condition": "clear|cloudy_blue|light_green|dark_green|brown|rusty|tea_colored|unknown",
  "surface_algae_level": "none|light|moderate|heavy|unknown",
  "visible_debris_level": "none|light|heavy|unknown",
  "bottom_visibility": "yes|partial|no|unknown",
  "metals_suspected": true,
  "free_chlorine_bucket": "very_low|low|acceptable|high|unknown",
  "ph_bucket": "low|acceptable|high|very_high|unknown",
  "alkalinity_bucket": "low|acceptable|high|unknown",
  "cya_bucket": "low|acceptable|high|unclear|unknown",
  "strip_confidence": "high|medium|low",
  "severity_hint": 1,
  "reasoning_summary": "short plain-English summary"
}

Rules:
- Be conservative. If unclear, return "unknown".
- Do not invent exact chemical ppm values.
- Only infer metals when discoloration looks brown/rusty/tea-colored or strongly suggests metals.
- severity_hint should be 1-5.
- If no strip is visible or readable, return unknown strip buckets and low confidence.
- Return JSON only. No markdown.
""".strip()


USER_PROMPT = """
Analyze the uploaded pool image and optional strip image.

Goals:
- Classify the pool visually.
- Estimate algae/debris severity.
- Estimate bottom visibility.
- Detect whether metals may be present.
- Read the strip into broad chemistry buckets if possible.
- Keep the output conservative and operational.
""".strip()


def _to_data_url(file_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _guess_mime(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def analyze_pool_images(
    pool_image_bytes: bytes,
    pool_filename: str,
    strip_image_bytes: Optional[bytes] = None,
    strip_filename: Optional[str] = None,
    client: Optional[OpenAI] = None,
) -> Dict[str, Any]:

    if client is None:
        # Pick up OPENAI_API_KEY from st.secrets when running on Streamlit Cloud
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        except Exception:
            api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key) if api_key else OpenAI()

    content = [
        {"type": "input_text", "text": USER_PROMPT},
        {
            "type": "input_image",
            "image_url": _to_data_url(pool_image_bytes, _guess_mime(pool_filename)),
            "detail": "high",
        },
    ]

    if strip_image_bytes and strip_filename:
        content.append(
            {
                "type": "input_image",
                "image_url": _to_data_url(strip_image_bytes, _guess_mime(strip_filename)),
                "detail": "high",
            }
        )

    response = client.responses.create(
        model=VISION_MODEL,
        instructions=SYSTEM_PROMPT,
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    raw_text = getattr(response, "output_text", "")
    if not raw_text:
        raise ValueError("Vision response returned no output_text.")

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Vision response was not valid JSON: {raw_text}") from exc

    return parsed


def merge_image_detection_into_visit(
    visit: Dict[str, Any],
    detection: Dict[str, Any],
    overwrite_existing: bool = False,
) -> Dict[str, Any]:

    updated = dict(visit)

    mapping = {
        "water_color_input": detection.get("pool_condition", "unknown"),
        "surface_algae_level": detection.get("surface_algae_level", "unknown"),
        "visible_debris_level": detection.get("visible_debris_level", "unknown"),
        "bottom_visibility": detection.get("bottom_visibility", "unknown"),
        "strip_free_chlorine_bucket": detection.get("free_chlorine_bucket", "unknown"),
        "strip_ph_bucket": detection.get("ph_bucket", "unknown"),
        "strip_alkalinity_bucket": detection.get("alkalinity_bucket", "unknown"),
        "strip_cya_bucket": detection.get("cya_bucket", "unknown"),
        "strip_confidence": detection.get("strip_confidence", "low"),
    }

    for key, value in mapping.items():
        current = str(updated.get(key, "")).strip()
        if overwrite_existing or not current:
            updated[key] = value

    # 🔥 IMPORTANT: REMOVE WELL WATER AUTO-SET
    # (Provider must manually input this)

    updated["vision_reasoning_summary"] = detection.get("reasoning_summary", "")
    updated["vision_severity_hint"] = detection.get("severity_hint", "")
    updated["vision_metals_suspected"] = detection.get("metals_suspected", False)

    return updated


def build_detection_preview(detection: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Pool Condition": detection.get("pool_condition", "unknown"),
        "Surface Algae": detection.get("surface_algae_level", "unknown"),
        "Visible Debris": detection.get("visible_debris_level", "unknown"),
        "Bottom Visibility": detection.get("bottom_visibility", "unknown"),
        "Metals Suspected": detection.get("metals_suspected", False),
        "Free Chlorine": detection.get("free_chlorine_bucket", "unknown"),
        "pH": detection.get("ph_bucket", "unknown"),
        "Alkalinity": detection.get("alkalinity_bucket", "unknown"),
        "CYA": detection.get("cya_bucket", "unknown"),
        "Strip Confidence": detection.get("strip_confidence", "low"),
        "Severity Hint": detection.get("severity_hint", ""),
        "Summary": detection.get("reasoning_summary", ""),
    }