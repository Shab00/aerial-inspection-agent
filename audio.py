import json
import os

from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


EXTRACTION_SYSTEM_PROMPT = """You are processing aerial tree inspection audio notes for a bat survey. Extract ONLY text description fields from the transcript.

You must NEVER extract, estimate or calculate:
- Any measurements (heights, widths, depths)
- PRF suitability ratings
- Overall tree suitability

Extract ONLY these text fields if mentioned:
- feature_type: type of PRF feature
- aspect: compass direction
- orientation: facing direction
- bat_notes: any bat observations mentioned
- smell: any smell described
- substrate: surface texture described
- humidity_condition: moisture conditions
- apex_shape: shape of the apex
- competitors: other species mentioned
- inspection_notes_1: surveyor's description of the feature

Return JSON with only the fields you found.
If a field is not mentioned return null.
Never invent values not spoken in the audio."""

_ALLOWED_FIELDS = {
    "feature_type",
    "aspect",
    "orientation",
    "bat_notes",
    "smell",
    "substrate",
    "humidity_condition",
    "apex_shape",
    "competitors",
    "inspection_notes_1",
}


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
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
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

    return {field: extracted.get(field) for field in _ALLOWED_FIELDS if field in extracted}
