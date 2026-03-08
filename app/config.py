from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


# Load .env from the project root if present.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class CoachConfig(BaseModel):
    """Feature flags and default lookback windows for the coach."""

    model_config = ConfigDict(extra="ignore")

    write_mode: bool = False
    enable_wellness: bool = True
    enable_power_curve: bool = True
    enable_history: bool = True
    enable_performance_trends: bool = True

    recent_days: int = 7
    medium_range_days: int = 28
    season_days: int = 180

    approval_required_for_writes: bool = True


class Settings(BaseModel):
    """Runtime settings loaded from environment variables."""

    model_config = ConfigDict(extra="ignore")

    intervals_api_key: str | None = None
    intervals_athlete_id: str | None = None
    log_level: str = "INFO"
    coach: CoachConfig = Field(default_factory=CoachConfig)



def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


settings = Settings(
    intervals_api_key=os.getenv("INTERVALS_API_KEY"),
    intervals_athlete_id=os.getenv("INTERVALS_ATHLETE_ID"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    coach=CoachConfig(
        write_mode=_parse_bool(os.getenv("INTERVALS_WRITE_ENABLED"), False),
        approval_required_for_writes=_parse_bool(
            os.getenv("INTERVALS_REQUIRE_APPROVAL"), True
        ),
        enable_wellness=_parse_bool(os.getenv("ENABLE_WELLNESS"), True),
        enable_power_curve=_parse_bool(os.getenv("ENABLE_POWER_CURVE"), True),
        enable_history=_parse_bool(os.getenv("ENABLE_HISTORY"), True),
        enable_performance_trends=_parse_bool(
            os.getenv("ENABLE_PERFORMANCE_TRENDS"), True
        ),
        recent_days=int(os.getenv("RECENT_DAYS", "7")),
        medium_range_days=int(os.getenv("MEDIUM_RANGE_DAYS", "28")),
        season_days=int(os.getenv("SEASON_DAYS", "180")),
    ),
)
