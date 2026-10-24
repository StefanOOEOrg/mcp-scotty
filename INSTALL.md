# Installation Guide for mcp-scotty

This guide provides detailed instructions for installing and configuring mcp-scotty.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Claude Desktop or another MCP-compatible client

## Step-by-Step Installation

### 1. Check Python Version

First, verify that you have Python 3.10 or higher installed:

```bash
python --version
# or
python3 --version
```

If you need to install or upgrade Python, visit [python.org](https://www.python.org/downloads/).

### 2. Clone or Download the Repository

```bash
git clone https://github.com/yourusername/mcp-scotty.git
cd mcp-scotty
```

Or download and extract the ZIP file from GitHub.

### 3. Create a Virtual Environment (Recommended)

Creating a virtual environment helps keep dependencies isolated:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 4. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Or install the package in development mode:

```bash
pip install -e .
```

### 5. Verify Installation

Test that the server can start:

```bash
python run_server.py
```

The server should start without errors. Press `Ctrl+C` to stop it.

## Configuration for Claude Desktop

### macOS

1. Locate your Claude Desktop configuration file:
   ```
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. If the file doesn't exist, create it:
   ```bash
   mkdir -p ~/Library/Application\ Support/Claude/
   touch ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. Edit the configuration file and add mcp-scotty:
   ```json
   {
     "mcpServers": {
       "scottymcp": {
         "command": "python",
         "args": [
           "/full/path/to/mcp-scotty/run_server.py"
         ]
       }
     }
   }
   ```

4. Replace `/full/path/to/mcp-scotty/` with the actual absolute path. You can find it by running:
   ```bash
   pwd
   ```
   in the mcp-scotty directory.

5. If you're using a virtual environment, use the full path to the Python interpreter in the venv:
   ```json
   {
     "mcpServers": {
       "scottymcp": {
         "command": "/full/path/to/mcp-scotty/venv/bin/python",
         "args": [
           "/full/path/to/mcp-scotty/run_server.py"
         ]
       }
     }
   }
   ```

### Windows

1. Locate your Claude Desktop configuration file:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. If the file doesn't exist, create it:
   ```powershell
   New-Item -Path "$env:APPDATA\Claude\claude_desktop_config.json" -ItemType File -Force
   ```

3. Edit the configuration file and add mcp-scotty:
   ```json
   {
     "mcpServers": {
       "scottymcp": {
         "command": "python",
         "args": [
           "C:\\full\\path\\to\\mcp-scotty\\run_server.py"
         ]
       }
     }
   }
   ```

4. If you're using a virtual environment:
   ```json
   {
     "mcpServers": {
       "scottymcp": {
         "command": "C:\\full\\path\\to\\mcp-scotty\\venv\\Scripts\\python.exe",
         "args": [
           "C:\\full\\path\\to\\mcp-scotty\\run_server.py"
         ]
       }
     }
   }
   ```

### Linux

1. Locate your Claude Desktop configuration file:
   ```
   ~/.config/Claude/claude_desktop_config.json
   ```

2. If the file doesn't exist, create it:
   ```bash
   mkdir -p ~/.config/Claude/
   touch ~/.config/Claude/claude_desktop_config.json
   ```

3. Edit the configuration file and add mcp-scotty:
   ```json
   {
     "mcpServers": {
       "scottymcp": {
         "command": "python3",
         "args": [
           "/full/path/to/mcp-scotty/run_server.py"
         ]
       }
     }
   }
   ```

4. If you're using a virtual environment:
   ```json
   {
     "mcpServers": {
       "scottymcp": {
         "command": "/full/path/to/mcp-scotty/venv/bin/python",
         "args": [
           "/full/path/to/mcp-scotty/run_server.py"
         ]
       }
     }
   }
   ```

## Restart Claude Desktop

After configuring the MCP server, restart Claude Desktop completely:

1. Quit Claude Desktop
2. Start Claude Desktop again
3. The mcp-scotty tools should now be available

## Verify Installation

In Claude Desktop, try asking:
- "Search for train stations named Wien"
- "What are the available tools from mcp-scotty?"

If configured correctly, Claude should be able to use the mcp-scotty tools.

## Troubleshooting

### Server doesn't start

1. Check Python version: `python --version`
2. Verify dependencies are installed: `pip list | grep mcp`
3. Check for error messages in Claude Desktop logs

### Claude can't find the server

1. Verify the path in `claude_desktop_config.json` is absolute (not relative)
2. Check that `run_server.py` exists at the specified path
3. Ensure proper JSON syntax (no trailing commas, proper quotes)
4. Restart Claude Desktop after making changes

### Import errors

If you see import errors:
```bash
pip install --upgrade -r requirements.txt
```

### Virtual environment issues

If using a virtual environment, ensure it's activated:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

Then reinstall dependencies:
```bash
pip install -r requirements.txt
```

## Alternative: Using uvx (Universal Virtualenv eXecutor)

If you have `uvx` installed, you can run mcp-scotty without manually creating a virtual environment:

```json
{
  "mcpServers": {
    "scottymcp": {
      "command": "uvx",
      "args": [
        "--from",
        "/full/path/to/mcp-scotty",
        "scottymcp"
      ]
    }
  }
}
```

## Getting Help

If you encounter issues:

1. Check the [main README](README.md) for general information
2. Review the [MCP documentation](https://modelcontextprotocol.io/)
3. Open an issue on the GitHub repository with:
   - Your operating system
   - Python version
   - Error messages
   - Configuration file contents
