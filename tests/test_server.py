"""Tests for the MCP tool layer (WP3b).

The server is driven through the in-process ``Client`` so these tests see exactly
what an MCP client sees, including ``is_error``. ``hafas_client`` is replaced by a
fake, so no test touches the network.
"""

from datetime import datetime

import pytest
from mcp.client import Client

from mcp_scotty import server
from mcp_scotty.profiles import PROFILES

SIX_TOOLS = [
    "list_transit_profiles",
    "set_transit_profile",
    "search_stations",
    "get_journeys",
    "get_departures",
    "get_arrivals",
]

STATION = {
    "id": "A=1@O=Wien Hbf (U)@L=1290401@",
    "name": "Wien Hbf (U)",
    "ext_id": "1290401",
    "type": "S",
}

JOURNEY = {
    "id": "C-0",
    "departure": "2026-10-25T08:03:00",
    "arrival": "2026-10-25T11:08:00",
    "duration_minutes": 185,
    "changes": 1,
    "legs": [
        {
            "type": "JNY",
            "line": "Tram 18",
            "origin": "Wien Hbf (Tiefgeschoß Straßenbahn)",
            "destination": "Wien Westbahnhof (Neugasse)",
            "departure": "2026-10-25T08:03:00",
            "arrival": "2026-10-25T08:18:00",
        },
        {
            "type": "WALK",
            "line": None,
            "origin": "Wien Westbahnhof (Neugasse)",
            "destination": "Wien Westbahnhof",
            "departure": "2026-10-25T08:18:00",
            "arrival": "2026-10-25T08:24:00",
        },
        {
            "type": "JNY",
            "line": "WB 906",
            "origin": "Wien Westbahnhof",
            "destination": "Salzburg Hbf",
            "departure": "2026-10-25T08:38:00",
            "arrival": "2026-10-25T11:08:00",
        },
    ],
}


class FakeClient:
    """Stands in for ``HafasClient`` and records what the handlers ask for."""

    def __init__(self, locations=(), journeys=(), error=None):
        self.locations = list(locations)
        self.journeys = list(journeys)
        self.error = error
        self.calls = []

    def search_locations(self, query, max_results=10):
        self.calls.append(("search_locations", query, max_results))
        if self.error:
            raise self.error
        return self.locations[:max_results]

    def get_journeys(self, origin_id, dest_id, date=None, max_journeys=5):
        self.calls.append(("get_journeys", origin_id, dest_id, date, max_journeys))
        if self.error:
            raise self.error
        return self.journeys[:max_journeys]


@pytest.fixture
def connect(monkeypatch):
    """Install a fake client plus an initialised profile."""

    def _install(fake):
        monkeypatch.setattr(server, "hafas_client", fake)
        monkeypatch.setattr(server, "current_profile", PROFILES["oebb"])
        return fake

    return _install


async def call_tool(name: str, arguments: dict) -> tuple[bool, str]:
    """Call a tool through the in-process MCP client and return (is_error, text)."""
    async with Client(server.app) as client:
        result = await client.call_tool(name, arguments)
    return bool(result.is_error), "\n".join(block.text for block in result.content)


# --------------------------------------------------------------------- tools


async def test_lists_exactly_the_six_tools():
    async with Client(server.app) as client:
        tools = await client.list_tools()

    assert [tool.name for tool in tools.tools] == SIX_TOOLS


async def test_unknown_tool_is_an_error():
    is_error, text = await call_tool("does_not_exist", {})

    assert is_error is True
    assert "Unknown tool: does_not_exist" in text


# ------------------------------------------------------------ search_stations


async def test_search_stations_returns_name_and_id(connect):
    connect(FakeClient(locations=[STATION]))

    is_error, text = await call_tool("search_stations", {"query": "Wien Hbf"})

    assert is_error is False
    assert "Wien Hbf (U)" in text
    assert "A=1@O=Wien Hbf (U)@L=1290401@" in text


async def test_search_stations_passes_query_and_limit(connect):
    fake = connect(FakeClient(locations=[STATION]))

    await call_tool("search_stations", {"query": "Wien Hbf", "max_results": 5})

    assert fake.calls[0] == ("search_locations", "Wien Hbf", 5)


async def test_search_stations_without_matches_is_an_error(connect):
    connect(FakeClient(locations=[]))

    is_error, text = await call_tool("search_stations", {"query": "Nirgendwo"})

    assert is_error is True
    assert "No stations found" in text


async def test_a_failing_client_becomes_an_error_result(connect):
    connect(FakeClient(error=RuntimeError("HAFAS antwortet nicht")))

    is_error, text = await call_tool("search_stations", {"query": "Wien Hbf"})

    assert is_error is True
    assert "HAFAS antwortet nicht" in text


# --------------------------------------------------------------- get_journeys


async def test_get_journeys_formats_connections_and_legs(connect):
    connect(FakeClient(locations=[STATION], journeys=[JOURNEY]))

    is_error, text = await call_tool(
        "get_journeys",
        {
            "origin": "Wien Hbf",
            "destination": "Salzburg Hbf",
            "date": "2026-10-25",
            "time": "08:00",
        },
    )

    assert is_error is False
    assert "08:03" in text and "11:08" in text
    assert "185" in text
    assert "Tram 18" in text
    assert "WB 906" in text
    assert "Salzburg Hbf" in text


async def test_get_journeys_resolves_names_to_ids_and_passes_the_moment(connect):
    fake = connect(FakeClient(locations=[STATION], journeys=[JOURNEY]))

    await call_tool(
        "get_journeys",
        {
            "origin": "Wien Hbf",
            "destination": "Salzburg Hbf",
            "date": "2026-10-25",
            "time": "08:00",
            "max_journeys": 2,
        },
    )

    journey_call = next(c for c in fake.calls if c[0] == "get_journeys")
    assert journey_call[1] == STATION["id"]
    assert journey_call[2] == STATION["id"]
    assert isinstance(journey_call[3], datetime)
    assert journey_call[3] == datetime(2026, 10, 25, 8, 0)
    assert journey_call[4] == 2


async def test_get_journeys_with_unknown_station_is_an_error(connect):
    connect(FakeClient(locations=[]))

    is_error, text = await call_tool(
        "get_journeys", {"origin": "Nirgendwo", "destination": "Salzburg Hbf"}
    )

    assert is_error is True
    assert "Origin station not found: Nirgendwo" in text


async def test_get_journeys_without_connections_is_an_error(connect):
    connect(FakeClient(locations=[STATION], journeys=[]))

    is_error, text = await call_tool(
        "get_journeys", {"origin": "Wien Hbf", "destination": "Salzburg Hbf"}
    )

    assert is_error is True
    assert "No journeys found from Wien Hbf to Salzburg Hbf" in text


# ------------------------------------------------- departures / arrivals: honest


async def test_departures_say_they_are_not_implemented(connect):
    connect(FakeClient())

    is_error, text = await call_tool("get_departures", {"station": "Wien Hbf"})

    assert is_error is True
    assert "not implemented yet" in text
    assert "ÖBB" in text


async def test_arrivals_say_they_are_not_implemented(connect):
    connect(FakeClient())

    is_error, text = await call_tool("get_arrivals", {"station": "Wien Hbf"})

    assert is_error is True
    assert "not implemented yet" in text
    assert "ÖBB" in text
