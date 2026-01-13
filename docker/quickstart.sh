#!/bin/bash
# Quick start script for MCP Datadog Server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "=========================================="
echo "MCP Datadog Server - Quick Start"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "Create .env with your Datadog credentials:"
    echo "  echo 'DD_API_KEY=your-key' > .env"
    echo "  echo 'DD_APP_KEY=your-key' >> .env"
    exit 1
fi

echo "✅ .env file found"
echo ""

# Option 1: Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "Option 1: Using Docker Compose (Recommended)"
    echo "  docker-compose up -d mcp-datadog"
    echo "  docker-compose logs -f mcp-datadog"
    echo ""
fi

# Option 2: Local Python
echo "Option 2: Using Local Python"
echo "  cd src"
echo "  pip install -r requirements.txt"
echo "  python -m start_mcp_server"
echo ""

# Option 3: Docker
if command -v docker &> /dev/null; then
    echo "Option 3: Using Docker"
    echo "  docker build -f Dockerfile.mcp -t mcp-datadog ."
    echo "  docker run -e DD_API_KEY=\$(grep DD_API_KEY .env | cut -d= -f2) \\"
    echo "    -e DD_APP_KEY=\$(grep DD_APP_KEY .env | cut -d= -f2) mcp-datadog"
    echo ""
fi

echo "=========================================="
echo "For external access, see: EXTERNAL_ACCESS.md"
echo "=========================================="
