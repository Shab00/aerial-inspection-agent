import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from openai import OpenAIError

from audio import extract_text_fields, transcribe_audio

router = APIRouter()

# Expected failure modes from the OpenAI calls; anything else bubbles up.
_HANDLED_ERRORS = (OpenAIError, ValueError, RuntimeError)


@router.post("/audio")
async def process_audio(
    tree_ref: int = Form(...),
    prf_number: int = Form(...),
    audio: UploadFile = File(...),
):
    suffix = os.path.splitext(audio.filename or "")[1] or ".m4a"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        try:
            transcript = transcribe_audio(tmp_path)
        except _HANDLED_ERRORS as e:
            raise HTTPException(
                status_code=422, detail={"stage": "transcribe", "message": str(e)}
            ) from e
    finally:
        os.remove(tmp_path)

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=422,
            detail={"stage": "transcribe", "message": "empty transcript"},
        )

    try:
        extracted_fields = extract_text_fields(transcript, tree_ref, prf_number)
    except _HANDLED_ERRORS as e:
        raise HTTPException(
            status_code=422, detail={"stage": "extract", "message": str(e)}
        ) from e

    return {"transcript": transcript, "extracted_fields": extracted_fields}
