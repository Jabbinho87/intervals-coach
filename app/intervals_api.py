from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException

from app.config import settings
from app.models import (
    ActivitySummary,
    PlannedWorkoutSummary,
    PowerCurveSnapshot,
    WellnessSummary,
    validate_activity_list,
    validate_planned_workout_list,
    validate_power_curve,
    validate_wellness_list,
)


class IntervalsAPIError(Exception):
    """Raised when the API connection or response is not usable."""


@dataclass(slots=True)
class DateRange:
    oldest: str
    newest: str


class IntervalsAPI:
    """Small read-only client for the Intervals.icu API."""

    BASE_URL = "https://intervals.icu/api/v1"

    def __init__(self) -> None:
        api_key = settings.intervals_api_key
        athlete_id = settings.intervals_athlete_id

        if not api_key:
            raise IntervalsAPIError(
                "INTERVALS_API_KEY fehlt. Trage ihn in deiner .env ein."
            )
        if athlete_id is None or athlete_id == "":
            raise IntervalsAPIError(
                "INTERVALS_ATHLETE_ID fehlt. Trage ihn in deiner .env ein."
            )

        self.athlete_id = athlete_id
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth("API_KEY", api_key)
        self.session.headers.update({"Accept": "application/json"})

    def _build_url(self, path: str) -> str:
        return f"{self.BASE_URL}{path}"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = self._build_url(path)
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "?"
            detail = ""
            try:
                detail = exc.response.text[:300] if exc.response is not None else ""
            except Exception:
                detail = ""
            raise IntervalsAPIError(
                f"API-Fehler bei GET {url} (Status {status_code}). {detail}"
            ) from exc
        except RequestException as exc:
            raise IntervalsAPIError(
                f"Netzwerkfehler bei der Verbindung zu Intervals.icu: {exc}"
            ) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise IntervalsAPIError(
                f"Antwort von {url} war kein gültiges JSON."
            ) from exc

    @staticmethod
    def _default_date_range(days_back: int = 30, days_forward: int = 14) -> DateRange:
        today = date.today()
        oldest = today - timedelta(days=days_back)
        newest = today + timedelta(days=days_forward)
        return DateRange(oldest=oldest.isoformat(), newest=newest.isoformat())

    def get_activities(
        self,
        oldest: str | None = None,
        newest: str | None = None,
        limit: int | None = 10,
    ) -> list[ActivitySummary]:
        params: dict[str, Any] = {}
        if oldest:
            params["oldest"] = oldest
        if newest:
            params["newest"] = newest

        raw = self._get(f"/athlete/{self.athlete_id}/activities", params=params)
        if not isinstance(raw, list):
            raise IntervalsAPIError(
                "Unerwartetes Format für Aktivitäten. Erwartet wurde eine Liste."
            )

        items = validate_activity_list(raw)
        items.sort(key=lambda x: x.display_date or "", reverse=True)
        return items[:limit] if limit is not None else items

    def get_activities_for_range(self, days_back: int) -> list[ActivitySummary]:
        date_range = self._default_date_range(days_back=days_back, days_forward=0)
        return self.get_activities(
            oldest=date_range.oldest,
            newest=date_range.newest,
            limit=None,
        )

    def get_planned_workouts(
        self,
        oldest: str | None = None,
        newest: str | None = None,
        calendar_id: int | str | None = None,
    ) -> list[PlannedWorkoutSummary]:
        try:
            if not oldest or not newest:
                date_range = self._default_date_range(days_back=7, days_forward=21)
                oldest = oldest or date_range.oldest
                newest = newest or date_range.newest

            params: dict[str, Any] = {"oldest": oldest, "newest": newest}
            if calendar_id is not None:
                params["calendar_id"] = calendar_id

            raw = self._get(f"/athlete/{self.athlete_id}/events", params=params)
            if not isinstance(raw, list):
                print(
                    "Warnung: Geplante Workouts wurden nicht als Liste zurückgegeben. "
                    "Es wird eine leere Liste verwendet."
                )
                return []

            items = validate_planned_workout_list(raw)
            workout_like = [
                item
                for item in items
                if (item.category or "").upper() == "WORKOUT" or (item.type is not None)
            ]
            workout_like.sort(key=lambda x: x.display_date or "")
            return workout_like
        except IntervalsAPIError as exc:
            print(f"Warnung: Geplante Workouts konnten nicht geladen werden: {exc}")
            return []

    def get_wellness(
        self,
        oldest: str | None = None,
        newest: str | None = None,
    ) -> list[WellnessSummary]:
        try:
            if not oldest or not newest:
                date_range = self._default_date_range(days_back=30, days_forward=0)
                oldest = oldest or date_range.oldest
                newest = newest or date_range.newest

            params = {"oldest": oldest, "newest": newest}
            raw = self._get(f"/athlete/{self.athlete_id}/wellness", params=params)
            if not isinstance(raw, list):
                print(
                    "Warnung: Wellness-Daten wurden nicht als Liste zurückgegeben. "
                    "Es wird eine leere Liste verwendet."
                )
                return []

            items = validate_wellness_list(raw)
            items.sort(key=lambda x: x.display_date or "", reverse=True)
            return items
        except IntervalsAPIError as exc:
            print(f"Warnung: Wellness-Daten konnten nicht geladen werden: {exc}")
            return []

    def get_power_curve(self) -> PowerCurveSnapshot | None:
        try:
            raw = self._get(f"/athlete/{self.athlete_id}/power-curve")
            snapshot = validate_power_curve(raw)
            if snapshot is None:
                print("Warnung: Power-Curve-Daten konnten nicht interpretiert werden.")
            return snapshot
        except IntervalsAPIError as exc:
            print(f"Warnung: Power-Curve-Daten konnten nicht geladen werden: {exc}")
            return None

    def get_activity_details(self, activity_id: str | int) -> dict[str, Any] | None:
        """Fetch a single activity including ICU intervals when available."""
        try:
            raw = self._get(f"/activity/{activity_id}", params={"intervals": "true"})
            return raw if isinstance(raw, dict) else None
        except IntervalsAPIError as exc:
            print(f"Warnung: Aktivitätsdetails konnten nicht geladen werden: {exc}")
            return None

    def get_activity_streams(
        self,
        activity_id: str | int,
        types: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch stream data (e.g. watts/heartrate) for one activity."""
        try:
            params = {}
            if types:
                params["types"] = ",".join(types)
            raw = self._get(f"/activity/{activity_id}/streams.json", params=params)
            return raw if isinstance(raw, dict) else None
        except IntervalsAPIError as exc:
            print(f"Warnung: Aktivitätsstreams konnten nicht geladen werden: {exc}")
            return None
