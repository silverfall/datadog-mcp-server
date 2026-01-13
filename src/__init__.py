"""
SRE Observability Engine - MCP Datadog Integration

This package contains:
- MCP Server for Datadog metrics queries
- Lambda functions for report generation
- Configuration management
"""

__version__ = "1.0.0"
__author__ = "SRE Team"

from .mcp_datadog_server import DatadogMetricsClient, create_mcp_server

__all__ = [
    "DatadogMetricsClient",
    "create_mcp_server",
]
