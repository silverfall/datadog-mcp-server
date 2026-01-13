# SRE Observability Engine - Source Code

This directory contains the core implementation of the SRE Observability Engine.

## Structure

```
src/
├── __init__.py                      # Package initialization
├── mcp_datadog_server.py            # MCP server for Datadog metrics
├── start_mcp_server.py              # Server launcher with .env support
└── requirements.txt                 # Python dependencies
```

## Components

### MCP Datadog Server (`mcp_datadog_server.py`)

FastMCP server that exposes three tools:

1. **query_metrics** - Query timeseries metrics from Datadog
   - Parameters: `query` (str), `days_back` (int, optional)
   - Returns: JSON with series data and timestamps

2. **search_metrics** - Search available metrics
   - Parameters: `prefix` (str)
   - Returns: List of matching metrics

3. **get_metric_tags** - Get tag information
   - Parameters: `metric_name` (str)
   - Returns: Tag metadata

### Server Launcher (`start_mcp_server.py`)

Entry point that:
- Loads environment variables from `.env`
- Initializes Datadog client
- Starts MCP server on stdio

### Lambda Function (`lambda_function.py`)

AWS Lambda handler for:
- Batch report generation
- Multi-service metric aggregation
- PDF report creation

### Bedrock Integration (`bedrock_function.py`)

AWS Bedrock AI for:
- Metric analysis
- Anomaly detection
- Report insights

## Usage

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set credentials
export DD_API_KEY=your-api-key
export DD_APP_KEY=your-app-key

# Run server
python -m start_mcp_server
```

### Docker Deployment

```bash
# Build image
docker build -f ../Dockerfile.mcp -t mcp-datadog .

# Run container
docker run -e DD_API_KEY=xxx -e DD_APP_KEY=yyy mcp-datadog

# Or use docker-compose
cd ..
docker-compose up -d mcp-datadog
```

### AWS Lambda

Configure environment variables:
- `DD_API_KEY`
- `DD_APP_KEY`
- `INPUT_BUCKET` - S3 bucket with config
- `S3_BUCKET_NAME` - Output S3 bucket

Deploy:
```bash
zip -r lambda.zip src/
aws lambda update-function-code --function-name my-function --zip-file fileb://lambda.zip
```

## Configuration

### Environment Variables

Required:
- `DD_API_KEY` - Datadog API key
- `DD_APP_KEY` - Datadog application key

Optional:
- `DD_SITE` - Datadog site (default: `datadoghq.com`)
- `LOG_LEVEL` - Logging level (default: `info`)

AWS Lambda only:
- `INPUT_BUCKET` - S3 input bucket
- `INPUT_KEY` - S3 config file path
- `S3_BUCKET_NAME` - S3 output bucket
- `S3_KEY_PREFIX` - S3 output prefix
- `BEDROCK_MODEL_ID` - AWS Bedrock model
- `REGION` - AWS region

### Configuration File (`config_service.yaml`)

```yaml
services:
  mytelkomsel:
    account: mytelkomsel-prod
    metrics:
      - alb_5xx_error_rate
      - rds_cpu_utilization
    alerting:
      enabled: true
      channels:
        - slack
        - email
```

## Dependencies

Core dependencies in `requirements.txt`:

- `mcp>=0.5.0` - Model Context Protocol SDK
- `datadog>=0.47.0` - Datadog API client
- `python-dotenv>=1.0.0` - Environment management
- `asyncio` - Async support
- `httpx>=0.24.0` - HTTP client
- `structlog>=23.0.0` - Structured logging

AWS-specific (optional):
- `boto3` - AWS SDK
- `reportlab` - PDF generation

## Testing

```bash
# Run tests
python -m pytest tests/

# With coverage
python -m pytest --cov=src tests/

# Integration tests
python -m pytest tests/integration/ -v
```

## Development

### Adding New Tools

Edit `mcp_datadog_server.py`:

```python
@mcp.tool()
def new_tool(param: str) -> str:
    """Tool description"""
    result = process(param)
    return json.dumps(result)
```

### Adding New Metrics

Update `config_service.yaml`:

```yaml
services:
  myservice:
    metrics:
      - new_metric_name
```

### Debugging

Enable verbose logging:

```bash
export LOG_LEVEL=debug
python -m start_mcp_server
```

Check server logs:

```bash
# Docker
docker-compose logs -f mcp-datadog

# Local
tail -f /tmp/mcp-server.log
```

## Deployment

### Development

```bash
# Run locally with live reload
python -m start_mcp_server
```

### Production

```bash
# Using docker-compose
docker-compose -f ../docker-compose.yml up -d mcp-datadog

# Using Docker directly
docker run -d \
  -e DD_API_KEY=$DD_API_KEY \
  -e DD_APP_KEY=$DD_APP_KEY \
  -p 3000:3000 \
  --restart unless-stopped \
  mcp-datadog:latest

# Using Kubernetes
kubectl apply -f ../k8s/mcp-deployment.yaml
```

## Security

1. **Never commit credentials**
   - Use `.env` file (not in git)
   - Use AWS Secrets Manager
   - Use environment variables

2. **Restrict access**
   - Use firewall rules
   - Use SSH tunnels for remote access
   - Use VPN for external clients

3. **Rotate credentials regularly**
   - Update API keys in Datadog
   - Update in all deployment environments

See `../EXTERNAL_ACCESS.md` for detailed security guidance.

## Troubleshooting

### "DD_API_KEY not found"
```bash
# Check if .env exists
ls -la ../.env

# Set manually
export DD_API_KEY=your-key
export DD_APP_KEY=your-key
```

### "Connection refused"
```bash
# Check if server is running
ps aux | grep start_mcp_server

# Check port
lsof -i :3000
```

### "Datadog API error"
```bash
# Verify credentials
python -c "from mcp_datadog_server import DatadogMetricsClient; \
  client = DatadogMetricsClient('$DD_API_KEY', '$DD_APP_KEY'); \
  print('Connected!')"
```

## Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Submit PR

Follow PEP 8 style guide and use type hints.

## License

See LICENSE file in root directory.
