# Changelog

All notable changes to mcp-scotty will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Station board (`get_departures`, `get_arrivals`) — Stage 2
- Trip tracking functionality
- Fare and pricing information
- Station facilities and amenities information
- Real-time platform change notifications
- Service disruption alerts
- Support for more European transit providers (SNCF, NMBS, DSB, etc.)

## [0.4.0] - 2026-10-24

The release that made the server work. Until here it started only with the old
`mcp` 1.x and returned empty results without saying so.

### Fixed
- **It runs with the current SDK again.** The handlers were registered with the
  mcp 1.x decorators, while `pyproject.toml` allowed any version, so a fresh
  install pulled 2.x and died on import (`'Server' object has no attribute
  'list_tools'`). Ported to the 2.x handlers (`on_list_tools`, `on_call_tool`),
  pinned `mcp>=2.2,<3`, and declared `requests`, which was imported but never
  listed as a dependency.
- **Station search works.** The `LocMatch` body was ignored by the API, so every
  search came back empty. It now sends the documented body and normalises the
  matches (`id`, `name`, `ext_id`, `type`).
- **Journey planning works.** Same for `TripSearch`: real connections with
  departure/arrival, duration, number of changes and every leg (line name,
  origin, destination, times), including connections that cross midnight — HAFAS
  prefixes those times with a day offset (`01020700` = 02:07 the next day).
- **Failures look like failures.** Tool errors travel through `ToolFailure` and
  reach the client as `is_error: true`; an empty result is an error, not a
  successful empty answer.
- **`get_departures` / `get_arrivals` fail honestly** with "The station board is
  not implemented yet …" instead of returning an empty list. The HAFAS
  `StationBoard` request is still unverified (Stage 2).
- Removed the unused `pyhafas` dependency (it has no ÖBB profile), and the
  `Apache-2.0` metadata that contradicted the GPL-3.0 `LICENSE`.

### Added
- **Tests:** 32 of them — the client against recorded ÖBB responses (no network
  in CI), the tool layer through an in-process MCP client, and the provider
  profiles including a guard that every profile has a HAFAS configuration.
- **CI:** ruff and pytest on Python 3.10 and 3.14.
- **Rename:** the package is `mcp_scotty` and the project `mcp-scotty`
  (formerly `transitmcp` / `TransitMCP`); the server announces itself as
  `scotty`.

## [0.3.0] - 2025-11-10

### Breaking Changes
- **Removed pyhafas dependency** - Now using custom direct HAFAS API implementation
- Reduced supported providers from 6 to 4 (removed NVV, VSN - will be re-added)

### Added
- Custom HAFAS API client (`hafas_client.py`)
- Direct HTTP communication with HAFAS mgate.exe endpoints
- Provider-specific HAFAS configurations (endpoint URLs, authentication)
- HAFAS_CONFIGS dictionary with ÖBB, DB, SBB, NS configurations
- Proper HAFAS request structure (auth, client, svcReqL)

### Changed
- `requirements.txt`: Replaced `pyhafas>=0.4.0` with `requests>=2.31.0`
- Profile structure: Changed from `hafas_profile` to `hafas_profile_id`
- Client initialization: Now uses `HafasClient` from `hafas_client.py`
- Station search: Updated to handle HAFAS JSON response format

### Technical Improvements
- Better control over HAFAS API requests
- Configurable SSL verification per provider
- Detailed logging of HAFAS requests
- JSON response parsing with error handling

### Known Issues
- HAFAS request format needs fine-tuning (currently returns PARSE errors)
- Station search not yet working due to protocol refinement needed
- Need to validate request body structure per provider

### Work in Progress
- Debugging HAFAS mgate.exe request format
- Testing with different HAFAS endpoints
- Request parameter validation

## [0.2.0] - 2025-11-10

### Major Changes
- **Project renamed** from mcp-scotty to mcp-scotty for broader international appeal
- **Multi-provider support**: Can now switch between different transit providers
- **Package renamed** from `scottymcp` to `mcp_scotty`

### Added
- Multi-profile architecture supporting different HAFAS providers
- Six transit provider profiles: ÖBB (Austria), DB (Germany), SBB (Switzerland), NS (Netherlands), NVV, VSN
- New tool: `list_transit_profiles` - List all available providers
- New tool: `set_transit_profile` - Switch between providers at runtime
- Environment variable `TRANSIT_PROFILE` for default provider selection
- Profile-specific error messages with appropriate website links
- Comprehensive English documentation for international users
- Transit provider comparison table in README

### Changed
- All documentation translated to English
- Error messages now adapt to selected provider
- Server name from "scottymcp" to "mcp_scotty"
- Claude Desktop config updated to use "transit" identifier
- README completely rewritten for multi-provider context

### Technical
- New `profiles.py` module for provider configuration management
- Profile dataclass with country, language, timezone information
- Dynamic profile switching without server restart
- Improved logging with profile context

## [0.1.0] - 2025-11-10

### Added
- Initial release of mcp-scotty
- MCP server implementation using official Python SDK
- Integration with pyhafas for HAFAS API access
- Four main tools:
  - `search_stations`: Search for train stations by name
  - `get_journeys`: Find connections between stations
  - `get_departures`: Get upcoming departures from a station
  - `get_arrivals`: Get upcoming arrivals at a station
- Comprehensive documentation:
  - README with overview and usage examples
  - INSTALL guide with step-by-step instructions
  - CONTRIBUTING guidelines for developers
- Project structure with proper packaging
- Example configuration for Claude Desktop
- Apache 2.0 license
- Python 3.10+ support

### Technical Details
- Uses MCP SDK 1.2.0+
- Uses pyhafas 0.4.0+
- Stdio-based communication protocol
- Async/await support throughout

[Unreleased]: https://github.com/yourusername/mcp-scotty/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/mcp-scotty/releases/tag/v0.1.0
