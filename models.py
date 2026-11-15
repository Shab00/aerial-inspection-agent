import datetime
import uuid

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class PRFFeature(BaseModel):
    prf_number: int
    prf_height_m: float | None = None
    dph_cm: float | None = None
    entrance_height_cm: float | None = None
    entrance_width_cm: float | None = None
    internal_width_cm: float | None = None
    internal_depth_cm: float | None = None
    internal_height_cm: float | None = None
    feature_type: str | None = None
    aspect: str | None = None
    orientation: str | None = None
    droppings: bool = False
    bat_notes: str | None = None
    smell: str | None = None
    substrate: str | None = None
    humidity_condition: str | None = None
    apex_shape: str | None = None
    competitors: str | None = None
    prf_suitability: Literal[
        "PRF-I", "PRF-M", "Negligible", "N/A"
    ] = "N/A"
    inspection_notes_1: str | None = None
    inspection_notes_2: str | None = None
    inspection_notes_3: str | None = None
    photo_path: str | None = None

    @field_validator("prf_number")
    @classmethod
    def validate_prf_number(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("prf_number must be between 1 and 10")
        return v


class TreeSurvey(BaseModel):
    site_name: str
    licence_no: str
    tree_ref: int
    overall_suitability: Literal[
        "PRF-I", "PRF-M", "Negligible"
    ]
    date: str
    habitat: str
    w3w: str | None = None
    tree_species: str
    tree_alive: Literal["Alive", "Dead"] = "Alive"
    dbh_cm: float | None = None
    tree_height_m: float | None = None
    tree_form: Literal[
        "Single stem", "Multi stem", "Coppice"
    ] = "Single stem"
    temperature: float
    cloud_cover: int
    humidity_pct: float
    wind: int
    prfs: list[PRFFeature] = []

    @field_validator("cloud_cover")
    @classmethod
    def validate_cloud(cls, v):
        if not 0 <= v <= 8:
            raise ValueError("Cloud cover must be 0-8")
        return v

    @field_validator("wind")
    @classmethod
    def validate_wind(cls, v):
        if not 0 <= v <= 12:
            raise ValueError("Wind must be 0-12")
        return v

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        return v

    @field_validator("prfs")
    @classmethod
    def validate_unique_prf_numbers(cls, v):
        numbers = [p.prf_number for p in v]
        if len(numbers) != len(set(numbers)):
            raise ValueError("prf_number values must be unique within a tree")
        return v


class AerialInspectionSurvey(BaseModel):
    trees: list[TreeSurvey]
    survey_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = Field(
        default_factory=lambda: datetime.datetime.now().isoformat(timespec="seconds")
    )

    @field_validator("trees")
    @classmethod
    def validate_unique_tree_refs(cls, v):
        refs = [t.tree_ref for t in v]
        if len(refs) != len(set(refs)):
            raise ValueError("tree_ref values must be unique within a survey")
        return v
