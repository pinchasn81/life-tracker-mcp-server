# Deployment Guide

## Deploying to FastMCP Cloud

This guide explains how to deploy your LifeTracker MCP server to FastMCP cloud.

### Prerequisites

1. Install FastMCP CLI:
   ```bash
   pip install fastmcp
   ```

2. Authenticate with FastMCP:
   ```bash
   fastmcp auth login
   ```

### Configuration

The `fastmcp.json` file is already configured for deployment. It includes:

- **AWS_REGION**: Set to `eu-central-1` (modify if needed)
- **AWS_ACCESS_KEY_ID**: Will use `${AWS_ACCESS_KEY_ID}` from environment
- **AWS_SECRET_ACCESS_KEY**: Will use `${AWS_SECRET_ACCESS_KEY}` from environment
- **TABLE_PREFIX**: Will use `${TABLE_PREFIX}` from environment

### Setting Environment Variables

Before deploying, you need to set your AWS credentials and table prefix in the FastMCP environment.

#### Option 1: Using FastMCP CLI

```bash
# Set AWS credentials
fastmcp env set AWS_ACCESS_KEY_ID your_access_key_here
fastmcp env set AWS_SECRET_ACCESS_KEY your_secret_key_here
fastmcp env set TABLE_PREFIX your_table_prefix_here

# Verify they're set
fastmcp env list
```

#### Option 2: Using FastMCP Dashboard

1. Go to https://gofastmcp.com/dashboard
2. Navigate to your project
3. Click on "Environment Variables"
4. Add:
   - `AWS_ACCESS_KEY_ID` = your actual access key
   - `AWS_SECRET_ACCESS_KEY` = your actual secret key
   - `TABLE_PREFIX` = your table prefix (e.g., `5vikfbruezha3mkjeftpwsivle-NONE`)

### Deploy

Once environment variables are set:

```bash
# From your project directory
fastmcp deploy

# Or specify the config file explicitly
fastmcp deploy --config fastmcp.json
```

### Testing the Deployment

After deployment, FastMCP will provide you with an endpoint URL. Test it:

```bash
# Get your deployment URL
fastmcp deployments list

# Test the endpoint
curl -X POST https://your-deployment-url.fastmcp.com/tools/create_activity_log \
  -H "Content-Type: application/json" \
  -d '{
    "activity_type": "food",
    "raw_input": "Had breakfast",
    "owner": "test@example.com"
  }'
```

### Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `AWS_REGION` | Yes | AWS region for DynamoDB | `eu-central-1` |
| `AWS_ACCESS_KEY_ID` | Yes | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Yes | AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `TABLE_PREFIX` | No | Prefix for DynamoDB tables | `5vikfbruezha3mkjeftpwsivle-NONE` |

**Note:** If `TABLE_PREFIX` is not set, the code will look for tables without a prefix (e.g., just `ActivityLog` instead of `ActivityLog-5vikfbruezha3mkjeftpwsivle-NONE`).

### Security Best Practices

1. **Never commit credentials**: The `fastmcp.json` uses `${VAR}` syntax to pull from environment, not hardcoded values
2. **Use IAM roles** (recommended): For production, use AWS IAM roles instead of access keys
3. **Rotate keys regularly**: Change your AWS credentials periodically
4. **Minimal permissions**: Grant only the necessary DynamoDB permissions

### Updating the Deployment

To update after code changes:

```bash
# Pull latest changes
git pull

# Redeploy
fastmcp deploy
```

### Monitoring and Logs

View logs from your deployment:

```bash
fastmcp logs --follow
```

### Troubleshooting

#### "Table not found" errors

- Verify your `TABLE_PREFIX` is correct
- Check that your AWS credentials have DynamoDB read/write permissions
- Verify the region matches where your tables are

#### "Access Denied" errors

Your AWS credentials need these permissions:
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
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:eu-central-1:*:table/ActivityLog*",
        "arn:aws:dynamodb:eu-central-1:*:table/UserProfile*",
        "arn:aws:dynamodb:eu-central-1:*:table/MemoryEntry*",
        "arn:aws:dynamodb:eu-central-1:*:table/QuickAction*"
      ]
    }
  ]
}
```

### Alternative: Deploy with Docker

If you prefer Docker deployment:

```bash
# Build the image
docker build -t lifetracker-mcp .

# Run with environment variables
docker run -e AWS_ACCESS_KEY_ID=your_key \
           -e AWS_SECRET_ACCESS_KEY=your_secret \
           -e AWS_REGION=eu-central-1 \
           -e TABLE_PREFIX=your_prefix \
           -p 8000:8000 \
           lifetracker-mcp
```

### Support

- FastMCP Docs: https://docs.gofastmcp.com
- GitHub Issues: https://github.com/pinchasn81/life-tracker-mcp-server/issues

