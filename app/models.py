__future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseIntervalsModel(BaseModel):
    """
    Base model for Intervals.icu responses.

    We ignore extra fields because the API can return many more fields than we
    currently need, and those fields may change over time.
    """

    model_config = ConfigDict(extra="ignore")


class ActivitySummary(BaseIntervalsModel):
    id: str | int | None = None
    name: str | None = None
    type: str | None = None
    start_date_local: str | None = None
    start_date: str | None = None
    distance: float | None = None
    moving_time: float | None = None
    elapsed_time: float | None = None
    average_watts: float | None = None
    weighted_average_watts: float | None = None
    max_watts: float | None = None
    average_heartrate: float | None = None
    max_heartrate: float | None = None
    calories: float | None = None

    @property
    def display_date(self) -> str | None:
        """Return the most useful available date field."""
        return self.start_date_local or self.start_date


class PlannedWorkoutSummary(BaseIntervalsModel):
    id: str | int | None = None
    name: str | None = None
    type: str | None = None
    category: str | None = None
    start_date_local: str | None = None
    end_date_local: str | None = None
    description: str | None = None
    moving_time: float | None = None
    icu_training_load: float | None = None

    @property
    def display_date(self) -> str | None:
        return self.start_date_local


class WellnessSummary(BaseIntervalsModel):
    """
    Wellness fields can vary depending on integrations and account setup.

    We keep this intentionally tolerant.
    """

    id: str | int | None = None
    ctl: float | None = None
    atl: float | None = None
    ramp_rate: float | None = None
    weight: float | None = None
    resting_hr: float | None = None
    hrv: float | None = None
    sleep_secs: float | None = None
    steps: float | None = None
    mood: str | None = None
    soreness: str | None = None
    fatigue: str | None = None
    freshness: str | None = None

    @property
    def display_date(self) -> str | None:
        if self.id is None:
            return None
        return str(self.id)


class PowerCurvePoint(BaseIntervalsModel):
    duration_seconds: int
    watts: float | None = None
    watts_per_kg: float | None = None
    source: str | None = None


class PowerCurveSnapshot(BaseIntervalsModel):
    label: str | None = None
    date: str | None = None
    points: list[PowerCurvePoint] = Field(default_factory=list)
    modeled_ftp: float | None = None
    time_to_exhaustion_seconds: float | None = None
    durability_notes: list[str] = Field(default_factory=list)


class HistoricalTrainingSummary(BaseIntervalsModel):
    period_label: str
    start_date: str | None = None
    end_date: str | None = None
    total_activities: int | None = None
    total_duration_seconds: float | None = None
    total_distance: float | None = None
    total_training_load: float | None = None
    consistency_score: float | None = None
    notes: list[str] = Field(default_factory=list)


class PerformanceTrend(BaseIntervalsModel):
    metric: str
    direction: str | None = None
    change_percent: float | None = None
    timeframe: str | None = None
    summary: str | None = None


class CoachRecommendation(BaseIntervalsModel):
    summary: str
    observations: list[str] = Field(default_factory=list)
    interpretation: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    requires_approval: bool = True
    proposed_write_action: str | None = None


class DashboardSnapshot(BaseIntervalsModel):
    activities: list[ActivitySummary]
    planned_workouts: list[PlannedWorkoutSummary]
    wellness_entries: list[WellnessSummary]
    power_curve: PowerCurveSnapshot | None = None
    history: list[HistoricalTrainingSummary] = Field(default_factory=list)
    trends: list[PerformanceTrend] = Field(default_factory=list)


def validate_activity_list(items: list[dict[str, Any]]) -> list[ActivitySummary]:
    """Convert raw activity JSON objects into ActivitySummary models."""
    return [ActivitySummary.model_validate(item) for item in items]


def validate_planned_workout_list(
    items: list[dict[str, Any]],
) -> list[PlannedWorkoutSummary]:
    """Convert raw event JSON objects into PlannedWorkoutSummary models."""
    return [PlannedWorkoutSummary.model_validate(item) for item in items]


def validate_wellness_list(items: list[dict[str, Any]]) -> list[WellnessSummary]:
    """Convert raw wellness JSON objects into WellnessSummary models."""
    return [WellnessSummary.model_validate(item) for item in items]


def validate_power_curve(
    item: dict[str, Any] | None,
) -> PowerCurveSnapshot | None:
    """Convert a raw power curve JSON object into a PowerCurveSnapshot."""
    if item is None:
        return None
    return PowerCurveSnapshot.model_validate(item)


def validate_history_list(
    items: list[dict[str, Any]],
) -> list[HistoricalTrainingSummary]:
    """Convert raw historical summary JSON objects into models."""
    return [HistoricalTrainingSummary.model_validate(item) for item in items]


def validate_trend_list(items: list[dict[str, Any]]) -> list[PerformanceTrend]:
    """Convert raw performance trend JSON objects into models."""
    return [PerformanceTrend.model_validate(item) for item in items]