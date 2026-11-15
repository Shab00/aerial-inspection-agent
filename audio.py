import json
import os
import re

from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


SYSTEM_PROMPT = """You are processing aerial tree inspection audio notes for a bat survey. You extract text fields from a transcript under strict evidence rules.

EVIDENCE RULES (absolute):
- NEVER invent, infer, guess, or paraphrase a field. Only record what the surveyor actually said.
- Every non-null field MUST include "quote": an exact, contiguous span copied character-for-character from the transcript. Do not fix spelling, reorder words, join separate phrases, or add words.
- If you cannot point to the exact words in the transcript that support a field, return null for that field.
- null is ALWAYS correct when the surveyor did not say it. When in doubt, return null.

FORBIDDEN (always null / never extract):
- NEVER calculate, estimate, or extract any number, measurement, height, width, depth, diameter, percentage, temperature, cloud cover, or wind.
- NEVER assign a suitability rating (PRF-I, PRF-M, Negligible). Suitability is not one of your fields; never put a rating in any field.

FIELDS (extract only these):
- feature_type: type of PRF feature (e.g. rot hole, split, flaking bark)
- substrate: surface texture described inside the feature
- aspect: compass direction of the feature
- orientation: direction the feature faces or runs
- bat_notes: any bat observations
- droppings: true or false, ONLY if the surveyor explicitly states droppings were or were not present
- smell: any smell described
- humidity_condition: moisture conditions described
- apex_shape: shape of the feature's apex
- competitors: other species mentioned using the feature
- inspection_notes_1, inspection_notes_2, inspection_notes_3: the surveyor's own descriptive notes about the feature, each a separate verbatim statement. Only use these for observations about the feature that are not already captured in another field. Never use them for procedural or filler speech (tree/PRF identifiers, "moving on", "that's it"); return null instead.

For each field return either null or {"value": ..., "quote": "..."}. "value" must be taken from the quoted words, not reworded."""

_TEXT_FIELDS = [
    "feature_type",
    "substrate",
    "aspect",
    "orientation",
    "bat_notes",
    "smell",
    "humidity_condition",
    "apex_shape",
    "competitors",
    "inspection_notes_1",
    "inspection_notes_2",
    "inspection_notes_3",
]
_FIELDS = _TEXT_FIELDS[:5] + ["droppings"] + _TEXT_FIELDS[5:]


def _field_schema(value_type: str) -> dict:
    return {
        "anyOf": [
            {"type": "null"},
            {
                "type": "object",
                "properties": {
                    "value": {"type": value_type},
                    "quote": {"type": "string"},
                },
                "required": ["value", "quote"],
                "additionalProperties": False,
            },
        ]
    }


SCHEMA = {
    "type": "object",
    "properties": {
        field: _field_schema("boolean" if field == "droppings" else "string")
        for field in _FIELDS
    },
    "required": _FIELDS,
    "additionalProperties": False,
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def enforce_quotes(extracted: dict, transcript: str) -> dict:
    """Null out any field whose quote is empty or not verbatim in the transcript,
    or whose string value is empty or not verbatim in its own quote."""
    normalized_transcript = _normalize(transcript)
    enforced = {}
    for field in _FIELDS:
        entry = extracted.get(field)
        quote = entry.get("quote") if isinstance(entry, dict) else None
        if not isinstance(quote, str) or not _normalize(quote):
            enforced[field] = None
        elif _normalize(quote) not in normalized_transcript:
            enforced[field] = None
        elif isinstance(entry.get("value"), str) and (
            not _normalize(entry["value"])
            or _normalize(entry["value"]) not in _normalize(quote)
        ):
            enforced[field] = None
        else:
            enforced[field] = entry
    return enforced


def transcribe_audio(file_path: str) -> str:
    client = _get_client()
    with open(file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    return transcript.text


def extract_text_fields(transcript: str, tree_ref: int, prf_number: int) -> dict:
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "prf_extraction",
                "strict": True,
                "schema": SCHEMA,
            },
        },
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Tree Ref: {tree_ref}\nPRF Number: {prf_number}\n\n"
                    f"Transcript:\n{transcript}"
                ),
            },
        ],
    )
    content = response.choices[0].message.content
    try:
        extracted = json.loads(content)
    except (TypeError, ValueError):
        extracted = {}
    if not isinstance(extracted, dict):
        extracted = {}

    enforced = enforce_quotes(extracted, transcript)
    return {
        field: entry["value"] if entry is not None else None
        for field, entry in enforced.items()
    }
