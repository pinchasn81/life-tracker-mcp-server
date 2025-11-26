# DynamoDB Global Secondary Index Setup

## Required GSI for Optimal Performance

The LifeTracker MCP server uses **Query** operations instead of Scan for better performance and strong consistency. To enable this, you need to create a Global Secondary Index (GSI) on the `user_name` attribute.

## Creating the GSI

### Option 1: AWS Console

1. Go to DynamoDB in AWS Console
2. Select your `ActivityLog` table (e.g., `ActivityLog-5vikfbruezha3mkjeftpwsivle-NONE`)
3. Click the **Indexes** tab
4. Click **Create index**
5. Configure the index:
   - **Partition key**: `user_name` (String)
   - **Sort key**: Leave empty OR use `timestamp` for time-based queries
   - **Index name**: `user_name-index`
   - **Projected attributes**: `All` (recommended for flexibility)
6. Click **Create index**

### Option 2: AWS CLI

```bash
aws dynamodb update-table \
    --table-name ActivityLog-YOUR-PREFIX-HERE \
    --attribute-definitions \
        AttributeName=user_name,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"user_name-index\",\"KeySchema\":[{\"AttributeName\":\"user_name\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"},\"ProvisionedThroughput\":{\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}}}]"
```

### Option 3: CloudFormation/Terraform

**CloudFormation:**
```yaml
GlobalSecondaryIndexes:
  - IndexName: user_name-index
    KeySchema:
      - AttributeName: user_name
        KeyType: HASH
    Projection:
      ProjectionType: ALL
    ProvisionedThroughput:
      ReadCapacityUnits: 5
      WriteCapacityUnits: 5
```

**Terraform:**
```hcl
global_secondary_index {
  name               = "user_name-index"
  hash_key           = "user_name"
  projection_type    = "ALL"
  read_capacity      = 5
  write_capacity     = 5
}
```

## Why This Improves Performance

### Without GSI (using Scan):
- ❌ Scans entire table (slow for large datasets)
- ❌ Eventually consistent by default
- ❌ Consumes more read capacity
- ❌ Can hit 1MB scan limits

### With GSI (using Query):
- ✅ Only reads items for specific user (fast)
- ✅ More consistent results
- ✅ Lower read capacity usage
- ✅ Better for large datasets

## Cost Implications

**GSI adds:**
- Storage cost for the index (duplicates data)
- Additional write capacity (writes go to both table and index)
- Additional read capacity for queries against the index

**But saves:**
- Much lower query costs (targeted reads vs full scans)
- Better user experience (faster, more consistent)

## If You Don't Have the GSI Yet

The code will still work but will fall back to Scan with `ConsistentRead=True`:
- Slower for large datasets
- Higher read capacity cost
- But guaranteed to see recent writes

## Verification

After creating the GSI, verify it's active:

```bash
aws dynamodb describe-table \
    --table-name ActivityLog-YOUR-PREFIX-HERE \
    --query 'Table.GlobalSecondaryIndexes[?IndexName==`user_name-index`]'
```

Should show status: `ACTIVE`

## Custom GSI Name

If your GSI has a different name, update `main.py`:

```python
# Line ~571 and ~713
IndexName="your-custom-gsi-name",  # Change this
```

