#!/usr/bin/env python3
"""
MCP Server for Datadog Metrics Integration

This MCP server exposes tools to:
- Query timeseries metrics from Datadog
- Search and list available metrics

Usage:
  python mcp_datadog_server.py

Environment Variables:
  DD_API_KEY: Datadog API key
  DD_APP_KEY: Datadog Application key
  DD_SITE: Datadog site (default: datadoghq.com)
"""

import os
import sys
import json
import time
import io
import base64
from typing import Any
from datetime import datetime
import logging

# MCP imports
from mcp.server.fastmcp import FastMCP
import mcp.types as types

# Datadog imports
from datadog_api_client.v1 import ApiClient, Configuration
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.api.tags_api import TagsApi

# Image generation
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Datadog Client Initialization
# =============================================================================

class DatadogMetricsClient:
    """Wrapper around Datadog API client for metrics operations."""

    def __init__(self, api_key: str, app_key: str, site: str = "datadoghq.com"):
        """Initialize Datadog API client."""
        self.api_key = api_key
        self.app_key = app_key
        self.site = site

        config = Configuration()
        config.api_key["apiKeyAuth"] = api_key
        config.api_key["appKeyAuth"] = app_key
        config.server_variables["site"] = site

        self.api_client = ApiClient(config)
        self.metrics_api = MetricsApi(self.api_client)
        self.tags_api = TagsApi(self.api_client)

    def query_metrics(
        self,
        query: str,
        from_timestamp: int,
        to_timestamp: int,
    ) -> dict[str, Any]:
        """
        Query timeseries metrics from Datadog.

        Args:
            query: Datadog metric query (e.g., "avg:system.cpu{*}")
            from_timestamp: Start time (unix seconds)
            to_timestamp: End time (unix seconds)

        Returns:
            Dictionary with series data and metadata
        """
        try:
            response = self.metrics_api.query_metrics(
                _from=from_timestamp,
                to=to_timestamp,
                query=query,
            )

            series_list = []
            if response.series:
                for s in response.series:
                    scope = getattr(s, "scope", None) or ""
                    pointlist = getattr(s, "pointlist", None) or []
                    
                    # Convert points to [timestamp, value] format
                    points = []
                    for p in pointlist:
                        try:
                            # Try list access first
                            ts = int(p[0] / 1000) if p[0] else 0
                            val = float(p[1]) if p[1] is not None else 0.0
                            points.append([ts, val])
                        except (TypeError, KeyError, IndexError):
                            # Fallback: try as object attributes
                            try:
                                ts = int(getattr(p, 'timestamp', 0) / 1000)
                                val = float(getattr(p, 'value', 0))
                                if ts > 0 or val > 0:  # Only add non-empty points
                                    points.append([ts, val])
                            except:
                                pass  # Skip malformed points
                    
                    if points:  # Only add series if it has data
                        series_list.append({"scope": scope, "points": points})

            return {
                "status": "success",
                "query": query,
                "from": from_timestamp,
                "to": to_timestamp,
                "series_count": len(series_list),
                "series": series_list,
            }
        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            return {
                "status": "error",
                "query": query,
                "error": str(e),
            }

    def search_metrics(self, prefix: str) -> dict[str, Any]:
        """
        Search for metrics matching a prefix.

        Args:
            prefix: Metric prefix to search (e.g., "aws.applicationelb")

        Returns:
            Dictionary with matching metrics
        """
        try:
            response = self.metrics_api.list_metrics(q=prefix)
            metrics = []
            
            # response.results is a MetricSearchResponseResults object
            # Try to iterate or extract the data
            if response.results:
                try:
                    # Try as iterable
                    for m in response.results:
                        name = getattr(m, 'name', str(m))
                        if name:
                            metrics.append(name)
                except TypeError:
                    # Try as object with direct attributes
                    results_obj = response.results
                    # Check if it has results attribute
                    if hasattr(results_obj, 'results'):
                        for m in results_obj.results:
                            name = getattr(m, 'name', str(m))
                            if name:
                                metrics.append(name)
                    else:
                        # Try to convert to dict and extract
                        logger.warning(f"Unexpected results format: {type(results_obj)}")
            
            return {
                "status": "success",
                "prefix": prefix,
                "count": len(metrics),
                "metrics": metrics[:50],  # Limit to first 50
            }
        except Exception as e:
            logger.error(f"Failed to search metrics: {e}")
            return {
                "status": "error",
                "prefix": prefix,
                "error": str(e),
            }

    def get_metric_tags(self, metric_name: str) -> dict[str, Any]:
        """
        Get available tags for a metric.

        Args:
            metric_name: Name of the metric

        Returns:
            Dictionary with tag information
        """
        try:
            return {
                "status": "success",
                "metric": metric_name,
                "message": "Use metric query with filters to discover tags",
            }
        except Exception as e:
            logger.error(f"Failed to get metric tags: {e}")
            return {
                "status": "error",
                "metric": metric_name,
                "error": str(e),
            }

    def generate_metric_image(
        self,
        query: str,
        from_timestamp: int,
        to_timestamp: int,
        title: str = None,
        format: str = "png"
    ) -> dict[str, Any]:
        """
        Generate a chart image for Datadog metrics.

        Args:
            query: Datadog metric query
            from_timestamp: Start time (unix seconds)
            to_timestamp: End time (unix seconds)
            title: Chart title (optional)
            format: Image format - 'png' or 'base64'

        Returns:
            Dictionary with image data or base64 string
        """
        try:
            # Query metrics first
            result = self.query_metrics(query, from_timestamp, to_timestamp)
            
            if result.get("status") != "success" or not result.get("series"):
                return {
                    "status": "error",
                    "error": "No data available for the query"
                }
            
            # Create figure
            plt.figure(figsize=(12, 6))
            
            # Plot each series
            for series in result["series"]:
                timestamps = [p[0] for p in series["points"]]
                values = [p[1] for p in series["points"]]
                
                # Convert timestamps to datetime
                dates = [datetime.fromtimestamp(ts) for ts in timestamps]
                
                # Plot line
                label = series["scope"] if series["scope"] else query
                plt.plot(dates, values, marker='o', linestyle='-', linewidth=2, markersize=4, label=label)
            
            # Formatting
            plt.xlabel('Time', fontsize=12)
            plt.ylabel('Value', fontsize=12)
            plt.title(title or query, fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.legend(loc='best')
            
            # Format x-axis
            plt.gcf().autofmt_xdate()
            ax = plt.gca()
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            
            plt.tight_layout()
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            if format == "base64":
                # Return base64 encoded image
                img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                return {
                    "status": "success",
                    "query": query,
                    "format": "base64",
                    "image": img_base64,
                    "mime_type": "image/png"
                }
            else:
                # Return raw bytes
                return {
                    "status": "success",
                    "query": query,
                    "format": "png",
                    "image_bytes": buf.getvalue(),
                    "mime_type": "image/png"
                }
                
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return {
                "status": "error",
                "query": query,
                "error": str(e)
            }


# =============================================================================
# MCP Server Setup
# =============================================================================

def create_mcp_server() -> FastMCP:
    """Create MCP server with Datadog tools."""
    
    # Initialize Datadog client
    api_key = os.getenv("DD_API_KEY")
    app_key = os.getenv("DD_APP_KEY")
    site = os.getenv("DD_SITE", "datadoghq.com")

    if not api_key or not app_key:
        raise ValueError("DD_API_KEY and DD_APP_KEY environment variables required")

    dd_client = DatadogMetricsClient(api_key, app_key, site)

    # Create MCP server
    mcp = FastMCP("datadog-metrics-mcp")

    # Register tools using decorators
    @mcp.tool()
    def query_metrics(
        query: str,
        days_back: int = 7,
    ) -> str:
        """
        Query timeseries metrics from Datadog.
        
        Args:
            query: Datadog metric query (e.g., 'sum:aws.applicationelb.httpcode_target_5xx{account_name:prod}' or 'avg:system.cpu{*}')
            days_back: Number of days to look back (default: 7)
        
        Returns:
            JSON string with series data and timestamps
        """
        to_ts = int(time.time())
        from_ts = to_ts - days_back * 24 * 3600
        
        result = dd_client.query_metrics(query, from_ts, to_ts)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def search_metrics(prefix: str) -> str:
        """
        Search for available metrics by prefix.
        
        Args:
            prefix: Metric prefix to search (e.g., 'aws.applicationelb', 'system.cpu')
        
        Returns:
            JSON string with list of matching metrics
        """
        result = dd_client.search_metrics(prefix)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def get_metric_tags(metric_name: str) -> str:
        """
        Get information about tags available for a metric.
        
        Args:
            metric_name: Name of the metric (e.g., 'aws.applicationelb.request_count')
        
        Returns:
            JSON string with tag information
        """
        result = dd_client.get_metric_tags(metric_name)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def generate_metric_chart(
        query: str,
        days_back: int = 7,
        title: str = None
    ) -> str:
        """
        Generate a PNG chart image for Datadog metrics.
        
        Args:
            query: Datadog metric query (e.g., 'avg:system.cpu.user{*}')
            days_back: Number of days to look back (default: 7)
            title: Chart title (optional, defaults to query)
        
        Returns:
            JSON string with base64-encoded PNG image
        """
        to_ts = int(time.time())
        from_ts = to_ts - days_back * 24 * 3600
        
        result = dd_client.generate_metric_image(query, from_ts, to_ts, title, format="base64")
        return json.dumps(result, indent=2)

    logger.info("✅ MCP Server created with tools:")
    logger.info("  - query_metrics: Query timeseries data")
    logger.info("  - search_metrics: Search available metrics")
    logger.info("  - get_metric_tags: Get metric tag information")
    logger.info("  - generate_metric_chart: Generate PNG chart image")

    return mcp


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the MCP server."""
    try:
        mcp = create_mcp_server()
        logger.info("🚀 Starting Datadog Metrics MCP Server...")
        logger.info(f"API Site: {os.getenv('DD_SITE', 'datadoghq.com')}")
        mcp.run(transport="stdio")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
