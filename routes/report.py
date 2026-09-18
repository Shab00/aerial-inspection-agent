import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from state import SURVEYS

router = APIRouter()

XLSM_MEDIA_TYPE = "application/vnd.ms-excel.sheet.macroEnabled.12"


@router.get("/report/{survey_id}/download")
def download_report(survey_id: str):
    path = SURVEYS.get(survey_id)
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(
        path,
        media_type=XLSM_MEDIA_TYPE,
        filename=os.path.basename(path),
    )
