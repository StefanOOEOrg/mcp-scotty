# mcp-scotty

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

- **Multi-Provider Support**: Switch between different transit providers on the fly
- **Station Search**: Find stations by name across Europe
- **Journey Planning**: Get connections with transfers, times, and durations
- **Real-Time Departures**: Check upcoming departures from any station
- **Real-Time Arrivals**: Monitor arriving trains/buses at stations
- **Delay Information**: Get real-time delay and platform change notifications

## 📋 Requirements

- Python 3.10 or higher
- MCP-compatible client (e.g., Claude Desktop)

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

### 5. `get_departures`

Get upcoming departures from a station.

**Parameters**:
- `station` (string): Station name
- `max_departures` (int, optional): Maximum departures (default: 10)

**Example**:
```
Show departures from Amsterdam Central Station
```

### 6. `get_arrivals`

Get upcoming arrivals at a station.

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
├── src/
│   └── mcp_scotty/
│       ├── __init__.py       # Package initialization
│       ├── profiles.py       # Transit provider profiles
│       └── server.py         # Main MCP server
├── examples/
│   └── usage_examples.md     # Detailed usage examples
├── tests/
│   ├── __init__.py
│   └── test_server.py       # Tests
├── run_server.py            # Entry point
├── requirements.txt         # Dependencies
├── pyproject.toml          # Project metadata
├── setup.py                # Setup configuration
├── README.md               # This file
├── INSTALL.md              # Installation guide
├── CONTRIBUTING.md         # Contributing guidelines
└── CHANGELOG.md            # Version history
```

## 🔒 Technical Details

- **MCP SDK**: Official Python MCP SDK (≥1.2.0)
- **HAFAS Client**: Custom direct implementation (removed pyhafas dependency)
- **Protocol**: stdio-based communication (MCP standard)
- **Architecture**: Multi-profile support with runtime switching
- **Error Handling**: Comprehensive SSL and network error handling
- **Transport**: Direct HTTP requests to HAFAS mgate.exe endpoints

## ⚠️ Known Issues

### HAFAS API Compatibility

**Current Status**: mcp-scotty now uses a custom direct HAFAS API implementation (v0.3.0+):

✅ **Improvements:**
- Removed pyhafas dependency for better control
- Direct HTTP requests to HAFAS mgate.exe endpoints
- Provider-specific configurations (ÖBB, DB, SBB, NS)
- SSL verification bypass option for testing

⚠️ **Work in Progress:**
- HAFAS request format requires fine-tuning
- Some endpoints return PARSE errors
- Request body structure needs adjustment per provider

**Impact**: Core functionality is implemented but requires further HAFAS protocol refinement.

**Workarounds**:

When mcp-scotty encounters these issues, it provides helpful error messages directing users to:
- Official transit provider websites (e.g., oebb.at, bahn.de, sbb.ch, ns.nl)
- Mobile apps available for each provider
- Customer service contacts

**For Testing** (SSL verification bypass):

```json
{
  "mcpServers": {
    "transit": {
      ...
      "env": {
        "TRANSIT_PROFILE": "oebb",
        "TRANSIT_DISABLE_SSL_VERIFY": "true"
      }
    }
  }
}
```

⚠️ **Warning**: Disabling SSL verification is insecure and should only be used for local testing.

**Alternative Solutions**:

```bash
# Update to latest versions
pip install --upgrade certifi pyhafas

# Check for pyhafas updates
pip list --outdated | grep pyhafas
```

## 🚧 Limitations

- Some providers use DB profile as fallback (pending dedicated profiles)
- Real-time data depends on HAFAS API availability
- Features may vary between providers

## 🔮 Planned Improvements

- [ ] Dedicated HAFAS profiles for each provider
- [ ] Direct HAFAS API implementation as fallback
- [ ] Enhanced SSL certificate handling
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

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [pyhafas](https://github.com/FahrplanDatenGarten/pyhafas) for HAFAS API access
- HAFAS is a product of [HaCon](https://www.hacon.de/) (Siemens Mobility)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/StefanOOEOrg/mcp-scotty/issues)
- **MCP Documentation**: https://modelcontextprotocol.io/
- **pyhafas Documentation**: https://pyhafas.readthedocs.io/

---

**Note**: This is an unofficial, community-maintained project. For official transit information, please use the respective provider's official website or mobile app.
