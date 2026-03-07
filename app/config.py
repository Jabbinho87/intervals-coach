from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CoachConfig(BaseModel):
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
