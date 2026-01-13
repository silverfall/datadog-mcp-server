#!/usr/bin/env python3
"""
MCP Datadog Server Launcher with .env support

Loads credentials from .env and starts the MCP server
"""

import os
from dotenv import load_dotenv

# Load .env before any other imports
# Try multiple paths for compatibility
for env_path in ['.env', '/app/.env', os.path.expanduser('~/.env')]:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

# Now run the server
from .mcp_datadog_server import main

if __name__ == "__main__":
    main()
