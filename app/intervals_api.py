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
    WellnessSummary,
    validate_activity_list,
    validate_planned_workout_list,
    validate_wellness_list,
)


class IntervalsAPIError(Exception):
    """Raised when the API connection or response is not usable."""


@dataclass(slots=True)
class DateRange:
    oldest: str
    newest: str


class IntervalsAPI:
    """
    Small read-only client for the Intervals.icu API.

    This client intentionally only implements GET requests.
    """

    BASE_URL = "https://intervals.icu/api/v1"

    def __init__(self) -> None:
        api_key = getattr(settings, "intervals_api_key", None)
        athlete_id = getattr(settings, "intervals_athlete_id", None)

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
        """Build a full API URL from a relative path."""
        return f"{self.BASE_URL}{path}"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """
        Perform a GET request and return parsed JSON.

        Raises:
            IntervalsAPIError: For auth failures, network failures, or invalid JSON.
        """
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
        """
        Create a simple local-date range for endpoints that require oldest/newest.

        events and wellness commonly use local-date range parameters.
        """
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
        """
        Fetch completed activities.

        If no date range is provided, Intervals usually still returns activities,
        but keeping optional oldest/newest support makes the client more useful.
        """
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

        if limit is not None:
            return items[:limit]
        return items

    def get_planned_workouts(
        self,
        oldest: str | None = None,
        newest: str | None = None,
        calendar_id: int | str | None = None,
    ) -> list[PlannedWorkoutSummary]:
        """
        Fetch planned workouts / calendar events.

        Intervals' events endpoint requires oldest and newest dates.
        If the endpoint fails or returns something unexpected, we fail gracefully
        and return an empty list.
        """
        try:
            if not oldest or not newest:
                date_range = self._default_date_range(days_back=7, days_forward=21)
                oldest = oldest or date_range.oldest
                newest = newest or date_range.newest

            params: dict[str, Any] = {
                "oldest": oldest,
                "newest": newest,
            }
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
                if (item.category or "").upper() == "WORKOUT"
                or (item.type is not None)
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
        """
        Fetch wellness entries.

        The wellness endpoint also commonly uses oldest/newest date parameters.
        If access is not available, return an empty list instead of crashing.
        """
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