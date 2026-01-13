#!/usr/bin/env python3
"""
HTTP Server wrapper for MCP Datadog Server.

Provides HTTP/SSE interface to access MCP tools without stdio-based clients.
Useful for integrating with HTTP clients, webhooks, and web services.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.responses import StreamingResponse, Response
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mcp_datadog_server import DatadogMetricsClient

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Get credentials from environment
DD_API_KEY = os.getenv("DD_API_KEY")
DD_APP_KEY = os.getenv("DD_APP_KEY")
DD_SITE = os.getenv("DD_SITE", "datadoghq.com")
AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", None)  # Optional: if set, requires Authorization header

if not DD_API_KEY or not DD_APP_KEY:
    print("ERROR: DD_API_KEY and DD_APP_KEY environment variables are required")
    sys.exit(1)

# Authorization dependency
def verify_token(authorization: Optional[str] = Header(None)):
    """Verify authorization token if AUTH_TOKEN is set."""
    if AUTH_TOKEN:  # Only enforce if token is configured
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        
        # Accept "Bearer token" format
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
        
        if token != AUTH_TOKEN:
            raise HTTPException(status_code=403, detail="Invalid authorization token")
    
    return True

app = FastAPI(
    title="Datadog MCP HTTP Server",
    description="HTTP wrapper for MCP Datadog Server with Server-Sent Events streaming",
    version="1.0.0"
)

# Initialize Datadog client
client = DatadogMetricsClient(DD_API_KEY, DD_APP_KEY, DD_SITE)


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {
        "status": "healthy",
        "service": "datadog-mcp-http",
        "version": "1.0.0",
        "auth_required": bool(AUTH_TOKEN)
    }


@app.get("/tools")
async def list_tools(authorized: bool = Depends(verify_token)):
    """List available MCP tools."""
    return {
        "tools": [
            {
                "name": "query_metrics",
                "description": "Query Datadog metrics with time-series data",
                "parameters": {
                    "query": {"type": "string", "description": "Datadog metric query"},
                    "days_back": {"type": "integer", "description": "Days to look back (default: 7)"}
                }
            },
            {
                "name": "search_metrics",
                "description": "Search for available metrics by prefix",
                "parameters": {
                    "prefix": {"type": "string", "description": "Metric prefix to search"}
                }
            },
            {
                "name": "get_metric_tags",
                "description": "Get tag information for a metric",
                "parameters": {
                    "metric_name": {"type": "string", "description": "Full metric name"}
                }
            },
            {
                "name": "generate_metric_chart",
                "description": "Generate a PNG chart image for metrics",
                "parameters": {
                    "query": {"type": "string", "description": "Datadog metric query"},
                    "days_back": {"type": "integer", "description": "Days to look back (default: 7)"},
                    "title": {"type": "string", "description": "Chart title (optional)"}
                }
            }
        ]
    }


@app.get("/query_metrics")
async def query_metrics_endpoint(
    query: str = Query(..., description="Datadog metric query"),
    days_back: int = Query(7, description="Days to look back"),
    authorized: bool = Depends(verify_token)
):
    """
    Query Datadog metrics.
    
    Example: /query_metrics?query=avg:system.cpu.user{*}&days_back=7
    """
    try:
        result = client.query_metrics(query, days_back)
        return {
            "status": "success",
            "tool": "query_metrics",
            "parameters": {"query": query, "days_back": days_back},
            "result": json.loads(result) if isinstance(result, str) else result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/query_metrics/stream")
async def query_metrics_stream(
    query: str = Query(..., description="Datadog metric query"),
    days_back: int = Query(7, description="Days to look back"),
    authorized: bool = Depends(verify_token)
):
    """
    Query Datadog metrics with SSE (Server-Sent Events) streaming.
    
    Example: /query_metrics/stream?query=avg:system.cpu.user{*}&days_back=7
    """
    async def generate():
        try:
            # Send query details
            yield f"data: {json.dumps({'type': 'start', 'query': query, 'days_back': days_back})}\n\n"
            
            # Query metrics
            result = client.query_metrics(query, days_back)
            result_data = json.loads(result) if isinstance(result, str) else result
            
            # Send result
            yield f"data: {json.dumps({'type': 'data', 'result': result_data})}\n\n"
            
            # Send complete
            yield f"data: {json.dumps({'type': 'complete', 'status': 'success'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/search_metrics")
async def search_metrics_endpoint(
    prefix: str = Query(..., description="Metric prefix"),
    authorized: bool = Depends(verify_token)
):
    """
    Search for Datadog metrics by prefix.
    
    Example: /search_metrics?prefix=system
    """
    try:
        result = client.search_metrics(prefix)
        return {
            "status": "success",
            "tool": "search_metrics",
            "parameters": {"prefix": prefix},
            "result": json.loads(result) if isinstance(result, str) else result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/search_metrics/stream")
async def search_metrics_stream(
    prefix: str = Query(..., description="Metric prefix"),
    authorized: bool = Depends(verify_token)
):
    """
    Search for Datadog metrics with SSE streaming.
    
    Example: /search_metrics/stream?prefix=system
    """
    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'start', 'prefix': prefix})}\n\n"
            
            result = client.search_metrics(prefix)
            result_data = json.loads(result) if isinstance(result, str) else result
            
            yield f"data: {json.dumps({'type': 'data', 'result': result_data})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'status': 'success'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/get_metric_tags")
async def get_metric_tags_endpoint(
    metric_name: str = Query(..., description="Metric name"),
    authorized: bool = Depends(verify_token)
):
    """
    Get tags for a Datadog metric.
    
    Example: /get_metric_tags?metric_name=system.cpu.user
    """
    try:
        result = client.get_metric_tags(metric_name)
        return {
            "status": "success",
            "tool": "get_metric_tags",
            "parameters": {"metric_name": metric_name},
            "result": json.loads(result) if isinstance(result, str) else result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/get_metric_tags/stream")
async def get_metric_tags_stream(
    metric_name: str = Query(..., description="Metric name"),
    authorized: bool = Depends(verify_token)
):
    """
    Get metric tags with SSE streaming.
    
    Example: /get_metric_tags/stream?metric_name=system.cpu.user
    """
    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'start', 'metric_name': metric_name})}\n\n"
            
            result = client.get_metric_tags(metric_name)
            result_data = json.loads(result) if isinstance(result, str) else result
            
            yield f"data: {json.dumps({'type': 'data', 'result': result_data})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'status': 'success'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/call")
async def call_tool(request: Dict[str, Any], authorized: bool = Depends(verify_token)):
    """
    Universal endpoint to call any MCP tool.
    
    Example POST body:
    ```json
    {
        "tool": "query_metrics",
        "parameters": {
            "query": "avg:system.cpu.user{*}",
            "days_back": 7
        }
    }
    ```
    """
    try:
        tool_name = request.get("tool")
        parameters = request.get("parameters", {})
        
        if tool_name == "query_metrics":
            result = client.query_metrics(
                parameters.get("query"),
                parameters.get("days_back", 7)
            )
        elif tool_name == "search_metrics":
            result = client.search_metrics(parameters.get("prefix"))
        elif tool_name == "get_metric_tags":
            result = client.get_metric_tags(parameters.get("metric_name"))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
        
        return {
            "status": "success",
            "tool": tool_name,
            "parameters": parameters,
            "result": json.loads(result) if isinstance(result, str) else result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/call/stream")
async def call_tool_stream(request: Dict[str, Any], authorized: bool = Depends(verify_token)):
    """
    Universal endpoint with SSE streaming.
    
    Same as /call but streams the response.
    """
    async def generate():
        try:
            tool_name = request.get("tool")
            parameters = request.get("parameters", {})
            
            yield f"data: {json.dumps({'type': 'start', 'tool': tool_name, 'parameters': parameters})}\n\n"
            
            if tool_name == "query_metrics":
                result = client.query_metrics(
                    parameters.get("query"),
                    parameters.get("days_back", 7)
                )
            elif tool_name == "search_metrics":
                result = client.search_metrics(parameters.get("prefix"))
            elif tool_name == "get_metric_tags":
                result = client.get_metric_tags(parameters.get("metric_name"))
            else:
                raise Exception(f"Unknown tool: {tool_name}")
            
            result_data = json.loads(result) if isinstance(result, str) else result
            
            yield f"data: {json.dumps({'type': 'data', 'result': result_data})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'status': 'success'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/generate_metric_chart")
async def generate_chart_endpoint(
    query: str = Query(..., description="Datadog metric query"),
    days_back: int = Query(7, description="Days to look back"),
    title: str = Query(None, description="Chart title"),
    format: str = Query("png", description="Output format: png or base64"),
    authorized: bool = Depends(verify_token)
):
    """
    Generate a chart image for Datadog metrics.
    
    Example: /generate_metric_chart?query=avg:system.cpu.user{*}&days_back=7&format=png
    """
    try:
        import time
        to_ts = int(time.time())
        from_ts = to_ts - days_back * 24 * 3600
        
        result = client.generate_metric_image(query, from_ts, to_ts, title, format=format)
        
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to generate image"))
        
        if format == "base64":
            return {
                "status": "success",
                "tool": "generate_metric_chart",
                "parameters": {"query": query, "days_back": days_back, "title": title},
                "result": result
            }
        else:
            # Return PNG image directly
            return Response(
                content=result["image_bytes"],
                media_type="image/png",
                headers={"Content-Disposition": f'inline; filename="metric_chart.png"'}
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("MCP_HTTP_PORT", 8000))
    
    auth_status = "🔐 AUTH ENABLED" if AUTH_TOKEN else "🔓 AUTH DISABLED (not recommended for production)"
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Datadog MCP HTTP Server (with SSE Streaming)         ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🌐 Server: http://localhost:{port}
    📚 API Docs: http://localhost:{port}/docs
    {auth_status}
    
    📡 Endpoints:
       GET  /health                    - Health check (no auth)
       GET  /tools                     - List available tools
       
       GET  /query_metrics             - Query metrics (JSON response)
       GET  /query_metrics/stream      - Query metrics (SSE streaming)
       
       GET  /search_metrics            - Search metrics (JSON response)
       GET  /search_metrics/stream     - Search metrics (SSE streaming)
       
       GET  /get_metric_tags           - Get metric tags (JSON response)
       GET  /get_metric_tags/stream    - Get metric tags (SSE streaming)
       
       GET  /generate_metric_chart     - Generate chart image (PNG/base64)
       
       POST /call                      - Call any tool (JSON response)
       POST /call/stream               - Call any tool (SSE streaming)
    
    🔑 Required Environment:
       DD_API_KEY=your-api-key
       DD_APP_KEY=your-app-key
    
    🔐 Optional Authorization:
       MCP_AUTH_TOKEN=your-secret-token
       (If set, requires: Authorization: Bearer your-secret-token)
    
    """)
    
    uvicorn.run(
        "src.http_server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
