"""Rice brown-spot disease classifier using Gemini vision."""
from __future__ import annotations
import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

PROMPT = (
    "You are a rice plant pathologist. Look at this photo and decide whether the "
    "rice leaf shows symptoms of brown spot disease (Cochliobolus miyabeanus / "
    "Bipolaris oryzae) — small to medium oval brown lesions, often with a gray "
    "center and yellow halo, scattered across the leaf blade.\n\n"
    "Respond ONLY with JSON matching this schema:\n"
    "{\n"
    '  "is_diseased": boolean,            // true ONLY if brown spot is clearly visible\n'
    '  "label": "brownspot" | "healthy" | "unknown",\n'
    '  "confidence": number,              // 0.0 to 1.0\n'
    '  "notes": string                     // short reason, <= 120 chars\n'
    "}\n"
    "If the image is unclear, not a rice leaf, or you cannot decide, set "
    'label="unknown" and is_diseased=false.'
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
