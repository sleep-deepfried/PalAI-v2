"""Rice brown-spot disease classifier using Gemini vision."""
from __future__ import annotations
import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

PROMPT = (
    "You are a plant pathologist analyzing a photo of a rice plant. Classify it "
    "as one of: brown spot, sheath blight, tungro, rice blast, healthy, or unknown.\n\n"
    "Symptom guide:\n"
    "- brownspot: small-to-medium oval brown lesions, often with a gray center and "
    "yellow halo, scattered on the leaf blade.\n"
    "- sheath_blight: greenish-gray water-soaked lesions on the leaf sheath that "
    "enlarge into oval/irregular straw-colored patches with brown borders, usually "
    "near the water line on the sheath rather than the blade.\n"
    "- tungro: leaves turn yellow-orange from the tip downward, plants are stunted "
    "with reduced tillering; discoloration is uniform rather than spotty.\n"
    "- rice_blast: diamond/spindle-shaped lesions with gray-white centers and brown "
    "or reddish borders on leaves; on necks, a dark girdling lesion.\n"
    "- healthy: green leaves/sheath with no visible lesions or discoloration.\n"
    "- unknown: image is blurry, dark, contains no plant material, or shows "
    "something that is not a rice plant.\n\n"
    "Be decisive — if a rice plant is visible, prefer a specific label over "
    "'unknown'. Only fall back to 'unknown' when no plant is in the frame.\n\n"
    "Respond ONLY with JSON:\n"
    "{\n"
    '  "is_diseased": boolean,    // true for any disease label, false for healthy/unknown\n'
    '  "label": "brownspot" | "sheath_blight" | "tungro" | "rice_blast" | "healthy" | "unknown",\n'
    '  "confidence": number,      // 0.0 to 1.0\n'
    '  "notes": string             // brief reason, <= 140 chars, describe what you see\n'
    "}"
)

_DISEASE_LABELS = {"brownspot", "sheath_blight", "tungro", "rice_blast"}
_ALL_LABELS = _DISEASE_LABELS | {"healthy", "unknown"}

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_diseased": {"type": "BOOLEAN"},
        "label": {"type": "STRING", "enum": sorted(_ALL_LABELS)},
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
        label = str(data.get("label") or "unknown")
        if label not in _ALL_LABELS:
            label = "unknown"
        # Trust the label over the model's is_diseased flag — keeps the two consistent.
        return {
            "is_diseased": label in _DISEASE_LABELS,
            "label": label,
            "confidence": float(data.get("confidence") or 0.0),
            "notes": str(data.get("notes") or ""),
        }
    except Exception as e:
        log.exception("Gemini classification failed")
        return _error(str(e))
