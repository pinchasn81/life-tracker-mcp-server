"""
HTTP entrypoint for cloud deployment using base MCP Server.
"""
import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Optional, Any, Dict

# Don't load dotenv in cloud
import boto3
from boto3.dynamodb.conditions import Key, Attr
from mcp.server import Server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "eu-central-1"
TABLE_PREFIX = os.getenv("TABLE_PREFIX", "")

# Lazy DynamoDB initialization
_dynamodb = None

def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        logger.info(f"Initializing DynamoDB with region: {AWS_REGION}")
        _dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    return _dynamodb

def get_table(table_name: str):
    full_table_name = f"{table_name}-{TABLE_PREFIX}" if TABLE_PREFIX else table_name
    return get_dynamodb().Table(full_table_name)

# Create MCP server
mcp = Server("LifeTracker")

@mcp.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_activity_log",
            description="Create a new activity log entry in DynamoDB",
            inputSchema={
                "type": "object",
                "properties": {
                    "activity_type": {
                        "type": "string",
                        "description": "Type of activity: food, drink, exercise, supplement, sleep, smoking, stomach"
                    },
                    "raw_input": {
                        "type": "string",
                        "description": "Original text input from user"
                    },
                    "owner": {
                        "type": "string",
                        "description": "User ID/email"
                    }
                },
                "required": ["activity_type", "raw_input"]
            }
        ),
        Tool(
            name="get_activity_logs",
            description="Fetch activity logs from DynamoDB",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Filter by owner/user ID"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum items to return (default: 50)"
                    }
                }
            }
        )
    ]

@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "create_activity_log":
        result = await create_activity_log(**arguments)
        return [TextContent(type="text", text=result)]
    elif name == "get_activity_logs":
        result = await get_activity_logs(**arguments)
        return [TextContent(type="text", text=result)]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def create_activity_log(
    activity_type: str,
    raw_input: str,
    owner: Optional[str] = None
) -> str:
    try:
        table = get_table("ActivityLog")
        item_id = f"activity-{datetime.utcnow().timestamp()}"
        now = datetime.utcnow().isoformat() + "Z"
        
        item = {
            "id": item_id,
            "timestamp": now,
            "activityType": activity_type,
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        if owner:
            item["owner"] = owner
            
        table.put_item(Item=item)
        
        return json.dumps({
            "success": True,
            "message": "Activity log created",
            "data": item
        }, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)

async def get_activity_logs(
    owner: Optional[str] = None,
    limit: int = 50
) -> str:
    try:
        table = get_table("ActivityLog")
        scan_kwargs = {"Limit": limit}
        
        if owner:
            scan_kwargs["FilterExpression"] = Attr("owner").eq(owner)
        
        response = table.scan(**scan_kwargs)
        items = response.get("Items", [])
        
        return json.dumps({
            "success": True,
            "count": len(items),
            "data": items
        }, indent=2, default=str)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)
