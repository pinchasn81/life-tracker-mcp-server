#!/bin/bash
# Setup script for LifeTracker MCP Server

echo "🚀 Setting up LifeTracker MCP Server..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# AWS Configuration
AWS_REGION=eu-central-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# DynamoDB Table Configuration
# For Amplify-managed tables, use the format: TableName-{AppSyncApiId}-{env}
# Example: UserProfile-abc123xyz-staging
# Leave empty if using exact table names
TABLE_PREFIX=your_table_prefix_here

# For production deployment, you can omit AWS credentials if using IAM roles
EOF
    echo "✅ .env file created. Please edit it with your AWS credentials."
else
    echo "ℹ️  .env file already exists."
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your AWS credentials"
echo "2. Set the TABLE_PREFIX or ensure table names match your DynamoDB tables"
echo "3. Test the server: uv run mcp dev main.py"
echo ""
echo "For more information, see README.md"

