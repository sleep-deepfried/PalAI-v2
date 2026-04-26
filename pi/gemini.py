"""Rice brown-spot disease classifier using Gemini vision."""
from __future__ import annotations
import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

PROMPT = (
    "You are a plant pathologist analyzing a photo for rice brown spot disease "
    "(Cochliobolus miyabeanus / Bipolaris oryzae). Brown spot symptoms: small to "
    "medium oval brown lesions, often with a gray center and yellow halo, "
    "scattered on the leaf blade.\n\n"
    "Classify the photo using these rules:\n"
    "- label='brownspot': you can see oval brown lesions on a green leaf.\n"
    "- label='healthy': you can see a green leaf with no visible lesions.\n"
    "- label='unknown': the image is blurry, dark, contains no plant material, "
    "or shows a leaf that is not green/rice-like.\n\n"
    "Be decisive — if any leaf is visible, prefer 'healthy' or 'brownspot' over "
    "'unknown'. Only fall back to 'unknown' when no plant is in the frame.\n\n"
    "Respond ONLY with JSON:\n"
    "{\n"
    '  "is_diseased": boolean,    // true only when label is "brownspot"\n'
    '  "label": "brownspot" | "healthy" | "unknown",\n'
    '  "confidence": number,      // 0.0 to 1.0\n'
    '  "notes": string             // brief reason, <= 140 chars, describe what you see\n'
    "}"
)

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_diseased": {"type": "BOOLEAN"},
        "label": {"type": "STRING", "enum": ["brownspot", "healthy", "unknown"]},
        "confidence": {"type": "NUMBER"},
        "notes": {"type": "STRING"},
    },
    "required": ["is_diseased", "label", "confidence", "notes"],
}


def _error(msg: str) -> dict[str, Any]:
    return {
        "is_diseased": None,
        "label": "error",
        "confidence": 0.0,
        "notes": msg[:240],
    }


def classify_brownspot(jpeg_bytes: bytes) -> dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _error("GEMINI_API_KEY not set")

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        return _error(f"google-genai not installed: {e}")

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
                PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_RESPONSE_SCHEMA,
                temperature=0.2,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            return _error("empty response from Gemini")
        data = json.loads(text)
        return {
            "is_diseased": bool(data.get("is_diseased")),
            "label": str(data.get("label") or "unknown"),
            "confidence": float(data.get("confidence") or 0.0),
            "notes": str(data.get("notes") or ""),
        }
    except Exception as e:
        log.exception("Gemini classification failed")
        return _error(str(e))
