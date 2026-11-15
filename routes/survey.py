import os

from fastapi import APIRouter, HTTPException

from excel import build_excel
from models import AerialInspectionSurvey
from routes.photos import UPLOADS_DIR
from state import SURVEY_DATA, SURVEYS

router = APIRouter()

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


def _build(survey_id: str, survey: AerialInspectionSurvey) -> str:
    output_path = os.path.join(OUTPUT_DIR, f"{survey_id}.xlsm")
    photos_dir = os.path.join(UPLOADS_DIR, survey_id)
    build_excel(survey, output_path, photos_dir=photos_dir)
    SURVEYS[survey_id] = output_path
    return output_path


@router.post("/survey")
def create_survey(survey: AerialInspectionSurvey):
    SURVEY_DATA[survey.survey_id] = survey.model_dump()
    _build(survey.survey_id, survey)
    return {
        "survey_id": survey.survey_id,
        "download_url": f"/report/{survey.survey_id}/download",
    }


@router.post("/survey/{survey_id}/rebuild")
def rebuild_survey(survey_id: str):
    if survey_id not in SURVEY_DATA:
        raise HTTPException(status_code=404, detail="survey not found")
    survey = AerialInspectionSurvey(**SURVEY_DATA[survey_id])
    _build(survey_id, survey)
    return {
        "survey_id": survey_id,
        "download_url": f"/report/{survey_id}/download",
    }
