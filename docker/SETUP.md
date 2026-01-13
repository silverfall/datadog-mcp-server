# Docker Setup Guide

## Quick Start

### 1. Setup Environment File

```bash
cd docker
cp .env.example .env
```

### 2. Edit .env with Your Credentials

```bash
# Get your API keys from: https://app.datadoghq.com/organization-settings/api-keys
nano .env
```

Required fields:
```bash
DD_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
DD_APP_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Build and Run

From the `docker/` directory:

```bash
# Build the image
docker-compose build

# Start the server
docker-compose up -d

# View logs
docker-compose logs -f mcp-datadog

# Stop the server
docker-compose down
```

## Troubleshooting

### "No module named src.start_mcp_server"

This error has been fixed in the latest Dockerfile. Make sure you have the latest version:

```dockerfile
# Should have:
ENV PYTHONPATH=/app:$PYTHONPATH
CMD ["python", "/app/src/start_mcp_server.py"]
```

**If you still get this error:**

```bash
# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```

### "DD_API_KEY variable is not set"

Make sure `.env` file exists in the `docker/` directory:

```bash
cd docker
cp .env.example .env
# Edit with your credentials
nano .env
```

Then run:

```bash
docker-compose up -d
```

### "Version is obsolete"

The `version: '3.8'` line has been removed from docker-compose.yml. Update to the latest file.

## What is MCP Protocol?

**MCP (Model Context Protocol)** uses **stdio (standard input/output)** for communication, not HTTP or SSE.

### How it works:

```
Claude Desktop / Client
    ↓ (stdin)
MCP Server (mcp-datadog-server)
    ↓ (stdout)
Claude Desktop / Client
```

- **Protocol**: JSON-RPC over stdio
- **Communication**: Bidirectional text stream
- **Connection**: No HTTP ports needed for MCP itself

### Port 8002 (in docker-compose)?

This port is **not used by MCP**. It's a placeholder for future features or custom proxies. MCP communicates purely through stdin/stdout.

### For External Access:

If you need Claude to access the MCP server from another machine, you need a bridge:

**Option 1: SSH Tunnel (Recommended)**
```bash
# On client machine
ssh -L localhost:3000:localhost:3000 user@server

# Then configure Claude to use: localhost:3000
```

**Option 2: Docker Network**
```yaml
# docker-compose.yml can expose port for TCP proxy
ports:
  - "3000:3000"

# Then use socat or netcat bridge
```

**MCP doesn't use HTTP/SSE directly** - the bridge tool handles the stdio-to-network translation.

## Docker Architecture

```
Container (mcp-datadog-server)
├── Python 3.14-slim
├── src/
│   ├── mcp_datadog_server.py (MCP server)
│   ├── start_mcp_server.py (launcher)
│   └── requirements.txt
├── PYTHONPATH=/app (for imports)
└── Runs: python /app/src/start_mcp_server.py
```

## Verify Setup

```bash
# Check container is running
docker-compose ps

# View logs (should show MCP server starting)
docker-compose logs mcp-datadog

# Expected log output:
# mcp-datadog-server  | MCP Server starting on stdio...
```

## Next Steps

1. ✅ Setup `.env` with credentials
2. ✅ Run `docker-compose up -d`
3. ✅ Configure Claude to use the MCP server
4. ✅ Ask Claude questions using Datadog tools

See [../MCP_DATADOG_README.md](../MCP_DATADOG_README.md) for Claude configuration.
