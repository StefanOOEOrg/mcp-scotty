# mcp-scotty

[![CI](https://github.com/StefanOOEOrg/mcp-scotty/actions/workflows/ci.yml/badge.svg)](https://github.com/StefanOOEOrg/mcp-scotty/actions/workflows/ci.yml)
[![M8ven Score](https://m8ven.ai/badge/mcp/stefanooeorg-mcp-scotty-vw6uta?v=1be218941eb5916cc75b4f2a5ed68f07)](https://m8ven.ai/mcp/stefanooeorg-mcp-scotty-vw6uta?s=readme)

**Multi-Provider MCP Server for European Public Transit Information**

mcp-scotty is a Model Context Protocol (MCP) server that provides real-time public transit information across Europe via the HAFAS API. Support for multiple transit providers including ÖBB (Austria), Deutsche Bahn (Germany), SBB (Switzerland), NS (Netherlands), and more.

## 🌍 Supported Transit Providers

| Provider | Country | Profile ID | Description |
|----------|---------|------------|-------------|
| **ÖBB** | 🇦🇹 Austria | `oebb` | Austrian Federal Railways |
| **Deutsche Bahn** | 🇩🇪 Germany | `db` | German Federal Railway |
| **SBB** | 🇨🇭 Switzerland | `sbb` | Swiss Federal Railways |
| **NS** | 🇳🇱 Netherlands | `ns` | Nederlandse Spoorwegen |
| **NVV** | 🇩🇪 Germany | `nvv` | Nordhessischer Verkehrsverbund |
| **VSN** | 🇩🇪 Germany | `vsn` | Verkehrsverbund Süd-Niedersachsen |

*Additional HAFAS providers can be added via configuration*

## ✨ Features

- **Multi-provider profiles**: `oebb`, `db`, `sbb`, `ns` — each with its own endpoint and language
- **Station search**: free-text search, returning the HAFAS id a client needs for the next step
- **Journey planning**: connections between two stations with departure/arrival, duration, number of
  changes and every leg (line name, origin, destination, times) — including overnight connections
- **Honest failures**: a failed or unsupported call comes back as an MCP error (`is_error: true`) with a
  readable message, never as an empty list that looks like a result

`get_departures` and `get_arrivals` exist as tools but **do not work yet** — the HAFAS station board is
still unverified, so they answer with an explicit error. See [Known issues](#-known-issues).

## 📋 Requirements

- Python 3.10 or higher (the CI runs 3.10 and 3.14)
- An MCP-compatible client (e.g. Claude Desktop)
- Internet access to the HAFAS endpoint of your provider — no account, no API key, no credentials

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/StefanOOEOrg/mcp-scotty.git
cd mcp-scotty
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Transit Provider

Set your default transit provider via environment variable (optional):

```bash
export TRANSIT_PROFILE=oebb  # Default is 'oebb'
# Options: oebb, db, sbb, ns, nvv, vsn
```

## ⚙️ Configuration

### Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "transit": {
      "command": "/absolute/path/to/mcp-scotty/venv/bin/python",
      "args": [
        "/absolute/path/to/mcp-scotty/run_server.py"
      ],
      "env": {
        "TRANSIT_PROFILE": "oebb"
      }
    }
  }
}
```

**Change the provider**: Modify `TRANSIT_PROFILE` to any supported provider ID.

## 🔧 Available Tools

### 1. `list_transit_profiles`

List all available transit provider profiles.

**Example**:
```
List all available transit providers
```

### 2. `set_transit_profile`

Switch to a different transit provider.

**Parameters**:
- `profile` (string): Profile ID (e.g., 'db', 'sbb', 'ns')

**Example**:
```
Switch to Deutsche Bahn profile
```

### 3. `search_stations`

Search for stations by name.

**Parameters**:
- `query` (string): Station name or partial name
- `max_results` (int, optional): Maximum results (default: 10)

**Example**:
```
Search for "Vienna Central Station"
```

### 4. `get_journeys`

Find connections between two stations.

**Parameters**:
- `origin` (string): Origin station name
- `destination` (string): Destination station name
- `date` (string, optional): Date in YYYY-MM-DD format
- `time` (string, optional): Time in HH:MM format
- `max_journeys` (int, optional): Maximum journeys (default: 5)

**Example**:
```
Find trains from Vienna to Salzburg tomorrow at 14:00
```

### 5. `get_departures` — not implemented yet

Currently answers with `is_error: true` and the message *"The station board is not implemented yet for
ÖBB; use get_journeys or search_stations instead."* The HAFAS `StationBoard` request is still being
researched (see [Planned improvements](#-planned-improvements)).

**Parameters**:
- `station` (string): Station name
- `max_departures` (int, optional): Maximum departures (default: 10)

**Example**:
```
Show departures from Amsterdam Central Station
```

### 6. `get_arrivals` — not implemented yet

Same as `get_departures`: it fails with a readable error instead of returning an empty list.

**Parameters**:
- `station` (string): Station name
- `max_arrivals` (int, optional): Maximum arrivals (default: 10)

**Example**:
```
Show arrivals at Zurich HB
```

## 💡 Usage Examples

Once configured with Claude Desktop, you can ask:

### Austria (ÖBB)
- "What trains go from Vienna to Salzburg this afternoon?"
- "Show me departures from Innsbruck Hauptbahnhof"
- "Find connections from Graz to Linz tomorrow morning"

### Germany (Deutsche Bahn)
- "Trains from Berlin to Munich?"
- "Switch to Deutsche Bahn and find connections to Hamburg"
- "Departures from Frankfurt Hauptbahnhof"

### Switzerland (SBB)
- "Set profile to SBB and search for Zurich stations"
- "Trains from Geneva to Bern"
- "What time does the next train to Lucerne leave?"

### Netherlands (NS)
- "Use NS profile and find Amsterdam stations"
- "Trains from Rotterdam to Utrecht"
- "Show departures from Den Haag Centraal"

## 📁 Project Structure

```
mcp-scotty/
├── src/mcp_scotty/
│   ├── __init__.py        # version
│   ├── hafas_client.py    # LocMatch + TripSearch, normalised into dicts
│   ├── profiles.py        # the four provider profiles
│   └── server.py          # MCP server: tools, dispatcher, error handling
├── tests/
│   ├── fixtures/          # recorded ÖBB responses (no network in CI)
│   ├── test_hafas_client.py
│   ├── test_profiles.py
│   └── test_server.py
├── examples/usage_examples.md
├── .github/workflows/ci.yml  # ruff + pytest on 3.10 and 3.14
├── run_server.py          # entry point
├── pyproject.toml         # metadata, dependencies, ruff + pytest config
├── setup.py               # console script
├── requirements.txt
├── CHANGELOG.md
├── INSTALL.md
├── CONTRIBUTING.md
└── README.md
```

## 🔒 Technical Details

- **MCP SDK**: Official Python MCP SDK (≥1.2.0)
- **HAFAS client**: direct HTTP against the provider's `mgate.exe`, no third-party HAFAS library
- **Protocol**: stdio-based communication (MCP standard)
- **Architecture**: Multi-profile support with runtime switching
- **Error Handling**: Comprehensive SSL and network error handling
- **Transport**: Direct HTTP requests to HAFAS mgate.exe endpoints

## ⚠️ Known Issues

- **The station board is not implemented.** HAFAS `StationBoard` returns no entries with the request
  bodies tried so far, so `get_departures` and `get_arrivals` answer with an explicit error. Everything
  else works against the live ÖBB API and is covered by tests over recorded responses.
- **Station search is fuzzy.** `LocMatch` answers even for nonsense queries — "Xyzzy-123" still returns a
  handful of unrelated stations. The "no stations found" error therefore only fires on genuinely empty
  answers; check the returned names before using an id.
- **No delay or platform information.** The normalised journey data carries times, durations, changes and
  legs — not real-time delays or platform changes.
- **SSL verification can be disabled** with `TRANSIT_DISABLE_SSL_VERIFY=true` for local testing. That is
  insecure and must never be used in production; the code logs a warning when it happens.

## 🚧 Limitations

- Four providers only (`oebb`, `db`, `sbb`, `ns`); more need their own endpoint configuration.
- No tickets, prices or seat reservations — this server only reads timetable data.
- No caching: every call goes to the provider, so rate limits and outages are visible immediately.
- Departures and arrivals are missing until the station board is understood (Stage 2).
- The HAFAS protocol is undocumented; a provider can change its endpoint without notice.

## 🔮 Planned Improvements

- [ ] **Stage 2:** research `StationBoard` and implement `get_departures` / `get_arrivals`
- [ ] More providers (SNCF, NMBS, DSB) with their own configurations
- [ ] Optional caching for repeated station lookups
- [ ] Surface real-time delay and platform data where the provider offers it
- [ ] Retry logic with exponential backoff
- [ ] Support for more European transit providers
- [ ] Fare and pricing information
- [ ] Service disruption alerts

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas for contribution:
- Additional transit provider profiles
- Improved error handling
- Documentation and examples
- Tests
- Bug fixes

## 📄 License

This project is licensed under the **GNU General Public License v3.0** — see the [LICENSE](LICENSE)
file for the full text.

## 🙏 Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Talks to HAFAS directly (`LocMatch`, `TripSearch`); the day-offset rule for times follows the
  convention documented by [pyhafas](https://github.com/FahrplanDatenGarten/pyhafas)
- HAFAS is a product of [HaCon](https://www.hacon.de/) (Siemens Mobility)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/StefanOOEOrg/mcp-scotty/issues)
- **MCP Documentation**: https://modelcontextprotocol.io/
- **pyhafas** (reference for the HAFAS time format): https://pyhafas.readthedocs.io/

---

**Note**: This is an unofficial, community-maintained project. For official transit information, please use the respective provider's official website or mobile app.
