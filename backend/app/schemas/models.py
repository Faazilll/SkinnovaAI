from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Questionnaire(BaseModel):
    age: int = Field(25, ge=10, le=90)
    gender: str = "female"
    menstrual_cycle: str = "regular"
    pcos: bool = False
    thyroid_status: str = "normal"
    pregnancy: bool = False
    medications: str = "none"
    sleep_hours: float = Field(7.0, ge=0, le=24)
    diet_quality: str = "average"
    water_intake_liters: float = Field(2.0, ge=0, le=10)
    exercise_frequency: str = "1-2_week"
    stress_level: int = Field(5, ge=1, le=10)
    smoking: bool = False
    alcohol: str = "none"
    skincare_consistency: str = "inconsistent"
    location_type: str = "suburban"
    pollution_level: str = "moderate"
    sun_exposure: str = "moderate"
    humidity: str = "moderate"
    climate: str = "temperate"
    outdoor_ratio: float = Field(0.3, ge=0, le=1)
    ac_heating_exposure: str = "moderate"


class ImagePrediction(BaseModel):
    severity: int
    severity_label: str
    class_probabilities: dict[str, float]
    risk_percent: float
    oiliness: float
    pores: float
    redness: float
    dark_spots: float
    current_skin_condition: str
    problem_areas: list[str]
    face_detected: bool
    method: str


class DataPrediction(BaseModel):
    hormonal_score: float
    lifestyle_score: float
    environmental_score: float
    combined_score: float
    drivers: list[str]
    method: str
    rule_engine_reference: Optional[dict[str, Any]] = None
    answers: Optional[dict[str, Any]] = None


class FusionRequest(BaseModel):
    image: dict[str, Any]
    data: dict[str, Any]


class RecalculateRequest(BaseModel):
    image: dict[str, Any]
    questionnaire: dict[str, Any]



class HealthResponse(BaseModel):
    status: str
    image_model_loaded: bool
    data_model_loaded: bool
    active_image_model: Optional[str] = None
    active_data_model: Optional[str] = None
    db_connected: Optional[bool] = True
