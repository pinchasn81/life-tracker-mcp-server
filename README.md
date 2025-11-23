# LifeTracker MCP Server

MCP server for LifeTracker DynamoDB integration.

## Files

- `main.py` - FastMCP server for local development
- `server.py` - Base MCP Server for HTTP deployment (alternative)
- `fastmcp.json` - Deployment configuration

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

