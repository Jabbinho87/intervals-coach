from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseIntervalsModel(BaseModel):
    """Base model that tolerates extra fields from the API."""

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
    icu_training_load: float | None = None
    pace: float | None = None
    stream_types: list[str] = Field(default_factory=list)
    description: str | None = None

    @property
    def display_date(self) -> str | None:
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
        return None if self.id is None else str(self.id)


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


class ReadinessAssessment(BaseIntervalsModel):
    score: int
    level: str
    observations: list[str] = Field(default_factory=list)


class SessionAnalysis(BaseIntervalsModel):
    session_type: str
    primary_stimulus: str
    quality: str
    observations: list[str] = Field(default_factory=list)


class PlanningInsight(BaseIntervalsModel):
    summary: str
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)


class TTEAssessment(BaseIntervalsModel):
    modeled_ftp: float | None = None
    estimated_tte_minutes: float | None = None
    level: str = "unknown"
    strengths: list[str] = Field(default_factory=list)
    limiters: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)


class DurabilityAnalysis(BaseIntervalsModel):
    activity_id: str | int | None = None
    session_label: str | None = None
    analyzed_with: str = "none"
    decoupling_percent: float | None = None
    drift_level: str = "unknown"
    fueling_flag: str | None = None
    observations: list[str] = Field(default_factory=list)


class PlanAlignment(BaseIntervalsModel):
    block_focus: str = "unknown"
    expected_week_structure: list[str] = Field(default_factory=list)
    matched_items: list[str] = Field(default_factory=list)
    mismatches: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


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


class CoachReport(BaseIntervalsModel):
    readiness: ReadinessAssessment
    latest_session: SessionAnalysis | None = None
    planning: PlanningInsight | None = None
    tte: TTEAssessment | None = None
    durability: DurabilityAnalysis | None = None
    plan_alignment: PlanAlignment | None = None
    recommendation: CoachRecommendation


def validate_activity_list(items: list[dict[str, Any]]) -> list[ActivitySummary]:
    return [ActivitySummary.model_validate(item) for item in items]


def validate_planned_workout_list(
    items: list[dict[str, Any]],
) -> list[PlannedWorkoutSummary]:
    return [PlannedWorkoutSummary.model_validate(item) for item in items]


def validate_wellness_list(items: list[dict[str, Any]]) -> list[WellnessSummary]:
    return [WellnessSummary.model_validate(item) for item in items]


def validate_power_curve(item: Any) -> PowerCurveSnapshot | None:
    if item is None:
        return None

    if isinstance(item, dict):
        if "points" in item:
            return PowerCurveSnapshot.model_validate(item)

        points: list[PowerCurvePoint] = []
        label = item.get("label")
        snapshot_date = item.get("date")
        modeled_ftp = item.get("modeled_ftp") or item.get("ftp")
        tte = item.get("time_to_exhaustion_seconds") or item.get("tte_seconds")

        for key, value in item.items():
            try:
                duration = int(key)
            except (TypeError, ValueError):
                continue
            if isinstance(value, (int, float)):
                points.append(PowerCurvePoint(duration_seconds=duration, watts=float(value)))
            elif isinstance(value, dict):
                points.append(
                    PowerCurvePoint(
                        duration_seconds=duration,
                        watts=value.get("watts"),
                        watts_per_kg=value.get("watts_per_kg"),
                        source=value.get("source"),
                    )
                )

        points.sort(key=lambda x: x.duration_seconds)
        return PowerCurveSnapshot(
            label=label,
            date=snapshot_date,
            points=points,
            modeled_ftp=modeled_ftp,
            time_to_exhaustion_seconds=tte,
        )

    return None


def validate_history_list(
    items: list[dict[str, Any]],
) -> list[HistoricalTrainingSummary]:
    return [HistoricalTrainingSummary.model_validate(item) for item in items]


def validate_trend_list(items: list[dict[str, Any]]) -> list[PerformanceTrend]:
    return [PerformanceTrend.model_validate(item) for item in items]
