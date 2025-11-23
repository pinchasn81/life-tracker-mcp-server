# PyCharm Debugging Setup - Quick Start

Follow these steps to set up debugging in PyCharm for your MCP server.

## 🚀 Quick Start (5 minutes)

### Step 1: Install Dependencies

Open terminal and run:
```bash
cd /Users/nirpinchas/Projects/LifeTracker/mcp-server
uv sync
```

### Step 2: Find Your Python Interpreter

Run this command and copy the output:
```bash
uv run which python
```

You'll get something like:
```
/Users/nirpinchas/.local/share/uv/python/cpython-3.12.x/bin/python
```

### Step 3: Configure PyCharm Python Interpreter

1. Open PyCharm
2. Go to **PyCharm → Preferences** (or **Cmd+,**)
3. Navigate to **Project: mcp-server → Python Interpreter**
4. Click the ⚙️ gear icon → **Add...**
5. Select **Existing environment**
6. Click the **...** button and paste the path from Step 2
7. Click **OK** → **OK**

### Step 4: Import Run Configurations

I've created pre-configured run configurations for you:

1. In PyCharm, go to **Run → Edit Configurations...**
2. Click the **folder icon** 📁 (top left, near the + button)
3. Navigate to: `/Users/nirpinchas/Projects/LifeTracker/mcp-server/.idea_runConfigurations/`
4. Select both XML files:
   - `MCP_Server_Debug.xml`
   - `Test_Debug.xml`
5. Click **Open**

If that doesn't work, manually create them:

#### Configuration 1: MCP Server (Debug)

- **Name:** MCP Server (Debug)
- **Script path:** `/Users/nirpinchas/Projects/LifeTracker/mcp-server/debug_server.py`
- **Working directory:** `/Users/nirpinchas/Projects/LifeTracker/mcp-server`
- **Environment variables:**
  ```
  AWS_REGION=eu-central-1
  AWS_ACCESS_KEY_ID=your_access_key_here
  AWS_SECRET_ACCESS_KEY=your_secret_key_here
  TABLE_PREFIX=your_table_prefix_here
  PYTHONUNBUFFERED=1
  ```

#### Configuration 2: Test Debug

- **Name:** Test Debug
- **Script path:** `/Users/nirpinchas/Projects/LifeTracker/mcp-server/test_debug.py`
- **Working directory:** `/Users/nirpinchas/Projects/LifeTracker/mcp-server`
- **Environment variables:** (same as above)
- **Emulate terminal:** ✅ (check this box)

### Step 5: Start Debugging!

#### Option A: Debug the Full MCP Server

1. Open `main.py`
2. Set a breakpoint in any function (click left gutter)
   - Try line 90 in `create_activity_log()`
3. Select **MCP Server (Debug)** from the run configuration dropdown
4. Click the **Debug** button (🐛)
5. Server starts and shows: "Starting MCP server in debug mode..."
6. Open another terminal and run: `uv run mcp dev-client`
7. Call a tool, and your breakpoint will be hit!

#### Option B: Debug Individual Functions (Easier)

1. Open `main.py`
2. Set a breakpoint in `create_activity_log()` (around line 90)
3. Select **Test Debug** from the run configuration dropdown
4. Click the **Debug** button (🐛)
5. Choose option 1 (Activity Logs) when prompted
6. Your breakpoint will be hit immediately!
7. Use PyCharm's debugger to:
   - Step through code (F8)
   - Step into functions (F7)
   - Evaluate expressions (Alt+F8)
   - View variables in the Variables panel

## 🎯 Common Debugging Scenarios

### Scenario 1: Debug Creating an Activity Log

```python
# In test_debug.py or your own test, set breakpoint in main.py line ~90
def create_activity_log(...):
    try:
        table = get_table("ActivityLog")
        logger.info(f"Creating new activity log entry for {activity_type}")  # <- Breakpoint here
        ...
```

### Scenario 2: Debug DynamoDB Table Name Issues

```python
# Set breakpoint in get_table() function (line ~35)
def get_table(table_name: str):
    """Get DynamoDB table reference with proper naming."""
    full_table_name = f"{table_name}-{TABLE_PREFIX}" if TABLE_PREFIX else table_name  # <- Breakpoint here
    return dynamodb.Table(full_table_name)
```

When stopped, check in the debugger:
- `table_name` - should be like "ActivityLog"
- `TABLE_PREFIX` - should be "your-table-prefix-here"
- `full_table_name` - should be "ActivityLog-your-table-prefix-here"

### Scenario 3: Debug JSON Parsing

```python
# Set breakpoint where processed_data is used
if processed_data:
    item["processedData"] = json.dumps(processed_data)  # <- Breakpoint here
```

Use **Evaluate Expression** (Alt+F8) to test:
```python
json.dumps(processed_data)
type(processed_data)
```

## 🔧 Debugging Tools in PyCharm

### 1. Debugger Console

While paused at a breakpoint, click the **Console** tab. You can run any Python code:

```python
# Check environment
import os
print(os.getenv("TABLE_PREFIX"))

# Test table connection
table = get_table("ActivityLog")
print(table.table_name)

# Check AWS credentials
import boto3
client = boto3.client('dynamodb', region_name='eu-central-1')
print(client.list_tables())
```

### 2. Watches

Add expressions to watch in the **Watches** panel:
- `table._table_name` - see the actual DynamoDB table name
- `len(items)` - count items returned
- `json.dumps(item)` - see formatted JSON
- `os.getenv("TABLE_PREFIX")` - check environment

### 3. Conditional Breakpoints

Right-click a breakpoint → **Edit Breakpoint** → add condition:
```python
activity_type == "food"
owner == "debug@example.com"
len(items) > 0
```

### 4. Step Through Code

- **F8** - Step Over (execute current line)
- **F7** - Step Into (go into function calls)
- **Shift+F8** - Step Out (return from function)
- **Alt+F9** - Run to Cursor
- **F9** - Resume (run to next breakpoint)

## 🐛 Troubleshooting

### "Module 'main' has no attribute 'mcp'"

**Cause:** PyCharm is using the wrong Python interpreter.

**Fix:**
1. Make sure you set the interpreter from `uv run which python`
2. File → Invalidate Caches → Invalidate and Restart

### Breakpoints are grey and not stopping

**Cause:** You're running in Run mode, not Debug mode.

**Fix:** Click the 🐛 Debug button, not the ▶️ Run button.

### "Table not found" in debugger

**Cause:** Environment variables not loaded or wrong table name.

**Fix:** 
1. Check run configuration has env vars set
2. In debugger console, run: `print(os.getenv("TABLE_PREFIX"))`
3. Set breakpoint in `get_table()` to see the constructed table name

### Can't see variables

**Cause:** Variables panel is hidden.

**Fix:** View → Tool Windows → Debug → Variables tab should be visible.

## 📚 Next Steps

1. **Read the full debugging guide:** `DEBUGGING.md`
2. **Test table connection:** Run `test_debug.py` first
3. **Check actual table names:** Run `find_tables.py`
4. **Try the MCP Inspector:** `uv run mcp dev main.py`

## 💡 Pro Tips

1. **Use logging over print statements:**
   ```python
   logger.debug(f"Processing: {activity_type}")  # Better
   print(f"Processing: {activity_type}")         # Avoid
   ```

2. **Add docstring examples in your breakpoints:**
   When stopped, try the code from the docstring to verify it works.

3. **Use PyCharm's "Evaluate and Log" breakpoint action:**
   Right-click breakpoint → More → Check "Evaluate and log"
   Add: `f"Activity type: {activity_type}, Owner: {owner}"`
   This logs without stopping!

4. **Debug configuration templates:**
   Once you have a working config, right-click it → **Save as Template**
   Now new Python files can use it easily.

## ✅ Verification

To verify everything is working:

1. Run **Test Debug** configuration
2. Choose option "0" (Just test connection)
3. You should see:
   ```
   ✅ ActivityLog → ActivityLog-your-table-prefix-here
   ✅ UserProfile → UserProfile-your-table-prefix-here
   ✅ MemoryEntry → MemoryEntry-your-table-prefix-here
   ✅ QuickAction → QuickAction-your-table-prefix-here
   ```

If you see this, you're ready to debug! 🎉

