#!/usr/bin/env python3
"""Entry point for running the mcp-scotty server."""

import asyncio
from src.mcp_scotty.server import main

if __name__ == "__main__":
    asyncio.run(main())
