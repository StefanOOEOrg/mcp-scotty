"""Tests for the HAFAS client (Stage 1: LocMatch and TripSearch).

The fixtures are real responses of the ÖBB endpoint, cut down to the fields the
client needs. `_make_request` is replaced, so no test touches the network.
"""

import json
from datetime import datetime
from pathlib import Path

from mcp_scotty.hafas_client import HAFAS_CONFIGS, HafasClient

FIXTURES = Path(__file__).parent / "fixtures"


def payload(name: str) -> dict:
    """The recorded ``res`` payload of a service call."""
    return json.loads((FIXTURES / name).read_text())


class RecordingClient(HafasClient):
    """A client that records the request and answers with a fixed payload."""

    def __init__(self, response: dict) -> None:
        super().__init__(HAFAS_CONFIGS["oebb"])
        self.response = response
        self.calls: list[tuple[str, dict]] = []

    def _make_request(self, method: str, params: dict) -> dict:
        self.calls.append((method, params))
        return self.response


# --------------------------------------------------------------------------- LocMatch


def test_search_locations_sends_a_lomatch_request():
    client = RecordingClient(payload("locmatch_wien_hbf.json"))

    client.search_locations("Wien Hbf", max_results=3)

    assert len(client.calls) == 1
    method, params = client.calls[0]
    assert method == "LocMatch"
    assert params == {
        "input": {
            "field": "S",
            "loc": {"name": "Wien Hbf", "type": "S"},
            "maxLoc": 3,
        }
    }


def test_search_locations_returns_normalised_matches():
    client = RecordingClient(payload("locmatch_wien_hbf.json"))

    matches = client.search_locations("Wien Hbf", max_results=3)

    assert isinstance(matches, list)
    assert len(matches) == 3
    assert [m["name"] for m in matches] == ["Wien Hbf (U)", "Wr.Neustadt Hbf", "Wien"]
    assert set(matches[0]) == {"id", "name", "ext_id", "type"}
    assert matches[0]["id"] == "A=1@O=Wien Hbf (U)@X=16377950@Y=48184986@U=81@L=1290401@p=1792663957@"
    assert matches[0]["ext_id"] == "1290401"
    assert matches[0]["type"] == "S"


def test_search_locations_without_matches_is_an_empty_list():
    client = RecordingClient({})

    assert client.search_locations("Nirgendwo") == []


# --------------------------------------------------------------------------- TripSearch


def test_get_journeys_sends_a_tripsearch_request():
    client = RecordingClient(payload("tripsearch_wien_salzburg.json"))
    when = datetime(2026, 10, 25, 8, 0)

    client.get_journeys("ORIGIN", "DEST", date=when, max_journeys=2)

    assert len(client.calls) == 1
    method, params = client.calls[0]
    assert method == "TripSearch"
    assert params == {
        "depLocL": [{"lid": "ORIGIN"}],
        "arrLocL": [{"lid": "DEST"}],
        "outDate": "20261025",
        "outTime": "080000",
        "numF": 2,
        "maxChg": 5,
    }


def test_get_journeys_normalises_connections():
    client = RecordingClient(payload("tripsearch_wien_salzburg.json"))

    journeys = client.get_journeys("ORIGIN", "DEST", date=datetime(2026, 10, 25, 8, 0))

    assert len(journeys) == 2
    first = journeys[0]
    assert set(first) == {"id", "departure", "arrival", "duration_minutes", "changes", "legs"}
    assert first["id"] == "C-0"
    assert first["departure"] == "2026-10-25T08:03:00"
    assert first["arrival"] == "2026-10-25T11:08:00"
    assert first["duration_minutes"] == 185
    assert first["changes"] == 1
    assert len(first["legs"]) == 3


def test_get_journeys_maps_legs_with_names_and_lines():
    client = RecordingClient(payload("tripsearch_wien_salzburg.json"))

    legs = client.get_journeys("ORIGIN", "DEST", date=datetime(2026, 10, 25, 8, 0))[0]["legs"]

    assert legs[0] == {
        "type": "JNY",
        "line": "Tram 18",
        "origin": "Wien Hbf (Tiefgeschoß Straßenbahn)",
        "destination": "Wien Westbahnhof (Neubaugürtel Mitte/Westeingang)",
        "departure": "2026-10-25T08:03:00",
        "arrival": "2026-10-25T08:18:00",
    }
    assert legs[1]["type"] == "WALK"
    assert legs[1]["line"] is None
    assert legs[2]["line"] == "WB 906"
    assert legs[2]["destination"] == "Salzburg Hbf"
    assert legs[2]["arrival"] == "2026-10-25T11:08:00"


def test_get_journeys_without_connections_is_an_empty_list():
    client = RecordingClient({})

    assert client.get_journeys("ORIGIN", "DEST") == []


def test_overnight_arrival_uses_the_day_offset_prefix():
    """A time on a later day carries a two-digit day offset: ``01020700`` = 02:07 +1 day."""
    client = RecordingClient(payload("tripsearch_overnight.json"))

    journey = client.get_journeys("ORIGIN", "DEST", date=datetime(2026, 10, 25, 23, 28))[0]

    assert journey["departure"] == "2026-10-25T23:28:00"
    assert journey["arrival"] == "2026-10-26T02:07:00"
    assert journey["duration_minutes"] == 159
    assert journey["legs"][0]["line"] == "EC 462"
    assert journey["legs"][0]["arrival"] == "2026-10-26T02:07:00"
