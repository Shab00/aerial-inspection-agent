import os
import tempfile

from fastapi import APIRouter, File, Form, UploadFile

from audio import extract_text_fields, transcribe_audio

router = APIRouter()


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
        transcript = transcribe_audio(tmp_path)
        extracted_fields = extract_text_fields(transcript, tree_ref, prf_number)
    finally:
        os.remove(tmp_path)

    return {"transcript": transcript, "extracted_fields": extracted_fields}
