# Docker Deployment Guide

This directory contains Docker configuration for running the Datadog MCP Server in a containerized environment.

## Files

- **Dockerfile.mcp** - Docker image definition
- **docker-compose.yml** - Docker Compose orchestration
- **.dockerignore** - Files excluded from Docker build
- **.env.example** - Example environment variables (copy to `.env`)

## Quick Start

### 1. Configure Environment

Create `.env` file from example:

```bash
cp .env.example .env
```

Edit `.env` with your Datadog credentials:

```bash
DD_API_KEY=your-datadog-api-key-here
DD_APP_KEY=your-datadog-application-key-here
DD_SITE=datadoghq.com
MCP_PORT=8002
LOG_LEVEL=info
```

### 2. Start Server

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f mcp-datadog

# Stop server
docker-compose down
```

### 3. Verify Running

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs mcp-datadog
```

## Docker Compose Configuration

### Service Definition

```yaml
services:
  mcp-datadog:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mcp
    container_name: mcp-datadog-server
    restart: unless-stopped
    environment:
      - DD_API_KEY=${DD_API_KEY}
      - DD_APP_KEY=${DD_APP_KEY}
      - DD_SITE=${DD_SITE:-datadoghq.com}
      - MCP_PORT=${MCP_PORT:-8002}
      - LOG_LEVEL=${LOG_LEVEL:-info}
    ports:
      - "${MCP_PORT:-8002}:8002"
    volumes:
      - ../src:/app/src:ro
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

## Dockerfile Structure

```dockerfile
FROM python:3.14-slim

# Install dependencies
COPY src/requirements.txt /app/src/
RUN pip install --no-cache-dir -r /app/src/requirements.txt

# Copy source code
COPY src/ /app/src/

# Create non-root user
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Start server
WORKDIR /app
CMD ["python", "-m", "src.start_mcp_server"]
```

## External Access Setup

### Method 1: SSH Tunnel (Recommended)

**On server machine:**
```bash
docker-compose up -d
```

**On client machine:**
```bash
ssh -L 8002:localhost:8002 user@server-ip
```

**Configure Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "datadog": {
      "command": "socat",
      "args": ["-", "TCP:localhost:8002"]
    }
  }
}
```

### Method 2: Direct Network Exposure

**Warning:** Only use on trusted networks or with proper firewall rules.

**docker-compose.yml:**
```yaml
services:
  mcp-datadog:
    ports:
      - "0.0.0.0:8002:8002"  # Expose on all interfaces
```

**Configure Claude Desktop:**
```json
{
  "mcpServers": {
    "datadog": {
      "command": "socat",
      "args": ["-", "TCP:server-ip:8002"]
    }
  }
}
```

**Firewall rules:**
```bash
# Ubuntu/Debian
sudo ufw allow 8002/tcp

# CentOS/RHEL
sudo firewall-cmd --add-port=8002/tcp --permanent
sudo firewall-cmd --reload
```

### Method 3: socat Bridge

**Install socat:**
```bash
# macOS
brew install socat

# Ubuntu/Debian
sudo apt-get install socat

# CentOS/RHEL
sudo yum install socat
```

**Create bridge:**
```bash
socat TCP-LISTEN:8002,reuseaddr,fork EXEC:"docker-compose -f /path/to/docker-compose.yml exec -T mcp-datadog python -m src.start_mcp_server"
```

### Method 4: Docker Network Bridge

**docker-compose.yml:**
```yaml
services:
  mcp-datadog:
    networks:
      - mcp-network

  mcp-bridge:
    image: alpine/socat
    command: tcp-listen:8002,fork,reuseaddr tcp-connect:mcp-datadog:8002
    ports:
      - "8002:8002"
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DD_API_KEY` | Yes | - | Datadog API key |
| `DD_APP_KEY` | Yes | - | Datadog Application key |
| `DD_SITE` | No | `datadoghq.com` | Datadog site (e.g., `datadoghq.eu`) |
| `MCP_PORT` | No | `8002` | Port for MCP server |
| `LOG_LEVEL` | No | `info` | Logging level (debug, info, warning, error) |

## Security Best Practices

### 1. Credentials Management

**Never commit `.env` file:**
```bash
# Add to .gitignore
echo "docker/.env" >> .gitignore
```

**Use Docker secrets (production):**
```yaml
services:
  mcp-datadog:
    secrets:
      - dd_api_key
      - dd_app_key
    environment:
      - DD_API_KEY_FILE=/run/secrets/dd_api_key
      - DD_APP_KEY_FILE=/run/secrets/dd_app_key

secrets:
  dd_api_key:
    file: ./secrets/dd_api_key.txt
  dd_app_key:
    file: ./secrets/dd_app_key.txt
```

### 2. Network Security

**Restrict access by IP:**
```yaml
ports:
  - "127.0.0.1:8002:8002"  # Only localhost
```

**Use VPN or SSH tunnel** for remote access instead of exposing ports.

### 3. Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

## Troubleshooting

### Container won't start

**Check logs:**
```bash
docker-compose logs mcp-datadog
```

**Common issues:**
- Missing `.env` file → Copy from `.env.example`
- Invalid credentials → Verify DD_API_KEY and DD_APP_KEY
- Port already in use → Change MCP_PORT in `.env`

### Build fails

**Rebuild without cache:**
```bash
docker-compose build --no-cache
```

**Check Dockerfile syntax:**
```bash
docker build -f Dockerfile.mcp -t mcp-datadog ..
```

### Cannot connect externally

**Verify port is open:**
```bash
# On server
netstat -tulpn | grep 8002

# From client
telnet server-ip 8002
```

**Check firewall:**
```bash
# Ubuntu/Debian
sudo ufw status

# CentOS/RHEL
sudo firewall-cmd --list-all
```

### Health check fails

**Test manually:**
```bash
docker-compose exec mcp-datadog python -c "import sys; sys.exit(0)"
```

**Check logs for errors:**
```bash
docker-compose logs --tail=50 mcp-datadog
```

## Maintenance

### Update server

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

### View logs

```bash
# Real-time logs
docker-compose logs -f mcp-datadog

# Last 100 lines
docker-compose logs --tail=100 mcp-datadog
```

### Cleanup

```bash
# Stop and remove container
docker-compose down

# Remove image
docker rmi mcp-datadog

# Remove volumes
docker-compose down -v
```

### Backup configuration

```bash
# Backup .env
cp .env .env.backup

# Export container
docker export mcp-datadog-server > mcp-datadog-backup.tar
```

## Production Deployment

### 1. Use Docker Secrets

```bash
# Create secrets
echo "your-api-key" | docker secret create dd_api_key -
echo "your-app-key" | docker secret create dd_app_key -
```

### 2. Configure Logging

**docker-compose.yml:**
```yaml
services:
  mcp-datadog:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. Set Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
  restart_policy:
    condition: on-failure
    delay: 5s
    max_attempts: 3
```

### 4. Use Health Checks

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

### 5. Enable Auto-restart

```yaml
restart: unless-stopped
```

## Advanced Configuration

### Multi-container Setup

```yaml
services:
  mcp-datadog:
    # ... main service
  
  mcp-proxy:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - mcp-datadog
```

### Custom Network

```yaml
networks:
  mcp-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Volume Mounts

```yaml
volumes:
  - ../src:/app/src:ro  # Read-only source
  - ./logs:/app/logs    # Writable logs
```

## Next Steps

- See `../src/README.md` for MCP server source documentation
- See `../test/README.md` for testing examples
- See root `MCP_DATADOG_README.md` for project overview

## Support

For issues or questions:
- Check logs: `docker-compose logs mcp-datadog`
- Review documentation in `../src/README.md`
- Check Datadog API status: https://status.datadoghq.com/
