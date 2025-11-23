# LifeTracker MCP Server

A Model Context Protocol (MCP) server that provides tools and resources for interacting with LifeTracker's DynamoDB tables. This server enables AI assistants (like Claude) to read and write activity logs, user profiles, memory entries, and quick actions.

## Features

### Tools (Actions)

The server exposes the following tools that can be called by MCP clients:

#### Activity Logs
- **`create_activity_log`** - Create a new activity log entry (food, drink, exercise, etc.)
- **`get_activity_logs`** - Fetch activity logs with optional filters (owner, type, date range)

#### User Profile
- **`get_user_profile`** - Fetch user profile by owner ID
- **`update_user_profile`** - Create or update user profile with health information

#### Memory Entries
- **`create_memory_entry`** - Save a new memory entry (saved foods, exercises, etc.)
- **`get_memory_entries`** - Fetch memory entries with filters

#### Quick Actions
- **`create_quick_action`** - Create a new quick action button
- **`get_quick_actions`** - Fetch quick actions by category

### Resources (Context for LLMs)

- **`profile://{owner}`** - User profile data for context
- **`recent-activities://{owner}`** - Recent activity logs for context

## Installation

1. **Install dependencies:**
   ```bash
   cd mcp-server
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and settings
   ```

3. **Set up AWS credentials:**
   
   For local development, add your AWS credentials to `.env`:
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=eu-central-1
   ```

   For production (running in AWS), the server will automatically use IAM roles.

## Configuration

### DynamoDB Table Names

The server needs to know your DynamoDB table names. Amplify creates tables with the following naming pattern:
```
{ModelName}-{AppSyncApiId}-{Environment}
```

For example:
- `ActivityLog-abc123xyz-staging`
- `UserProfile-abc123xyz-staging`

You have two options:

1. **Use TABLE_PREFIX** (recommended for Amplify tables):
   ```
   TABLE_PREFIX=ActivityLog-abc123xyz-staging
   ```
   The server will append the model name to this prefix.

2. **Use exact table names** (if you know them):
   Leave `TABLE_PREFIX` empty and ensure your table names match the model names exactly.

### Finding Your Table Names

You can find your actual DynamoDB table names by:

1. **AWS Console:**
   - Go to DynamoDB in AWS Console
   - Look at your table list

2. **AWS CLI:**
   ```bash
   aws dynamodb list-tables --region eu-central-1
   ```

3. **From Amplify outputs:**
   Check your `amplify_outputs.json` for the AppSync API ID, then construct the table names.

## Deployment

### Cloud Deployment (FastMCP)

Deploy to FastMCP cloud for serverless, always-available access:

```bash
# Install FastMCP CLI
pip install fastmcp

# Authenticate
fastmcp auth login

# Set environment variables
fastmcp env set AWS_ACCESS_KEY_ID your_key
fastmcp env set AWS_SECRET_ACCESS_KEY your_secret
fastmcp env set TABLE_PREFIX your_prefix

# Deploy
fastmcp deploy
```

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for detailed deployment instructions.

## Usage

### Running the Server

#### Development Mode with MCP Inspector
```bash
cd mcp-server
uv run mcp dev main.py
```

This opens an interactive inspector where you can test all the tools.

#### Direct Execution
```bash
cd mcp-server
uv run main.py
```

#### Install in Claude Desktop

1. Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "lifetracker": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/nirpinchas/Projects/LifeTracker/mcp-server",
        "run",
        "main.py"
      ],
      "env": {
        "AWS_REGION": "eu-central-1",
        "AWS_ACCESS_KEY_ID": "your_key",
        "AWS_SECRET_ACCESS_KEY": "your_secret"
      }
    }
  }
}
```

2. Restart Claude Desktop
3. You should see the LifeTracker server connected

### Example Interactions

Once connected to Claude or another MCP client, you can:

**Log an activity:**
```
"I just ate a greek yogurt with honey"
```
Claude can use `create_activity_log` to log this.

**Check your profile:**
```
"Show me my health profile"
```
Claude can use `get_user_profile` to fetch your data.

**Find saved foods:**
```
"What foods do I have saved in my memory?"
```
Claude can use `get_memory_entries` with `entry_type="food"`.

**View recent activities:**
```
"What have I eaten today?"
```
Claude can use `get_activity_logs` with date filters.

## Testing

### Using MCP Inspector

The MCP Inspector is the easiest way to test your server:

```bash
uv run mcp dev main.py
```

This provides a web interface where you can:
- See all available tools
- Call tools with sample data
- View responses
- Test resources

### Using Python Client

You can also write a Python client to test:

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def test_server():
    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(tools)
            
            # Call a tool
            result = await session.call_tool(
                "get_activity_logs",
                {"owner": "test@example.com", "limit": 10}
            )
            print(result)
```

## AWS IAM Permissions

For production deployment, ensure your IAM role/user has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:eu-central-1:*:table/ActivityLog-*",
        "arn:aws:dynamodb:eu-central-1:*:table/UserProfile-*",
        "arn:aws:dynamodb:eu-central-1:*:table/MemoryEntry-*",
        "arn:aws:dynamodb:eu-central-1:*:table/QuickAction-*"
      ]
    }
  ]
}
```

## Architecture

```
┌─────────────────┐
│  Claude/Client  │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────┐
│  FastMCP Server │
│  (main.py)      │
└────────┬────────┘
         │ boto3
         │
┌────────▼────────┐
│   DynamoDB      │
│   Tables        │
│  - ActivityLog  │
│  - UserProfile  │
│  - MemoryEntry  │
│  - QuickAction  │
└─────────────────┘
```

## Troubleshooting

### "Table not found" Error
- Check your `TABLE_PREFIX` in `.env`
- Verify table names exist in DynamoDB console
- Ensure AWS region is correct

### Authentication Errors
- Verify AWS credentials are set correctly
- Check IAM permissions
- For local testing, ensure credentials have DynamoDB access

### Connection Issues
- Ensure the server is running (`uv run mcp dev main.py`)
- Check Claude Desktop config is correct
- Look at Claude Desktop logs: `tail -f ~/Library/Logs/Claude/mcp*.log`

## Development

### Project Structure
```
mcp-server/
├── main.py           # Main MCP server implementation
├── pyproject.toml    # Dependencies and project config
├── .env.example      # Environment variables template
├── .env              # Your local configuration (gitignored)
└── README.md         # This file
```

### Adding New Tools

To add a new tool:

```python
@mcp.tool()
def my_new_tool(param1: str, param2: int) -> str:
    """
    Description of what the tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        JSON string with results
    """
    try:
        # Your implementation
        result = do_something(param1, param2)
        return json.dumps({"success": True, "data": result})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

### Adding Resources

```python
@mcp.resource("my-resource://{param}")
def get_my_resource(param: str) -> str:
    """Description of the resource."""
    # Fetch and return data
    return json.dumps({"data": "value"})
```

## Documentation

- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Guide](https://github.com/modelcontextprotocol/python-sdk#fastmcp)
- [boto3 DynamoDB Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html)

## License

Part of the LifeTracker project.

