from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import audio, health, photos, report, survey

app = FastAPI(title="Aerial Inspection Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(survey.router)
app.include_router(audio.router)
app.include_router(photos.router)
app.include_router(report.router)
app.include_router(health.router)
