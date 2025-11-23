# Debugging the MCP Server in PyCharm

This guide shows you how to debug your MCP server in PyCharm while it's running.

## Method 1: Using the Debug Wrapper (Recommended)

The easiest way to debug is to use the `debug_server.py` wrapper.

### Step 1: Configure PyCharm Run Configuration

1. Open PyCharm and go to **Run → Edit Configurations...**
2. Click the **+** button and select **Python**
3. Configure as follows:
   - **Name:** `MCP Server (Debug)`
   - **Script path:** Click the folder icon and select `debug_server.py`
   - **Working directory:** `/Users/nirpinchas/Projects/LifeTracker/mcp-server`
   - **Python interpreter:** Select your uv-managed Python interpreter (see below)
   - **Environment variables:** Click the folder icon and add:
     ```
    AWS_REGION=eu-central-1
    AWS_ACCESS_KEY_ID=your_access_key_here
    AWS_SECRET_ACCESS_KEY=your_secret_key_here
    TABLE_PREFIX=your_table_prefix_here
     ```
4. Click **OK**

### Step 2: Set Up the Python Interpreter

You need to tell PyCharm to use the Python environment that uv created:

1. Go to **PyCharm → Preferences → Project: mcp-server → Python Interpreter**
2. Click the gear icon ⚙️ → **Add...**
3. Select **Existing environment**
4. Find the uv Python path:
   ```bash
   # Run this in terminal to find the path:
   cd /Users/nirpinchas/Projects/LifeTracker/mcp-server
   uv run which python
   ```
5. Paste that path into PyCharm
6. Click **OK**

### Step 3: Set Breakpoints and Debug

1. Open `main.py` in PyCharm
2. Click in the left gutter next to any line to set a breakpoint
   - Try setting one in `create_activity_log()` function
3. Click the **Debug** button (🐛) in PyCharm toolbar
4. The server will start and wait at your breakpoints when tools are called

### Step 4: Test Your Server

While the debugger is running, open another terminal and use the MCP Inspector:

```bash
cd /Users/nirpinchas/Projects/LifeTracker/mcp-server
uv run mcp dev-client
```

Or use the `find_tables.py` script to test:

```bash
uv run python find_tables.py
```

## Method 2: Direct MCP Dev Command with Remote Debugging

If you want to use `mcp dev` command and attach the debugger:

### Step 1: Install debugpy

```bash
cd /Users/nirpinchas/Projects/LifeTracker/mcp-server
uv add debugpy
```

### Step 2: Modify main.py to Enable Remote Debugging

Add this at the top of `main.py` (after imports):

```python
# Enable remote debugging (remove in production)
import debugpy
debugpy.listen(5678)
print("🐛 Waiting for debugger to attach on port 5678...")
debugpy.wait_for_client()
print("✅ Debugger attached!")
```

### Step 3: Configure PyCharm Remote Debug

1. **Run → Edit Configurations...**
2. Click **+** → **Python Debug Server**
3. Configure:
   - **Name:** `MCP Remote Debug`
   - **Port:** `5678`
4. Click **OK**

### Step 4: Debug

1. Start the remote debug configuration in PyCharm (click Debug 🐛)
2. In terminal, run: `uv run mcp dev main.py`
3. The server will wait for PyCharm to attach
4. PyCharm will stop at your breakpoints

## Method 3: Using PyCharm Terminal with uv

You can also just use PyCharm's built-in terminal and run the MCP dev command directly:

1. Open the terminal in PyCharm (**View → Tool Windows → Terminal**)
2. Run:
   ```bash
   cd /Users/nirpinchas/Projects/LifeTracker/mcp-server
   uv run mcp dev main.py
   ```
3. While you can't set breakpoints, you can add `print()` statements or logging
4. Use `logger.info()`, `logger.debug()` for debugging output

## Debugging Tips

### 1. Use Logging Instead of Print

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# In your functions:
logger.debug(f"Input parameters: {activity_type}, {raw_input}")
logger.info(f"Created activity log with ID: {item_id}")
logger.error(f"Failed to create activity: {e}")
```

### 2. Set Conditional Breakpoints

In PyCharm, right-click a breakpoint and add a condition:
```python
activity_type == "food"
```

### 3. Evaluate Expressions

When stopped at a breakpoint, use PyCharm's **Evaluate Expression** (Alt+F8) to:
- Inspect variables
- Run test queries
- Check table names

### 4. Watch Variables

Add variables to the **Watches** panel:
- `table._table_name` - see actual DynamoDB table name
- `item` - see what's being written
- `response` - see DynamoDB responses

### 5. Debug DynamoDB Queries

Add this helper in your debug session:

```python
# In the debug console:
table = get_table("ActivityLog")
print(table.table_name)  # See actual table name
print(table.item_count)   # See how many items
```

## Common Issues

### Issue: "Module not found"

**Solution:** Make sure PyCharm is using the uv-managed Python interpreter:
```bash
# Find the path:
uv run which python

# Add to PyCharm:
PyCharm → Preferences → Python Interpreter → Add → Existing Environment
```

### Issue: "Table not found" 

**Solution:** Check your environment variables are loaded:
```python
# Add at top of debug session:
import os
print(os.getenv("TABLE_PREFIX"))
print(os.getenv("AWS_REGION"))
```

### Issue: Breakpoints not hitting

**Solution:** 
1. Make sure you're running in Debug mode (🐛) not Run mode (▶️)
2. Verify the breakpoint is in code that actually executes
3. Check the breakpoint is enabled (red dot, not grey)

## Testing Individual Functions

You can also create a test script to debug individual functions:

```python
# test_debug.py
import sys
import os
from dotenv import load_dotenv

load_dotenv()

from main import create_activity_log, get_activity_logs

# Test creating an activity
result = create_activity_log(
    activity_type="food",
    raw_input="Had a sandwich",
    owner="test@example.com"
)
print(result)

# Test fetching activities
result = get_activity_logs(owner="test@example.com", limit=5)
print(result)
```

Then debug this script instead:
1. Set breakpoints in `main.py` functions
2. Debug `test_debug.py`
3. Breakpoints will be hit when functions are called

## Quick Start

**Fastest way to start debugging:**

1. Open `main.py` in PyCharm
2. Right-click anywhere in the file
3. Select **Debug 'main'**
4. PyCharm will create a configuration and start debugging
5. Use another terminal for MCP Inspector: `uv run mcp dev-client`

## Environment Variables in PyCharm

Instead of setting them in the run configuration each time, you can:

1. **Use .env file** (already supported by python-dotenv):
   - PyCharm will automatically use `.env` in the project root
   - Make sure `load_dotenv()` is called in your code ✅ (already done)

2. **Set in PyCharm project settings:**
   - PyCharm → Preferences → Build, Execution, Deployment → Console → Python Console
   - Add environment variables there

## Resources

- [PyCharm Debugging Guide](https://www.jetbrains.com/help/pycharm/debugging-code.html)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [debugpy Documentation](https://github.com/microsoft/debugpy)

