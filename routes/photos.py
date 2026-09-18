import os

from fastapi import APIRouter, File, UploadFile

router = APIRouter()

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


@router.post("/photos/{survey_id}/{tree_ref}/{prf_number}")
async def upload_photo(
    survey_id: str,
    tree_ref: int,
    prf_number: int,
    photo: UploadFile = File(...),
):
    survey_dir = os.path.join(UPLOADS_DIR, survey_id)
    os.makedirs(survey_dir, exist_ok=True)

    ext = os.path.splitext(photo.filename or "")[1] or ".jpg"
    filename = f"T{tree_ref}_PRF{prf_number}{ext}"
    photo_path = os.path.join(survey_dir, filename)

    with open(photo_path, "wb") as f:
        f.write(await photo.read())

    return {"photo_path": photo_path}
