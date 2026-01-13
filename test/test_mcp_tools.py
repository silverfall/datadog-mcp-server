#!/usr/bin/env python3
"""
Test script for MCP Datadog Server tools.

This script demonstrates how to test the MCP server tools programmatically.
"""

import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from mcp_datadog_server import DatadogMetricsClient


def test_query_metrics():
    """Test querying Datadog metrics."""
    print("\n=== Testing query_metrics ===")
    
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    # Initialize client
    client = DatadogMetricsClient()
    
    # Example query
    query = "avg:system.cpu.user{*}"
    days_back = 1
    
    print(f"Query: {query}")
    print(f"Days back: {days_back}")
    
    try:
        result = client.query_metrics(query, days_back)
        print(f"\nResult: {result[:500]}..." if len(result) > 500 else f"\nResult: {result}")
        print("✅ query_metrics test passed")
    except Exception as e:
        print(f"❌ query_metrics test failed: {e}")


def test_search_metrics():
    """Test searching for Datadog metrics."""
    print("\n=== Testing search_metrics ===")
    
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    # Initialize client
    client = DatadogMetricsClient()
    
    # Example prefix
    prefix = "system"
    
    print(f"Prefix: {prefix}")
    
    try:
        result = client.search_metrics(prefix)
        print(f"\nResult: {result[:500]}..." if len(result) > 500 else f"\nResult: {result}")
        print("✅ search_metrics test passed")
    except Exception as e:
        print(f"❌ search_metrics test failed: {e}")


def test_get_metric_tags():
    """Test getting tags for a Datadog metric."""
    print("\n=== Testing get_metric_tags ===")
    
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    # Initialize client
    client = DatadogMetricsClient()
    
    # Example metric name
    metric_name = "system.cpu.user"
    
    print(f"Metric name: {metric_name}")
    
    try:
        result = client.get_metric_tags(metric_name)
        print(f"\nResult: {result[:500]}..." if len(result) > 500 else f"\nResult: {result}")
        print("✅ get_metric_tags test passed")
    except Exception as e:
        print(f"❌ get_metric_tags test failed: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Datadog Server - Tool Tests")
    print("=" * 60)
    
    # Check for credentials
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    if not os.getenv('DD_API_KEY') or not os.getenv('DD_APP_KEY'):
        print("\n❌ Error: DD_API_KEY and DD_APP_KEY must be set in .env file")
        sys.exit(1)
    
    print("\n✅ Credentials found")
    
    # Run tests
    test_query_metrics()
    test_search_metrics()
    test_get_metric_tags()
    
    print("\n" + "=" * 60)
    print("All tests completed")
    print("=" * 60)
