"""Direct HAFAS API Client - bypassing pyhafas for better control."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)


class HafasError(Exception):
    """A HAFAS call that failed: an API error or an unusable response."""


@dataclass
class HafasConfig:
    """Configuration for HAFAS API endpoint."""

    endpoint: str
    aid: str  # Authentication ID
    client_id: str
    client_name: str
    client_version: str
    api_version: str = "1.16"
    language: str = "de"


# Provider-specific configurations
HAFAS_CONFIGS = {
    "oebb": HafasConfig(
        endpoint="https://fahrplan.oebb.at/bin/mgate.exe",
        aid="OWDL4fE4ixNiPBBm",
        client_id="OEBB",
        client_name="oebbANDROID",
        client_version="100600",
    ),
    "db": HafasConfig(
        endpoint="https://reiseauskunft.bahn.de/bin/mgate.exe",
        aid="n91dB8Z77MLdoR0K",
        client_id="DB",
        client_name="DB Navigator",
        client_version="23040000",
    ),
    "sbb": HafasConfig(
        endpoint="https://fahrplan.sbb.ch/bin/mgate.exe",
        aid="2c4f8620337e48fb",
        client_id="SBB",
        client_name="SBBmobile",
        client_version="6.15.10.8.8",
        language="en",
    ),
    "ns": HafasConfig(
        endpoint="https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips",
        aid="",  # NS uses different auth
        client_id="NS",
        client_name="NS",
        client_version="1.0",
        language="en",
    ),
}


def _iso_time(date: str, time: str) -> str:
    """Combine a HAFAS date (``YYYYMMDD``) and time into ISO 8601.

    Six characters are ``HHMMSS`` on the given day; eight are ``DDHHMMSS``,
    where the first two digits are a day offset (``"01020700"`` is 02:07:00 one
    day later). pyhafas parses it the same way.
    """
    day = datetime.strptime(date, "%Y%m%d")
    # ``DDHHMMSS``: the first two digits are a day offset, not an hour.
    offset, clock = (int(time[:2]), time[2:]) if len(time) > 6 else (0, time)
    hours, minutes, seconds = int(clock[0:2]), int(clock[2:4]), int(clock[4:6])
    stamp = day + timedelta(days=offset, hours=hours, minutes=minutes, seconds=seconds)
    return stamp.strftime("%Y-%m-%dT%H:%M:%S")


def _minutes(duration: str) -> int:
    """Minutes of a HAFAS ``HHMMSS`` duration (``"030500"`` is 185)."""
    if not duration:
        return 0
    return int(duration[0:2]) * 60 + int(duration[2:4])


class HafasClient:
    """Direct HAFAS API client."""

    def __init__(self, config: HafasConfig, disable_ssl_verify: bool = False):
        """Initialize HAFAS client.

        Args:
            config: HAFAS configuration for specific provider
            disable_ssl_verify: Disable SSL verification (for testing only)
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Accept-Charset": "utf-8",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/json",
                "User-Agent": "mcp-scotty/0.5.0",
            }
        )
        self.disable_ssl_verify = disable_ssl_verify

        if disable_ssl_verify:
            logger.warning("SSL verification is DISABLED - only use for testing!")
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Make a request to HAFAS API.

        Args:
            method: HAFAS method name (e.g., 'LocMatch', 'TripSearch')
            params: Method-specific parameters

        Returns:
            Response dictionary

        Raises:
            HafasError: the service reported an error, or the envelope carries no
                service result at all (the API answers some bad request bodies with
                an empty ``svcResL`` and no error).
        """
        # Build request body
        request_body = {
            "auth": {"type": "AID", "aid": self.config.aid},
            "client": {
                "id": self.config.client_id,
                "name": self.config.client_name,
                "type": "AND",
                "v": self.config.client_version,
            },
            "ver": self.config.api_version,
            "lang": self.config.language,
            "svcReqL": [{"meth": method, "req": params}],
        }

        logger.debug(f"HAFAS request: {method} to {self.config.endpoint}")

        try:
            response = self.session.post(
                self.config.endpoint,
                json=request_body,
                verify=not self.disable_ssl_verify,
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()

            # A missing or empty svcResL is a failed call, not an empty result.
            if not data.get("svcResL"):
                raise HafasError("HAFAS returned no service result")

            svc_res = data["svcResL"][0]
            if svc_res.get("err") != "OK":
                error_msg = svc_res.get("errTxt", "Unknown error")
                raise HafasError(f"HAFAS error: {error_msg}")
            return svc_res.get("res", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            logger.error(f"Response text: {response.text[:500]}")
            raise HafasError("HAFAS API returned invalid JSON") from e

    def search_locations(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Find stations matching a free-text query.

        Args:
            query: Station or place name, e.g. "Wien Hbf".
            max_results: Maximum number of matches.

        Returns:
            A list of dicts, each with exactly these keys:
            ``id`` (the HAFAS location id, called ``lid`` in the response),
            ``name`` (display name), ``ext_id`` (the provider's external id as a
            string) and ``type`` (the HAFAS location type, e.g. ``"S"``).
            No match is an empty list, not an error.

        Request:
            Service ``LocMatch`` with the body
            ``{"input": {"field": "S", "loc": {"name": query, "type": "S"},
            "maxLoc": max_results}}``; the matches are ``res["match"]["locL"]``.

        Raises:
            Exception: whatever ``_make_request`` raises (network, HAFAS error).
        """
        params = {
            "input": {
                "field": "S",
                "loc": {"name": query, "type": "S"},
                "maxLoc": max_results,
            }
        }
        response = self._make_request("LocMatch", params)
        return [self._location(loc) for loc in response.get("match", {}).get("locL", [])]

    @staticmethod
    def _location(loc: dict[str, Any]) -> dict[str, Any]:
        """Normalise one ``LocMatch`` location."""
        ext_id = loc.get("extId")
        return {
            "id": loc.get("lid"),
            "name": loc.get("name"),
            "ext_id": str(ext_id) if ext_id is not None else None,
            "type": loc.get("type"),
        }

    def get_journeys(
        self, origin_id: str, dest_id: str, date: datetime | None = None, max_journeys: int = 5
    ) -> list[dict[str, Any]]:
        """Find connections between two stations.

        Args:
            origin_id: HAFAS location id of the origin (``id`` from
                :meth:`search_locations`).
            dest_id: HAFAS location id of the destination.
            date: Departure date and time; ``None`` means now.
            max_journeys: Maximum number of connections.

        Returns:
            A list of dicts:
            ``id`` (HAFAS connection id, the ``cid``),
            ``departure`` and ``arrival`` (ISO 8601 local time, e.g.
            ``"2026-10-25T08:03:00"``),
            ``duration_minutes`` (int), ``changes`` (int),
            ``legs``: a list of dicts with ``type`` (``"JNY"`` or ``"WALK"``),
            ``line`` (the product name like ``"Tram 18"``, ``None`` for a walk),
            ``origin`` and ``destination`` (station names), and
            ``departure``/``arrival`` (ISO 8601).
            No connection is an empty list, not an error.

        Request:
            Service ``TripSearch`` with
            ``{"depLocL": [{"lid": origin_id}], "arrLocL": [{"lid": dest_id}],
            "outDate": date.strftime("%Y%m%d"), "outTime": date.strftime("%H%M%S"),
            "numF": max_journeys, "maxChg": 5}``; the connections are
            ``res["outConL"]``.

        Notes for the implementation:
            * The connection carries its date as ``YYYYMMDD`` and its times as
              ``dTimeS``/``aTimeS`` (``HHMMSS``) on ``dep``/``arr``; legs carry
              their own ``dep``/``arr`` with the same shape.
            * A time on a later day carries a **two-digit day offset in front**
              (``DDHHMMSS``): ``"01020700"`` is 02:07:00 one day after the
              connection date. Six-character times (``HHMMSS``) are on the
              connection day itself. This is the convention pyhafas documents
              (``dateOffset = int(time[:2]) if len(time) > 6``).
            * Station names are indexes: ``locX`` into ``res["common"]["locL"]``;
              line names are ``prodX`` into ``res["common"]["prodL"]`` (key
              ``name``). A leg without ``jny`` is a walk and has no line.

        Raises:
            Exception: whatever ``_make_request`` raises (network, HAFAS error).
        """
        when = date or datetime.now()
        params = {
            "depLocL": [{"lid": origin_id}],
            "arrLocL": [{"lid": dest_id}],
            "outDate": when.strftime("%Y%m%d"),
            "outTime": when.strftime("%H%M%S"),
            "numF": max_journeys,
            "maxChg": 5,
        }
        response = self._make_request("TripSearch", params)
        common = response.get("common", {})
        locations = common.get("locL", [])
        products = common.get("prodL", [])
        return [self._connection(con, locations, products) for con in response.get("outConL", [])]

    def get_station_board(
        self,
        station_id: str,
        board_type: str = "DEP",
        date: datetime | None = None,
        time: datetime | None = None,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Departures from or arrivals at one station.

        Args:
            station_id: HAFAS location id of the station (``id`` from
                :meth:`search_locations`).
            board_type: ``"DEP"`` for departures, ``"ARR"`` for arrivals.
            date: Day of the board; ``None`` means today.
            time: Moment of the board; ``None`` means now.
            max_results: Maximum number of rows.

        Returns:
            A list of dicts, one per row, in the order the backend returned them
            (already time-ordered):
            ``line`` (the product name like ``"EC 101"``), ``category`` (e.g.
            ``"Eurocity"``, ``None`` when the product carries none), ``direction``
            (``dirTxt``, for a departure where the train goes, for an arrival where
            it comes from), ``time`` and ``planned_time`` (both the planned instant
            as ISO 8601, ``"2026-11-16T10:00:00"``) and ``platform`` (the planned
            platform as a plain string like ``"6A-B"``, ``None`` when absent).
            No rows is an empty list, not an error.

        Request:
            Service ``StationBoard`` with
            ``{"type": board_type, "stbLoc": {"lid": station_id, "type": "S"},
            "date": date.strftime("%Y%m%d"), "time": time.strftime("%H%M%S"),
            "maxJny": max_results}``; the rows are ``res["jnyL"]``. The station
            goes into ``stbLoc`` — a ``loc`` field is answered with an empty
            ``svcResL``.

        Notes:
            * A row carries its **own** day in ``date`` (``YYYYMMDD``) and its
              times in ``stbStop`` as ``dTimeS`` (departure) or ``aTimeS``
              (arrival), with the ``DDHHMMSS`` day offset of :meth:`get_journeys`;
              use the row's day, not the requested one.
            * ``prodX`` indexes ``res["common"]["prodL"]``; the platform comes from
              ``dPlatfS``/``aPlatfS``. Real-time values (``dTimeR``, ``dPlatfR``)
              are not used.

        Raises:
            ValueError: ``board_type`` is neither ``"DEP"`` nor ``"ARR"``.
            Exception: whatever ``_make_request`` raises (network, HAFAS error).
        """
        if board_type not in ("DEP", "ARR"):
            raise ValueError(f"Unknown board type: {board_type}")

        now = datetime.now()
        params = {
            "type": board_type,
            "stbLoc": {"lid": station_id, "type": "S"},
            "date": (date or now).strftime("%Y%m%d"),
            "time": (time or now).strftime("%H%M%S"),
            "maxJny": max_results,
        }
        response = self._make_request("StationBoard", params)
        products = response.get("common", {}).get("prodL", [])
        return [
            self._board_entry(entry, products, board_type) for entry in response.get("jnyL", [])
        ]

    @classmethod
    def _connection(
        cls,
        con: dict[str, Any],
        locations: list[dict[str, Any]],
        products: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Normalise one ``TripSearch`` connection."""
        day = con["date"]
        return {
            "id": con.get("cid"),
            "departure": _iso_time(day, con["dep"]["dTimeS"]),
            "arrival": _iso_time(day, con["arr"]["aTimeS"]),
            "duration_minutes": _minutes(con.get("dur", "")),
            "changes": int(con.get("chg", 0)),
            "legs": [cls._leg(sec, day, locations, products) for sec in con.get("secL", [])],
        }

    @staticmethod
    def _leg(
        sec: dict[str, Any],
        day: str,
        locations: list[dict[str, Any]],
        products: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Normalise one section of a connection; no ``jny`` means a walk."""
        prod_x = (sec.get("jny") or {}).get("prodX")
        return {
            "type": sec.get("type"),
            "line": products[int(prod_x)]["name"] if prod_x is not None else None,
            "origin": locations[int(sec["dep"]["locX"])]["name"],
            "destination": locations[int(sec["arr"]["locX"])]["name"],
            "departure": _iso_time(day, sec["dep"]["dTimeS"]),
            "arrival": _iso_time(day, sec["arr"]["aTimeS"]),
        }

    @staticmethod
    def _board_entry(
        entry: dict[str, Any],
        products: list[dict[str, Any]],
        board_type: str,
    ) -> dict[str, Any]:
        """Normalise one ``StationBoard`` row; only the planned values are used."""
        stop = entry.get("stbStop", {})
        prefix = "d" if board_type == "DEP" else "a"
        planned = _iso_time(entry["date"], stop[f"{prefix}TimeS"])
        prod_x = entry.get("prodX")
        index = int(prod_x) if prod_x is not None else -1
        product = products[index] if 0 <= index < len(products) else {}
        return {
            "line": product.get("name"),
            "category": (product.get("prodCtx") or {}).get("catOutL"),
            "direction": entry.get("dirTxt"),
            "time": planned,
            "planned_time": planned,
            "platform": stop.get(f"{prefix}PlatfS"),
        }
