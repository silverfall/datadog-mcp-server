# Datadog MCP Server

A Model Context Protocol (MCP) server that connects Claude AI to Datadog, enabling natural language queries for metrics, searches, and tag information.

## Project Structure

```
datadog-mcp-server/
├── src/                    # MCP Server source code
│   ├── mcp_datadog_server.py
│   ├── start_mcp_server.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md          # Source documentation
│
├── test/                   # Test scripts and examples
│   ├── test_mcp_tools.py
│   ├── example_queries.py
│   └── README.md          # Testing guide
│
├── docker/                 # Docker deployment
│   ├── Dockerfile.mcp
│   ├── docker-compose.yml
│   ├── .dockerignore
│   ├── .env.example
│   ├── quickstart.sh
│   └── README.md          # Docker deployment guide
│
└── MCP_DATADOG_README.md  # This file - Project overview
```

## Features

- **Query Metrics**: Retrieve Datadog metrics with time-series data
- **Search Metrics**: Find available metrics by prefix
- **Get Metric Tags**: Access tag metadata for specific metrics
- **Docker Support**: Containerized deployment with docker-compose
- **External Access**: Multiple methods for remote Claude connections

## Quick Start

### Option 1: Docker (Recommended)

```bash
# Configure credentials
cd docker
cp .env.example .env
# Edit .env with your Datadog API keys

# Start server
docker-compose up -d

# View logs
docker-compose logs -f mcp-datadog
```

See [docker/README.md](docker/README.md) for details.

### Option 2: Local Python

```bash
# Install dependencies
cd src
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your Datadog API keys

# Start server
python -m start_mcp_server
```

See [src/README.md](src/README.md) for details.

## Configuration

### Datadog Credentials

Required environment variables:

```bash
DD_API_KEY=your-datadog-api-key
DD_APP_KEY=your-datadog-application-key
DD_SITE=datadoghq.com  # Optional
```

Get your credentials from [Datadog API Keys](https://app.datadoghq.com/organization-settings/api-keys).

### Claude Desktop Setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "datadog": {
      "command": "python",
      "args": ["-m", "start_mcp_server"],
      "cwd": "/path/to/datadog-mcp-server/src",
      "env": {
        "DD_API_KEY": "your-api-key",
        "DD_APP_KEY": "your-app-key",
        "DD_SITE": "datadoghq.com"
      }
    }
  }
}
```

## Available Tools

### 1. `query_metrics`
Query timeseries metrics from Datadog.

**Parameters:**
- `query` (string, required): Datadog metric query
  - Examples:
    - `avg:system.cpu{*}`
    - `sum:aws.applicationelb.httpcode_target_5xx{account_name:prod}`
    - `sum:aws.applicationelb.request_count{account_name:prod} by {loadbalancer}`
- `days_back` (integer, optional): Number of days to look back (default: 7)

**Example Usage:**
```
query_metrics with query="sum:aws.applicationelb.httpcode_target_5xx{account_name:mytelkomsel-prod} by {loadbalancer}" days_back=7
```

**Response:**
```json
{
  "status": "success",
  "query": "sum:aws.applicationelb.httpcode_target_5xx{account_name:mytelkomsel-prod}...",
  "from": 1673001600,
  "to": 1673606400,
  "series_count": 3,
  "series": [
    {
      "scope": "loadbalancer:alb-prod-1",
      "points": [
        [1673001600, 45.2],
        [1673005200, 42.1],
        ...
      ]
    },
    ...
  ]
}
```

### 2. `search_metrics`
Search for available metrics by prefix.

**Parameters:**
- `prefix` (string, required): Metric prefix to search
  - Examples:
    - `aws.applicationelb`
    - `system.cpu`
    - `aws.rds`

**Example Usage:**
```
search_metrics with prefix="aws.applicationelb"
```

**Response:**
```json
{
  "status": "success",
  "prefix": "aws.applicationelb",
  "count": 15,
  "metrics": [
    "aws.applicationelb.active_connection_count",
    "aws.applicationelb.client_tls_negotiation_time_average",
    "aws.applicationelb.httpcode_target_2xx",
    "aws.applicationelb.httpcode_target_5xx",
    "aws.applicationelb.request_count",
    ...
  ]
}
```

### 3. `get_metric_tags`
Get tag information for a metric.

**Parameters:**
- `metric_name` (string, required): Name of the metric

**Example Usage:**
```
get_metric_tags with metric_name="aws.applicationelb.request_count"
```

## Available Tools

### 1. `query_metrics`
Query timeseries metrics from Datadog.

**Parameters:**
- `query` (string, required): Datadog metric query (e.g., `avg:system.cpu.user{*}`)
- `days_back` (integer, optional): Number of days to look back (default: 7)

**Examples:**
```
"Query system CPU for the last 7 days"
"Show me ALB errors: sum:aws.applicationelb.httpcode_target_5xx{*} by {loadbalancer}"
```

### 2. `search_metrics`
Search for available metrics by prefix.

**Parameters:**
- `prefix` (string, required): Metric prefix to search

**Examples:**
```
"Search for AWS metrics"
"Find all docker metrics"
```

### 3. `get_metric_tags`
Get tag information for a specific metric.

**Parameters:**
- `metric_name` (string, required): Full metric name

**Examples:**
```
"Get tags for system.cpu.user metric"
"What tags are available for aws.ec2.cpuutilization?"
```

See [test/README.md](test/README.md) for more examples.

## Testing

Run test suite:

```bash
cd test
python test_mcp_tools.py
```

View example queries:

```bash
cd test
python example_queries.py
```

See [test/README.md](test/README.md) for details.

## Deployment

### Local Development

```bash
cd src
pip install -r requirements.txt
python -m start_mcp_server
```

### Docker Production

```bash
cd docker
cp .env.example .env
# Edit .env
docker-compose up -d
```

### External Access

For connecting Claude from external machines:
- **SSH tunnel**: `ssh -L 3000:localhost:3000 user@server`
- **Direct network**: Configure firewall and expose port 3000
- **socat bridge**: Forward TCP connections to Docker container

See [docker/README.md](docker/README.md) for detailed setup.

## Documentation

- **[src/README.md](src/README.md)** - Source code and API documentation
- **[test/README.md](test/README.md)** - Testing guide and examples
- **[docker/README.md](docker/README.md)** - Docker deployment and external access

## Troubleshooting

### Missing credentials

**Error:** `DD_API_KEY and DD_APP_KEY required`

**Solution:**
```bash
# Create .env file
cp src/.env.example src/.env
# Edit with your credentials
```

### Import errors

**Error:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:**
```bash
cd src
pip install -r requirements.txt
```

### API authentication failed

**Error:** `403 Forbidden` or `401 Unauthorized`

**Solution:**
- Verify API keys at [Datadog API Keys](https://app.datadoghq.com/organization-settings/api-keys)
- Check API key permissions
- Ensure DD_SITE matches your Datadog region

### No metrics returned

**Possible causes:**
- Metric name incorrect → Use `search_metrics` to find available metrics
- No data in time range → Check Datadog UI for data availability
- Wrong account/environment tags → Verify tag names

## Requirements

- **Python**: 3.10 or higher
- **Datadog Account**: With API and Application keys
- **Dependencies**: See `src/requirements.txt`
  - mcp >= 0.5.0
  - datadog >= 0.47.0
  - python-dotenv >= 1.0.0
  - httpx >= 0.24.0

## Architecture

```
Claude Desktop/API
    ↓ (MCP Protocol)
start_mcp_server.py
    ↓ (loads .env)
mcp_datadog_server.py
    ├── FastMCP Server
    └── DatadogMetricsClient
        ↓ (Datadog SDK)
Datadog API
```

**Flow:**
1. Claude sends MCP tool request
2. FastMCP server receives and routes to tool handler
3. DatadogMetricsClient calls Datadog API
4. Response formatted as JSON
5. Returned to Claude via MCP protocol

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-tool`
3. Make changes and test: `cd test && python test_mcp_tools.py`
4. Commit: `git commit -am 'Add new tool'`
5. Push: `git push origin feature/new-tool`
6. Create Pull Request

## Support

- **Issues**: [GitHub Issues](https://github.com/silverfall/datadog-mcp-server/issues)
- **Datadog API**: [Datadog API Documentation](https://docs.datadoghq.com/api/)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)

## Changelog

### v1.0.0 (2026-01-13)
- Initial release
- Three core tools: query_metrics, search_metrics, get_metric_tags
- Docker support with docker-compose
- External access configuration options
- Comprehensive documentation
4. Returns results in a Claude-friendly format
