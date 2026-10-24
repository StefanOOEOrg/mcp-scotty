"""MCP Server for Public Transit Information across Europe via HAFAS API."""

import logging
import ssl
import os
from datetime import datetime
from typing import Any, Optional

from mcp.server.lowlevel import Server
from mcp.types import CallToolRequestParams, CallToolResult, ListToolsResult, TextContent, Tool

from .hafas_client import HafasClient, HAFAS_CONFIGS
from .profiles import get_profile, list_profiles, TransitProfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for current profile and client
current_profile: Optional[TransitProfile] = None
hafas_client: Optional[HafasClient] = None


def initialize_client(profile_name: str = None) -> bool:
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
    except Exception as e:
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
    except ssl.SSLError as e:
        logger.error(f"SSL error in tool {name}: {e}", exc_info=True)
        error_msg = get_error_message("ssl")
        return [TextContent(type="text", text=error_msg)], True
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
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

        if not locations:
            return [TextContent(
                type="text",
                text=f"No stations found for query: {query} (using {current_profile.name} profile)"
            )]

        # Format results
        results = []
        for location in locations[:max_results]:
            # Extract name from location dict
            name = location.get('name', 'Unknown')
            lid = location.get('lid', location.get('extId', 'N/A'))

            station_info = f"**{name}**\n"
            station_info += f"- ID: `{lid}`\n"

            # Check for coordinates
            if 'crd' in location:
                crd = location['crd']
                lat = crd.get('y', 0) / 1000000  # HAFAS uses scaled coordinates
                lon = crd.get('x', 0) / 1000000
                if lat != 0 and lon != 0:
                    station_info += f"- Coordinates: {lat:.6f}, {lon:.6f}\n"

            results.append(station_info)

        result_text = f"Found {len(results)} station(s) for '{query}' ({current_profile.name}):\n\n"
        result_text += "\n".join(results)
        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error searching stations: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error searching stations: {str(e)}")]


async def get_journeys(arguments: dict) -> list[TextContent]:
    """Get journey connections between two stations."""
    origin = arguments["origin"]
    destination = arguments["destination"]
    date_str = arguments.get("date")
    time_str = arguments.get("time")
    max_journeys = arguments.get("max_journeys", 5)

    logger.info(f"Getting journeys from {origin} to {destination} (profile: {current_profile.name})")

    try:
        # Parse date and time if provided
        dt = None
        if date_str or time_str:
            date_part = date_str if date_str else datetime.now().strftime("%Y-%m-%d")
            time_part = time_str if time_str else datetime.now().strftime("%H:%M")
            dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")

        # Get locations for origin and destination
        origin_locations = hafas_client.locations(origin)
        dest_locations = hafas_client.locations(destination)

        if not origin_locations:
            return [TextContent(type="text", text=f"Origin station not found: {origin}")]
        if not dest_locations:
            return [TextContent(type="text", text=f"Destination station not found: {destination}")]

        origin_id = origin_locations[0].id
        dest_id = dest_locations[0].id

        # Get journeys
        journeys = hafas_client.journeys(
            origin=origin_id,
            destination=dest_id,
            date=dt,
            max_journeys=max_journeys
        )

        if not journeys:
            return [TextContent(
                type="text",
                text=f"No journeys found from {origin_locations[0].name} to {dest_locations[0].name}"
            )]

        # Format results
        results = []
        for i, journey in enumerate(journeys[:max_journeys]):
            journey_info = f"### Journey {i + 1}\n"
            journey_info += f"**Departure:** {journey.departure} from {journey.origin.name}\n"
            journey_info += f"**Arrival:** {journey.arrival} at {journey.destination.name}\n"
            journey_info += f"**Duration:** {journey.duration}\n"
            journey_info += f"**Transfers:** {journey.transfers}\n"

            if journey.legs:
                journey_info += f"\n**Legs:**\n"
                for j, leg in enumerate(journey.legs):
                    journey_info += f"{j + 1}. {leg.name or 'Transfer'}: "
                    journey_info += f"{leg.origin.name} → {leg.destination.name}\n"

            results.append(journey_info)

        result_text = f"Found {len(results)} journey(ies) from **{origin_locations[0].name}** to **{dest_locations[0].name}**:\n\n"
        result_text += f"*(Using {current_profile.name} profile)*\n\n"
        result_text += "\n---\n\n".join(results)
        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error getting journeys: {e}")
        return [TextContent(type="text", text=f"Error getting journeys: {str(e)}")]


async def get_departures(arguments: dict) -> list[TextContent]:
    """Get departures from a station."""
    station = arguments["station"]
    max_departures = arguments.get("max_departures", 10)

    logger.info(f"Getting departures from: {station} (profile: {current_profile.name})")

    try:
        # Get station location
        locations = hafas_client.locations(station)
        if not locations:
            return [TextContent(type="text", text=f"Station not found: {station}")]

        station_id = locations[0].id
        station_name = locations[0].name

        # Get departures
        departures = hafas_client.departures(
            station=station_id,
            date=datetime.now(),
            max_trips=max_departures
        )

        if not departures:
            return [TextContent(type="text", text=f"No departures found for {station_name}")]

        # Format results
        results = []
        results.append(f"# Departures from {station_name}\n")
        results.append(f"*(Using {current_profile.name} profile)*\n")

        for departure in departures[:max_departures]:
            dep_info = f"**{departure.name}** to {departure.direction}\n"
            dep_info += f"- Departure: {departure.departure}\n"

            if hasattr(departure, 'platform') and departure.platform:
                dep_info += f"- Platform: {departure.platform}\n"

            if hasattr(departure, 'delay') and departure.delay:
                dep_info += f"- Delay: {departure.delay} minutes\n"

            results.append(dep_info)

        result_text = "\n".join(results)
        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error getting departures: {e}")
        return [TextContent(type="text", text=f"Error getting departures: {str(e)}")]


async def get_arrivals(arguments: dict) -> list[TextContent]:
    """Get arrivals at a station."""
    station = arguments["station"]
    max_arrivals = arguments.get("max_arrivals", 10)

    logger.info(f"Getting arrivals at: {station} (profile: {current_profile.name})")

    try:
        # Get station location
        locations = hafas_client.locations(station)
        if not locations:
            return [TextContent(type="text", text=f"Station not found: {station}")]

        station_id = locations[0].id
        station_name = locations[0].name

        # Get arrivals
        arrivals = hafas_client.arrivals(
            station=station_id,
            date=datetime.now(),
            max_trips=max_arrivals
        )

        if not arrivals:
            return [TextContent(type="text", text=f"No arrivals found for {station_name}")]

        # Format results
        results = []
        results.append(f"# Arrivals at {station_name}\n")
        results.append(f"*(Using {current_profile.name} profile)*\n")

        for arrival in arrivals[:max_arrivals]:
            arr_info = f"**{arrival.name}**"
            if hasattr(arrival, 'origin') and arrival.origin:
                arr_info += f" from {arrival.origin.name}\n"
            else:
                arr_info += "\n"
            arr_info += f"- Arrival: {arrival.arrival}\n"

            if hasattr(arrival, 'platform') and arrival.platform:
                arr_info += f"- Platform: {arrival.platform}\n"

            if hasattr(arrival, 'delay') and arrival.delay:
                arr_info += f"- Delay: {arrival.delay} minutes\n"

            results.append(arr_info)

        result_text = "\n".join(results)
        return [TextContent(type="text", text=result_text)]

    except Exception as e:
        logger.error(f"Error getting arrivals: {e}")
        return [TextContent(type="text", text=f"Error getting arrivals: {str(e)}")]


# Built after the handlers so the 2.x constructor can bind them.
app = Server(
    "transitmcp",
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
