# PyCharm Debugging - Simple Guide

There are 3 ways to debug your MCP server. **Method 1 is the easiest.**

---

## ⭐ Method 1: Debug Individual Functions (EASIEST)

This is the **recommended** way because it's simple and you get full debugging power.

### How it works:
- Use `test_debug.py` to call your MCP functions directly
- Set breakpoints in `main.py`
- Debug without needing the full MCP server running

### Steps:

1. **Open `main.py` and set a breakpoint**
   - Line 93: inside `create_activity_log()` function
   - Click in the left gutter (grey area) next to the line number
   - A red dot appears ⭕

2. **Right-click `test_debug.py`**
   - Select **"Debug 'test_debug'"**

3. **Choose a test option**
   - Type `1` and press Enter (for Activity Logs)

4. **Your breakpoint will be hit!** 🎯
   - Variables panel shows all values
   - Press **F8** to step through code
   - Press **Alt+F8** to evaluate expressions

### Screenshot of what you should see:
```
Debugger stopped at: main.py line 93
Variables:
  - activity_type: "food"
  - raw_input: "Debugging: ate a sandwich..."
  - table: DynamoDB.Table(...)
```

**✅ Pros:**
- Simple and fast
- Full debugging control
- No server setup needed
- Perfect for testing individual tools

**❌ Cons:**
- Doesn't use the MCP Inspector web interface

---

## Method 2: Debug MCP Server with Inspector (Advanced)

This lets you debug while using the actual MCP Inspector web interface.

### The Challenge:
The MCP Inspector is launched by the `mcp` CLI command, which makes debugging tricky in PyCharm.

### Best Workaround:

**Step 1: Run server in terminal with debug support**

Add this to the **very end** of your `main.py` file:

```python
# At the very end of main.py, before if __name__ == "__main__":
import sys

# If running in debug mode, add trace hook
if sys.gettrace() is not None:
    print("🐛 Debug mode detected!")
```

**Step 2: Run from PyCharm terminal**

1. Open PyCharm **Terminal** tab (bottom of screen)
2. Run:
   ```bash
   uv run mcp dev main.py
   ```
3. MCP Inspector opens in browser

**Step 3: Set breakpoints**

1. Set breakpoints in `main.py`
2. Call tools from the Inspector
3. Breakpoints **might not hit** (limitation of this approach)

### Why this is hard:

When you run `uv run mcp dev main.py` from the terminal, PyCharm doesn't control the process, so breakpoints won't work.

**Solution:** Use **Method 3** if you need MCP Inspector + debugging.

---

## Method 3: Debug with PyCharm Run Configuration

This gives you both debugging AND a running server, but without the web UI.

### Steps:

**Step 1: Create PyCharm Run Configuration**

1. **Run → Edit Configurations**
2. Click **+** → **Python**
3. Configure:
   - **Name:** `Debug MCP Server`
   - **Script path:** Browse to `main.py`
   - **Working directory:** `/Users/nirpinchas/Projects/LifeTracker/mcp-server`
   - **Environment variables:** (click folder icon 📁)
     ```
    AWS_REGION=eu-central-1
    AWS_ACCESS_KEY_ID=your_access_key_here
    AWS_SECRET_ACCESS_KEY=your_secret_key_here
    TABLE_PREFIX=your_table_prefix_here
     ```
4. Click **OK**

**Step 2: Set Breakpoints**

1. Open `main.py`
2. Set breakpoint in any tool function (e.g., line 93)

**Step 3: Debug**

1. Select **Debug MCP Server** from dropdown
2. Click Debug button (🐛)
3. Server starts in stdio mode

**Step 4: Connect a Client**

Open another terminal and run:
```bash
cd /Users/nirpinchas/Projects/LifeTracker/mcp-server
uv run mcp dev-client
```

Or use the test script to trigger your tools.

**✅ Pros:**
- Full debugging in PyCharm
- Breakpoints work perfectly
- Can step through code

**❌ Cons:**
- No automatic browser UI
- Need to use MCP client manually

---

## 🎯 My Recommendation

**For learning and testing: Use Method 1**

```bash
# In PyCharm:
1. Set breakpoint in main.py line 93
2. Right-click test_debug.py
3. Select "Debug 'test_debug'"
4. Choose option 1
5. Breakpoint hits immediately! 🎯
```

**For development: Combine approaches**

1. Use **Method 1** to debug logic and fix bugs
2. Use **Method 2** (terminal) to test with MCP Inspector
3. Use logging for production:
   ```python
   logger.info(f"Created activity: {item_id}")
   logger.debug(f"Full item: {json.dumps(item)}")
   ```

---

## 🔍 Quick Debugging Tips

### See Variables
When stopped at a breakpoint:
- **Variables panel** (bottom left) shows everything
- Hover over any variable to see its value
- Right-click variable → **Add to Watches**

### Execute Code
When stopped at a breakpoint:
- Press **Alt+F8** for "Evaluate Expression"
- Try:
  ```python
  print(json.dumps(item, indent=2))
  table.table_name
  os.getenv("TABLE_PREFIX")
  ```

### Step Through Code
- **F8** - Step Over (next line)
- **F7** - Step Into (enter function)
- **Shift+F8** - Step Out (exit function)
- **F9** - Resume (continue to next breakpoint)

### Console
When stopped, click **Console** tab:
```python
# Test anything:
import boto3
client = boto3.client('dynamodb', region_name='eu-central-1')
client.list_tables()
```

---

## 🐛 Troubleshooting

### "Waiting for debugger to attach..." and hangs

**Cause:** You added debugpy code (remote debugging)

**Fix:** Remove these lines from main.py:
```python
# REMOVE THESE:
import debugpy
debugpy.listen(5678)
print("🐛 Waiting for debugger to attach on port 5678...")
debugpy.wait_for_client()
print("✅ Debugger attached!")
```

✅ **Already fixed for you!**

### Breakpoints not hitting

**Cause 1:** Running in Run mode instead of Debug mode
- **Fix:** Click 🐛 Debug, not ▶️ Run

**Cause 2:** Breakpoint in code that doesn't execute
- **Fix:** Use test_debug.py which definitely calls the function

**Cause 3:** PyCharm not controlling the process
- **Fix:** Use Method 1 or Method 3

### "Module not found" errors

**Cause:** Wrong Python interpreter

**Fix:**
1. Find uv Python: `uv run which python`
2. PyCharm → Preferences → Python Interpreter
3. Add → Existing environment
4. Paste the path
5. Restart PyCharm

---

## ✅ Quick Start (Right Now!)

Try this in 30 seconds:

1. Open `main.py` in PyCharm
2. Click line 93 (left gutter) to set breakpoint
3. Right-click `test_debug.py` in project tree
4. Select **"Debug 'test_debug'"**
5. Type `1` and press Enter
6. 🎯 **Breakpoint hit!**

Now you can:
- See all variables
- Step through code with F8
- Evaluate expressions with Alt+F8
- Understand exactly what your code does

---

## 📚 Summary

| Method | Ease | Debugging | MCP Inspector | Best For |
|--------|------|-----------|---------------|----------|
| **Method 1: test_debug.py** | ⭐⭐⭐ | ✅ Full | ❌ No | **Learning & Testing** |
| Method 2: Terminal | ⭐ | ❌ Limited | ✅ Yes | Trying the UI |
| Method 3: Run Config | ⭐⭐ | ✅ Full | ❌ No | Development |

**Start with Method 1**, it's by far the easiest and most powerful for debugging! 🚀

