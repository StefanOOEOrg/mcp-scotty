"""MCP Server for Public Transit Information across Europe via HAFAS API."""

import logging
import os
import ssl
from datetime import datetime
from typing import Any

from mcp.server.lowlevel import Server
from mcp.types import CallToolRequestParams, CallToolResult, ListToolsResult, TextContent, Tool

from .hafas_client import HAFAS_CONFIGS, HafasClient
from .profiles import TransitProfile, get_profile, list_profiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for current profile and client
current_profile: TransitProfile | None = None
hafas_client: HafasClient | None = None



class ToolFailure(Exception):
    """A tool call that failed for a reason the caller should see."""


def initialize_client(profile_name: str | None = None) -> bool:
    """Initialize HAFAS client with specified profile.

    Args:
        profile_name: Name of the profile to use (e.g., 'oebb', 'db', 'sbb', 'ns')
                     If None, uses TRANSIT_PROFILE env variable or defaults to 'oebb'

    Returns:
        True if initialization successful, False otherwise
    """
    global current_profile, hafas_client

    # Determine profile to use
    if profile_name is None:
        profile_name = os.getenv("TRANSIT_PROFILE", "oebb")

    # Get profile configuration
    profile = get_profile(profile_name)
    if profile is None:
        logger.error(f"Unknown profile: {profile_name}")
        return False

    # Get HAFAS configuration
    hafas_config = HAFAS_CONFIGS.get(profile.hafas_profile_id)
    if hafas_config is None:
        logger.error(f"No HAFAS configuration for profile: {profile.hafas_profile_id}")
        return False

    try:
        current_profile = profile

        # Check if SSL verification should be disabled
        disable_ssl = os.getenv("TRANSIT_DISABLE_SSL_VERIFY", "false").lower() == "true"

        # Initialize our custom HAFAS client
        hafas_client = HafasClient(hafas_config, disable_ssl_verify=disable_ssl)

        logger.info(
            f"HAFAS client initialized successfully with {profile.name} profile "
            f"(SSL verify: {not disable_ssl})"
        )
        return True
    except Exception as e:  # noqa: BLE001  # startup: never crash on an init failure
        logger.error(f"Failed to initialize HAFAS client: {e}")
        hafas_client = None
        return False


# Initialize on module load
initialize_client()


async def handle_list_tools(ctx, params) -> ListToolsResult:
    """Return the tool definitions."""
    return ListToolsResult(tools=[
        Tool(
            name="list_transit_profiles",
            description=(
                "List all available transit provider profiles (ÖBB, DB, SBB, NS, etc.). "
                "Shows which countries and providers are supported."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="set_transit_profile",
            description=(
                "Switch to a different transit provider profile. "
                "Use 'oebb' for Austria, 'db' for Germany, 'sbb' for Switzerland, "
                "'ns' for Netherlands, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "profile": {
                        "type": "string",
                        "description": "Profile ID (e.g., 'oebb', 'db', 'sbb', 'ns')",
                    },
                },
                "required": ["profile"],
            },
        ),
        Tool(
            name="search_stations",
            description=(
                "Search for train/transit stations by name. "
                "Returns station names, IDs, and locations. "
                "Use this to find station IDs needed for journey planning."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Station name or partial name to search for",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_journeys",
            description=(
                "Find transit connections between two stations. "
                "Returns journey options with departure/arrival times, transfers, and durations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Origin station name or ID",
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination station name or ID",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date for journey (YYYY-MM-DD format, optional, defaults to today)",
                    },
                    "time": {
                        "type": "string",
                        "description": "Time for journey (HH:MM format, optional, defaults to now)",
                    },
                    "max_journeys": {
                        "type": "integer",
                        "description": "Maximum number of journey options to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["origin", "destination"],
            },
        ),
        Tool(
            name="get_departures",
            description=(
                "Get upcoming departures from a specific station. "
                "Shows train/bus number, destination, platform, and departure time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "station": {
                        "type": "string",
                        "description": "Station name or ID to get departures from",
                    },
                    "max_departures": {
                        "type": "integer",
                        "description": "Maximum number of departures to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["station"],
            },
        ),
        Tool(
            name="get_arrivals",
            description=(
                "Get upcoming arrivals at a specific station. "
                "Shows train/bus number, origin, platform, and arrival time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "station": {
                        "type": "string",
                        "description": "Station name or ID to get arrivals for",
                    },
                    "max_arrivals": {
                        "type": "integer",
                        "description": "Maximum number of arrivals to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["station"],
            },
        ),
    ])


async def _dispatch(name: str, arguments: dict[str, Any]) -> tuple[list[TextContent], bool]:
    """Handle tool calls for transit information."""
    # Handle profile management tools
    if name == "list_transit_profiles":
        return await handle_list_profiles(), False
    elif name == "set_transit_profile":
        return await handle_set_profile(arguments), False

    # Check if HAFAS client is available for other tools
    if hafas_client is None:
        error_msg = get_error_message("unavailable")
        return [TextContent(type="text", text=error_msg)], True

    try:
        if name == "search_stations":
            return await search_stations(arguments), False
        elif name == "get_journeys":
            return await get_journeys(arguments), False
        elif name == "get_departures":
            return await get_departures(arguments), False
        elif name == "get_arrivals":
            return await get_arrivals(arguments), False
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")], True
    except ToolFailure as exc:
        return [TextContent(type="text", text=str(exc))], True
    except ssl.SSLError:
        logger.exception(f"SSL error in tool {name}")
        error_msg = get_error_message("ssl")
        return [TextContent(type="text", text=error_msg)], True
    except Exception as e:
        logger.exception(f"Error executing tool {name}")
        error_msg = get_error_message("general", str(e))
        return [TextContent(type="text", text=error_msg)], True


async def handle_call_tool(ctx, params: CallToolRequestParams) -> CallToolResult:
    """Dispatch a tool call and wrap the result for the mcp 2.x API."""
    content, is_error = await _dispatch(params.name, params.arguments or {})
    return CallToolResult(content=content, is_error=is_error)


def get_error_message(error_type: str, technical_detail: str = "") -> str:
    """Get appropriate error message based on current profile and error type."""
    if current_profile is None:
        provider_info = "the transit provider"
        website = "your transit provider's website"
    else:
        provider_info = current_profile.name
        # Provider-specific websites
        websites = {
            "oebb": "https://www.oebb.at",
            "db": "https://www.bahn.de",
            "sbb": "https://www.sbb.ch",
            "ns": "https://www.ns.nl",
        }
        website = websites.get(current_profile.name.lower(), "your transit provider's website")

    if error_type == "unavailable":
        return (
            f"⚠️ The {provider_info} transit service is currently unavailable.\n\n"
            f"This may be due to SSL certificate issues or network problems. "
            f"Please use alternative resources:\n\n"
            f"- **Official Website**: {website}\n"
            f"- **Mobile App**: Available for your transit provider\n\n"
            f"Technical note: HAFAS client could not be initialized."
        )
    elif error_type == "ssl":
        return (
            f"⚠️ SSL certificate error when accessing {provider_info} database.\n\n"
            f"The connection could not be established due to certificate issues. "
            f"Please use alternative resources:\n\n"
            f"- **Official Website**: {website}\n"
            f"- **Mobile App**: Check your app store\n\n"
            f"Technical error: SSL certificate verification failed"
        )
    else:  # general
        return (
            f"⚠️ Technical problem retrieving {provider_info} information.\n\n"
            f"Unfortunately, the information could not be retrieved. "
            f"Please try:\n\n"
            f"- **Official Website**: {website}\n"
            f"- **Mobile App**: Available for download\n\n"
            f"Technical error: {technical_detail}"
        )


async def handle_list_profiles() -> list[TextContent]:
    """List all available transit profiles."""
    profiles = list_profiles()

    result = "# Available Transit Profiles\n\n"
    result += f"**Current profile**: {current_profile.name if current_profile else 'None'}\n\n"

    for profile in profiles:
        result += f"### {profile['id']}\n"
        result += f"- **Name**: {profile['name']}\n"
        result += f"- **Country**: {profile['country']}\n"
        result += f"- **Description**: {profile['description']}\n"
        result += f"- **Language**: {profile['language']}\n\n"

    result += "\nUse `set_transit_profile` to switch between profiles."

    return [TextContent(type="text", text=result)]


async def handle_set_profile(arguments: dict) -> list[TextContent]:
    """Set the active transit profile."""
    profile_name = arguments["profile"]

    if initialize_client(profile_name):
        return [TextContent(
            type="text",
            text=f"✓ Successfully switched to {current_profile.name} ({current_profile.country})"
        )]
    else:
        available = ", ".join(list_profiles())
        return [TextContent(
            type="text",
            text=f"✗ Failed to switch to profile '{profile_name}'. Available profiles: {available}"
        )]


async def search_stations(arguments: dict) -> list[TextContent]:
    """Search for transit stations."""
    query = arguments["query"]
    max_results = arguments.get("max_results", 10)

    logger.info(f"Searching for stations: {query} (profile: {current_profile.name})")

    try:
        locations = hafas_client.search_locations(query, max_results)
    except Exception as e:
        logger.exception(f"Error searching stations: {query}")
        raise ToolFailure(f"Error searching stations: {e}") from e

    if not locations:
        raise ToolFailure(
            f"No stations found for query: {query} (using {current_profile.name} profile)"
        )

    # Format results
    results = []
    for location in locations[:max_results]:
        name = location.get("name", "Unknown")
        station_id = location.get("id", "N/A")

        station_info = f"**{name}**\n"
        station_info += f"- ID: `{station_id}`\n"
        results.append(station_info)

    result_text = f"Found {len(results)} station(s) for '{query}' ({current_profile.name}):\n\n"
    result_text += "\n".join(results)
    return [TextContent(type="text", text=result_text)]


async def get_journeys(arguments: dict) -> list[TextContent]:
    """Connections between two stations, for the given date and time.

    Arguments: ``origin`` and ``destination`` (station names), optional ``date``
    (YYYY-MM-DD), ``time`` (HH:MM) and ``max_journeys`` (default 3).

    Implementation:
        1. Resolve both names with ``hafas_client.search_locations(name, 1)``.
        2. ``raise ToolFailure(f"Origin station not found: {origin}")`` (and the
           destination equivalent) when nothing matches.
        3. Build the departure moment from ``date``/``time`` (missing parts: today
           and now) and call
           ``hafas_client.get_journeys(origin_id, dest_id, date=when, max_journeys=n)``.
        4. No connection ->
           ``raise ToolFailure(f"No journeys found from {origin} to {destination}")``.
        5. Otherwise one ``TextContent``: a heading, then per connection a line
           with departure and arrival (``HH:MM``), the duration in minutes and the
           number of changes, followed by its legs — each ``JNY`` leg with its line
           name and ``origin -> destination``, each ``WALK`` leg marked as a walk.
           Every name from the normalised dicts has to appear in the text.
    """
    origin = arguments["origin"]
    destination = arguments["destination"]
    max_journeys = arguments.get("max_journeys", 3)
    when = _departure_moment(arguments.get("date"), arguments.get("time"))

    origin_id = _resolve_station(origin, "Origin")
    dest_id = _resolve_station(destination, "Destination")

    journeys = hafas_client.get_journeys(
        origin_id, dest_id, date=when, max_journeys=max_journeys
    )
    if not journeys:
        raise ToolFailure(f"No journeys found from {origin} to {destination}")

    return [TextContent(
        type="text",
        text=_format_journeys(origin, destination, journeys),
    )]


def _resolve_station(name: str, label: str) -> str:
    """Resolve a station name to its HAFAS id, or fail with a clear message."""
    matches = hafas_client.search_locations(name, 1)
    if not matches:
        raise ToolFailure(f"{label} station not found: {name}")
    return matches[0]["id"]


def _departure_moment(date: str | None, time: str | None) -> datetime:
    """Build the departure moment; a missing date means today, a missing time now."""
    now = datetime.now()
    day = datetime.strptime(date, "%Y-%m-%d") if date else now
    if time:
        clock = datetime.strptime(time, "%H:%M")
        hour, minute = clock.hour, clock.minute
    else:
        hour, minute = now.hour, now.minute
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _clock(stamp: str) -> str:
    """``HH:MM`` of an ISO 8601 timestamp."""
    return datetime.fromisoformat(stamp).strftime("%H:%M")


def _format_journeys(origin: str, destination: str, journeys: list[dict]) -> str:
    """Render the connections as Markdown, one block per connection."""
    lines = [f"# Connections from {origin} to {destination}", ""]
    for index, journey in enumerate(journeys, 1):
        lines.append(
            f"{index}. {_clock(journey['departure'])} -> {_clock(journey['arrival'])} "
            f"({journey['duration_minutes']} min, {journey['changes']} change(s))"
        )
        for leg in journey["legs"]:
            lines.append(f"   - {_format_leg(leg)}")
        lines.append("")
    return "\n".join(lines)


def _format_leg(leg: dict) -> str:
    """One leg as ``line: origin -> destination``, or ``Walk: origin -> destination``."""
    route = f"{leg['origin']} -> {leg['destination']}"
    if leg["type"] == "WALK":
        return f"Walk: {route}"
    return f"{leg['line']}: {route}"



async def get_departures(arguments: dict) -> list[TextContent]:
    """Departures from one station - not implemented yet (Stage 2).

    Arguments: ``station`` (name), optional ``max_departures`` (default 10).

    The station board of the HAFAS API returns no data yet, so this tool fails
    honestly instead of pretending:
    ``raise ToolFailure("The station board is not implemented yet for "
    f"{current_profile.name}; use get_journeys or search_stations instead.")``.
    It must not answer with an empty list.
    """
    raise ToolFailure(
        "The station board is not implemented yet for "
        f"{current_profile.name}; use get_journeys or search_stations instead."
    )



async def get_arrivals(arguments: dict) -> list[TextContent]:
    """Arrivals at one station - not implemented yet (Stage 2).

    Arguments: ``station`` (name), optional ``max_arrivals`` (default 10).

    Same rule as :func:`get_departures`: ``raise ToolFailure("The station board is
    not implemented yet for " f"{current_profile.name}; use get_journeys or
    search_stations instead.")`` instead of returning an empty list.
    """
    raise ToolFailure(
        "The station board is not implemented yet for "
        f"{current_profile.name}; use get_journeys or search_stations instead."
    )



# Built after the handlers so the 2.x constructor can bind them.
app = Server(
    "scotty",
    version="0.3.0",
    on_list_tools=handle_list_tools,
    on_call_tool=handle_call_tool,
)


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
