import os

from fastapi import APIRouter

from excel import build_excel
from models import AerialInspectionSurvey
from state import SURVEYS

router = APIRouter()

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")


@router.post("/survey")
def create_survey(survey: AerialInspectionSurvey):
    output_path = os.path.join(OUTPUT_DIR, f"{survey.survey_id}.xlsm")
    build_excel(survey, output_path)
    SURVEYS[survey.survey_id] = output_path
    return {
        "survey_id": survey.survey_id,
        "download_url": f"/report/{survey.survey_id}/download",
    }
