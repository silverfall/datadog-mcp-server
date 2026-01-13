# Test Directory

This directory contains test scripts and examples for the Datadog MCP Server.

## Files

### test_mcp_tools.py

Test script for validating MCP server tools programmatically.

**Usage:**
```bash
cd test
python test_mcp_tools.py
```

**Requirements:**
- `.env` file in project root with `DD_API_KEY` and `DD_APP_KEY`
- Python packages installed: `pip install -r ../src/requirements.txt`

**What it tests:**
- ✅ `query_metrics()` - Query Datadog metrics with time range
- ✅ `search_metrics()` - Search for available metrics by prefix
- ✅ `get_metric_tags()` - Retrieve tags for specific metrics

**Example output:**
```
============================================================
MCP Datadog Server - Tool Tests
============================================================

✅ Credentials found

=== Testing query_metrics ===
Query: avg:system.cpu.user{*}
Days back: 1

Result: {"series": [{"metric": "system.cpu.user", "points": [...]}]}
✅ query_metrics test passed

=== Testing search_metrics ===
Prefix: system

Result: {"metrics": ["system.cpu.user", "system.cpu.system", ...]}
✅ search_metrics test passed

=== Testing get_metric_tags ===
Metric name: system.cpu.user

Result: {"tags": {"host": ["host1", "host2"], ...}}
✅ get_metric_tags test passed

============================================================
All tests completed
============================================================
```

### example_queries.py

Collection of example Datadog queries for reference.

**Usage:**
```bash
cd test
python example_queries.py
```

**Contents:**
- System metrics (CPU, memory, disk)
- AWS metrics (EC2, RDS)
- Application metrics (traces, requests)
- Database metrics (PostgreSQL, MySQL)
- Container metrics (Docker, Kubernetes)

**Example queries included:**
```python
# Query system CPU
"avg:system.cpu.user{*}"

# Query AWS EC2 by host
"avg:aws.ec2.cpuutilization{*} by {host}"

# Query application requests with tags
"sum:trace.http.request.hits{service:my-service,env:production}"
```

## Running Tests

### Prerequisites

1. **Environment setup:**
   ```bash
   # From project root
   pip install -r src/requirements.txt
   ```

2. **Credentials:**
   Create `.env` file in project root:
   ```bash
   DD_API_KEY=your-datadog-api-key
   DD_APP_KEY=your-datadog-app-key
   DD_SITE=datadoghq.com
   ```

### Run all tests

```bash
cd test
python test_mcp_tools.py
```

### Run examples

```bash
cd test
python example_queries.py
```

## Testing with MCP Protocol

To test with actual MCP protocol (via Claude or MCP client):

1. **Start the MCP server:**
   ```bash
   cd src
   python -m start_mcp_server
   ```

2. **Configure Claude Desktop:**
   Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "datadog": {
         "command": "python",
         "args": ["-m", "start_mcp_server"],
         "cwd": "/path/to/project/src",
         "env": {
           "DD_API_KEY": "your-api-key",
           "DD_APP_KEY": "your-app-key"
         }
       }
     }
   }
   ```

3. **Test in Claude:**
   - "Query system.cpu.user metrics for the last 7 days"
   - "Search for metrics starting with 'aws'"
   - "Get tags for system.mem.used metric"

## Common Issues

### Missing credentials

**Error:**
```
❌ Error: DD_API_KEY and DD_APP_KEY must be set in .env file
```

**Solution:**
```bash
# Create .env in project root
echo "DD_API_KEY=your-key" >> ../.env
echo "DD_APP_KEY=your-key" >> ../.env
```

### Import errors

**Error:**
```
ModuleNotFoundError: No module named 'mcp'
```

**Solution:**
```bash
pip install -r ../src/requirements.txt
```

### API errors

**Error:**
```
❌ query_metrics test failed: 403 Forbidden
```

**Solution:**
- Verify API keys are valid
- Check API key permissions in Datadog
- Ensure DD_SITE is correct (default: datadoghq.com)

## Writing Custom Tests

Example custom test:

```python
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from mcp_datadog_server import DatadogMetricsClient

# Load credentials
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Create client
client = DatadogMetricsClient()

# Query metrics
result = client.query_metrics("avg:system.cpu.user{*}", days_back=1)
print(result)
```

## Next Steps

- See `../src/README.md` for MCP server documentation
- See `../docker/README.md` for Docker deployment
- See root `README.md` for project overview
