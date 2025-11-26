# LifeTracker MCP Server

MCP server for LifeTracker DynamoDB integration.

## Files

- `main.py` - FastMCP server with activity logging tools
- `fastmcp.json` - Deployment configuration
- `GSI_SETUP.md` - Guide for creating DynamoDB Global Secondary Index

## Prerequisites

### Required DynamoDB GSI

For optimal performance and consistency, create a Global Secondary Index on `user_name`:

**Index configuration:**
- Index name: `user_name-index`
- Partition key: `user_name` (String)
- Projection: ALL

See **[GSI_SETUP.md](./GSI_SETUP.md)** for detailed setup instructions.

**Note:** The server will work without the GSI but will fall back to slower Scan operations with `ConsistentRead=True`.

## Local Development

```bash
uv run mcp dev main.py
```

## Deployment Issue

⚠️ **Current Issue**: FastMCP cloud is throwing "Already running asyncio in this thread" errors.

This appears to be a compatibility issue between:
- FastMCP HTTP transport
- The cloud platform's event loop management

### Attempted Fixes

✅ Removed `mcp.run()` 
✅ Lazy DynamoDB initialization
✅ Removed Enum types
✅ Set both AWS_REGION and AWS_DEFAULT_REGION
✅ Created alternative `server.py` with base MCP Server

### Recommended Solutions

1. **Contact FastMCP Support** - This error comes from their platform (cli.py:533)
2. **Try Different Platform** - Deploy to:
   - AWS Lambda with API Gateway
   - Google Cloud Run
   - Docker container on any host
3. **Use Local/Claude Desktop** - Works perfectly with stdio transport

## Environment Variables

Required:
- `AWS_ACCESS_KEY_ID` 
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION` (use this, not just AWS_REGION)
- `TABLE_PREFIX` (optional)

## Tools

- `create_activity_log` - Log activities
- `get_activity_logs` - Fetch activity history

