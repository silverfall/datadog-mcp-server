#!/usr/bin/env python3
"""
Example queries for Datadog MCP Server.

This file contains example queries you can use to test the MCP server.
"""

# Example 1: Query system CPU metrics
QUERY_SYSTEM_CPU = {
    "query": "avg:system.cpu.user{*}",
    "days_back": 7
}

# Example 2: Query AWS metrics
QUERY_AWS_EC2 = {
    "query": "avg:aws.ec2.cpuutilization{*} by {host}",
    "days_back": 1
}

# Example 3: Query application metrics with tags
QUERY_APP_REQUESTS = {
    "query": "sum:trace.http.request.hits{service:my-service,env:production}",
    "days_back": 3
}

# Example 4: Query database metrics
QUERY_DATABASE = {
    "query": "avg:postgresql.connections{*}",
    "days_back": 7
}

# Example 5: Query container metrics
QUERY_CONTAINERS = {
    "query": "avg:docker.cpu.usage{*} by {container_name}",
    "days_back": 1
}

# Example metric search prefixes
SEARCH_PREFIXES = [
    "system",      # System metrics
    "aws",         # AWS metrics
    "docker",      # Docker metrics
    "kubernetes",  # K8s metrics
    "trace",       # APM traces
    "custom",      # Custom metrics
]

# Example metric names for tag retrieval
METRIC_NAMES = [
    "system.cpu.user",
    "system.mem.used",
    "system.disk.used",
    "aws.ec2.cpuutilization",
    "docker.cpu.usage",
]


def print_examples():
    """Print all example queries."""
    print("=" * 70)
    print("EXAMPLE DATADOG QUERIES")
    print("=" * 70)
    
    print("\n1. Query System CPU:")
    print(f"   Query: {QUERY_SYSTEM_CPU['query']}")
    print(f"   Days back: {QUERY_SYSTEM_CPU['days_back']}")
    
    print("\n2. Query AWS EC2:")
    print(f"   Query: {QUERY_AWS_EC2['query']}")
    print(f"   Days back: {QUERY_AWS_EC2['days_back']}")
    
    print("\n3. Query Application Requests:")
    print(f"   Query: {QUERY_APP_REQUESTS['query']}")
    print(f"   Days back: {QUERY_APP_REQUESTS['days_back']}")
    
    print("\n4. Query Database:")
    print(f"   Query: {QUERY_DATABASE['query']}")
    print(f"   Days back: {QUERY_DATABASE['days_back']}")
    
    print("\n5. Query Containers:")
    print(f"   Query: {QUERY_CONTAINERS['query']}")
    print(f"   Days back: {QUERY_CONTAINERS['days_back']}")
    
    print("\n" + "=" * 70)
    print("EXAMPLE METRIC SEARCHES")
    print("=" * 70)
    
    for prefix in SEARCH_PREFIXES:
        print(f"  - {prefix}")
    
    print("\n" + "=" * 70)
    print("EXAMPLE METRICS FOR TAG RETRIEVAL")
    print("=" * 70)
    
    for metric in METRIC_NAMES:
        print(f"  - {metric}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print_examples()
