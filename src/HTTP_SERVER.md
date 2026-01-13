# HTTP Streamable Server Guide

Access the Datadog MCP Server via HTTP with **Server-Sent Events (SSE)** streaming - no bridge tools needed!

## Quick Start

### Option 1: Run HTTP Server Locally

```bash
cd src
pip install -r requirements.txt
export DD_API_KEY=your-key
export DD_APP_KEY=your-key
export SERVER_MODE=http
python http_server.py
```

Visit: http://localhost:8000

### Option 2: Run with Docker Compose (HTTP Mode)

```bash
cd docker
cp .env.example .env
# Edit .env with credentials

# Run HTTP version
docker-compose -f docker-compose.http.yml up -d

# View logs
docker-compose -f docker-compose.http.yml logs -f mcp-datadog-http
```

Visit: http://localhost:8000

### Option 3: Run Docker (Both MCP and HTTP)

```bash
cd docker

# MCP mode (default, uses stdio)
docker-compose up -d

# HTTP mode
docker run -e SERVER_MODE=http -e DD_API_KEY=your-key -e DD_APP_KEY=your-key -p 8000:8000 mcp-datadog
```

## HTTP Endpoints

### 📊 Quick Reference

| Method | Endpoint | Response | Description |
|--------|----------|----------|-------------|
| GET | `/health` | JSON | Health check |
| GET | `/tools` | JSON | List available tools |
| GET | `/query_metrics` | JSON | Query metrics |
| GET | `/query_metrics/stream` | SSE | Query metrics (streaming) |
| GET | `/search_metrics` | JSON | Search metrics |
| GET | `/search_metrics/stream` | SSE | Search metrics (streaming) |
| GET | `/get_metric_tags` | JSON | Get metric tags |
| GET | `/get_metric_tags/stream` | SSE | Get metric tags (streaming) |
| POST | `/call` | JSON | Call any tool |
| POST | `/call/stream` | SSE | Call any tool (streaming) |

### 🚀 Interactive API Docs

```
http://localhost:8000/docs
```

FastAPI automatically generates interactive Swagger UI where you can test all endpoints.

## Usage Examples

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "datadog-mcp-http",
  "version": "1.0.0"
}
```

### 2. List Available Tools

```bash
curl http://localhost:8000/tools
```

### 3. Query Metrics (JSON Response)

```bash
curl "http://localhost:8000/query_metrics?query=avg:system.cpu.user{*}&days_back=7"
```

Response:
```json
{
  "status": "success",
  "tool": "query_metrics",
  "parameters": {
    "query": "avg:system.cpu.user{*}",
    "days_back": 7
  },
  "result": {
    "series": [...]
  }
}
```

### 4. Query Metrics (SSE Streaming)

```bash
curl -N "http://localhost:8000/query_metrics/stream?query=avg:system.cpu.user{*}&days_back=7"
```

Response (Server-Sent Events):
```
data: {"type":"start","query":"avg:system.cpu.user{*}","days_back":7}

data: {"type":"data","result":{"series":[...]}}

data: {"type":"complete","status":"success"}
```

### 5. Search Metrics

```bash
curl "http://localhost:8000/search_metrics?prefix=system"
```

### 6. Get Metric Tags

```bash
curl "http://localhost:8000/get_metric_tags?metric_name=system.cpu.user"
```

### 7. Call Tool via POST (JSON)

```bash
curl -X POST http://localhost:8000/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_metrics",
    "parameters": {
      "query": "avg:system.cpu.user{*}",
      "days_back": 7
    }
  }'
```

### 8. Call Tool via POST (SSE Streaming)

```bash
curl -N -X POST http://localhost:8000/call/stream \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "query_metrics",
    "parameters": {
      "query": "avg:system.cpu.user{*}",
      "days_back": 7
    }
  }'
```

## Server-Sent Events (SSE) Explanation

### What is SSE?

SSE allows servers to push updates to clients over HTTP. Perfect for streaming large results.

### SSE Response Format

```
data: {"type":"start","query":"..."}

data: {"type":"data","result":{...}}

data: {"type":"complete","status":"success"}
```

### Types

- `start` - Request started
- `data` - Actual result
- `complete` - Request finished
- `error` - Error occurred

### JavaScript Client Example

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/query_metrics/stream?query=avg:system.cpu.user{*}'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'start') {
    console.log('Query started:', data);
  } else if (data.type === 'data') {
    console.log('Result:', data.result);
  } else if (data.type === 'complete') {
    console.log('Query complete');
    eventSource.close();
  } else if (data.type === 'error') {
    console.error('Error:', data.error);
    eventSource.close();
  }
};
```

### Python Client Example

```python
import requests
import json

def stream_query():
    url = 'http://localhost:8000/query_metrics/stream'
    params = {'query': 'avg:system.cpu.user{*}', 'days_back': 7}
    
    response = requests.get(url, params=params, stream=True)
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(f"[{data['type']}]", data)

stream_query()
```

### cURL with SSE

Use `-N` flag to disable buffering:

```bash
curl -N "http://localhost:8000/query_metrics/stream?query=avg:system.cpu.user{*}"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_MODE` | `mcp` | `mcp` or `http` |
| `MCP_HTTP_PORT` | `8000` | HTTP server port |
| `DD_API_KEY` | Required | Datadog API key |
| `DD_APP_KEY` | Required | Datadog application key |
| `DD_SITE` | `datadoghq.com` | Datadog site |
| `LOG_LEVEL` | `info` | Logging level |

## Performance

### JSON Response
- ✅ Simpler for small results
- ✅ All data at once
- ❌ Larger payloads
- ❌ Long wait time for large results

### SSE Streaming
- ✅ Stream large results progressively
- ✅ Client can start processing immediately
- ✅ Better for long-running queries
- ❌ More complex client code

## Production Deployment

### Docker with HTTP

```bash
# Build
docker build -f docker/Dockerfile.mcp -t mcp-datadog .

# Run HTTP mode
docker run \
  -e SERVER_MODE=http \
  -e DD_API_KEY=$DD_API_KEY \
  -e DD_APP_KEY=$DD_APP_KEY \
  -p 8000:8000 \
  mcp-datadog
```

### Reverse Proxy (Nginx)

```nginx
upstream mcp_http {
    server localhost:8000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://mcp_http;
        proxy_http_version 1.1;
        proxy_set_header Connection "upgrade";
        proxy_set_header Upgrade $http_upgrade;
        proxy_buffering off;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Load Balancer

For multiple instances, use:

```yaml
# docker-compose.yml with load balancer
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - mcp-1
      - mcp-2

  mcp-1:
    build: .
    environment:
      - SERVER_MODE=http
      - PORT=8001

  mcp-2:
    build: .
    environment:
      - SERVER_MODE=http
      - PORT=8002
```

## Troubleshooting

### "Cannot connect to localhost:8000"

Check if server is running:
```bash
curl http://localhost:8000/health
```

Or view logs:
```bash
docker-compose -f docker-compose.http.yml logs mcp-datadog-http
```

### "401 Unauthorized" from Datadog

Verify credentials:
```bash
echo $DD_API_KEY
echo $DD_APP_KEY
```

Update .env and restart:
```bash
docker-compose -f docker-compose.http.yml restart
```

### "No module named fastapi"

Install dependencies:
```bash
pip install -r src/requirements.txt
```

Or rebuild Docker:
```bash
docker-compose -f docker-compose.http.yml build --no-cache
```

### SSE Not Streaming

Make sure to use `/stream` endpoints and client supports SSE:
```bash
# Correct
curl -N http://localhost:8000/query_metrics/stream?query=avg:system.cpu.user

# Wrong (won't stream)
curl http://localhost:8000/query_metrics
```

## MCP vs HTTP

| Feature | MCP | HTTP |
|---------|-----|------|
| Protocol | stdio (JSON-RPC) | HTTP/REST |
| Streaming | No | SSE (Optional) |
| Claude Native | ✅ | ❌ |
| Web Access | ❌ | ✅ |
| Bridge Tools | ✅ | ❌ |
| Setup | Complex | Simple |
| Load Balancing | Hard | Easy (nginx) |

## Summary

- **Use MCP** when: Using Claude Desktop native
- **Use HTTP** when: Web services, webhooks, external access, simple HTTP clients

Both run in the same Docker container - just set `SERVER_MODE=http` to switch!

See [../MCP_DATADOG_README.md](../MCP_DATADOG_README.md) for MCP-specific documentation.
