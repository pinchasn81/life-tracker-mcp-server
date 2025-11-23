# 🚀 Quick Debug Start - PyCharm

## ⚡ 3-Minute Setup

### 1. Create .env File

```bash
cd /Users/nirpinchas/Projects/LifeTracker/mcp-server
cat > .env << 'EOF'
AWS_REGION=eu-central-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
TABLE_PREFIX=your_table_prefix_here
EOF
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Find Python Path

```bash
uv run which python
# Copy the output - you'll need it for PyCharm
```

### 4. Configure PyCharm

1. **PyCharm → Preferences → Python Interpreter**
2. Click ⚙️ → **Add → Existing environment**
3. Paste the path from step 3
4. Click **OK**

### 5. Create Debug Configuration

1. **Run → Edit Configurations → +** → **Python**
2. **Name:** `Debug MCP`
3. **Script:** Browse to `debug_server.py`
4. **Working directory:** `/Users/nirpinchas/Projects/LifeTracker/mcp-server`
5. Click **OK**

(Environment variables will be loaded from .env automatically!)

### 6. Start Debugging! 🐛

**Easiest way:**
1. Open `test_debug.py` in PyCharm
2. Right-click anywhere in the file
3. Select **Debug 'test_debug'**
4. Set breakpoints in `main.py` and they'll be hit!

**Or use the configuration:**
1. Set breakpoint in `main.py` (try line 90 in `create_activity_log`)
2. Select **Debug MCP** from dropdown
3. Click Debug button 🐛
4. Breakpoint will be hit when tools are called

## 📝 Files I Created for You

| File | Purpose |
|------|---------|
| `debug_server.py` | Run the MCP server with debugging support |
| `test_debug.py` | Test individual functions with breakpoints |
| `find_tables.py` | Verify your DynamoDB table names |
| `PYCHARM_SETUP.md` | Detailed PyCharm setup guide |
| `DEBUGGING.md` | Complete debugging reference |

## 🎯 Quick Tests

### Test 1: Connection

```bash
uv run python test_debug.py
# Choose option 0
```

Should show:
```
✅ ActivityLog → ActivityLog-your-table-prefix-here
✅ UserProfile → UserProfile-your-table-prefix-here
...
```

### Test 2: Find Tables

```bash
uv run python find_tables.py
```

Verifies your actual DynamoDB tables.

### Test 3: MCP Inspector

```bash
uv run mcp dev main.py
```

Opens web interface to test all tools.

## 🐛 Debug Workflow

**Method 1: Test Individual Functions (Recommended for learning)**

1. Open `main.py`
2. Find the function you want to debug (e.g., `create_activity_log`)
3. Click in left gutter to set breakpoint (red dot appears)
4. Right-click `test_debug.py` → **Debug 'test_debug'**
5. Choose which test to run
6. Your breakpoint will be hit! 
7. Use debugger:
   - **F8** to step through code
   - **Alt+F8** to evaluate expressions
   - Hover over variables to see values
   - Check **Variables** panel for all data

**Method 2: Debug Full MCP Server**

1. Set breakpoints in `main.py`
2. Run **Debug MCP** configuration
3. In another terminal: `uv run mcp dev-client`
4. Call tools through the client
5. Breakpoints hit when tools are executed

## 💡 Common Debugging Tasks

### See What Table Name Is Being Used

Breakpoint in `get_table()` function (line ~38):
```python
full_table_name = f"{table_name}-{TABLE_PREFIX}" if TABLE_PREFIX else table_name
# When stopped here, check full_table_name in debugger
```

### Debug JSON Data

Breakpoint where JSON is created:
```python
item["processedData"] = json.dumps(processed_data)
# Use Alt+F8 and try: json.loads(item["processedData"])
```

### Check AWS Connection

In debugger console (when stopped at any breakpoint):
```python
import boto3
client = boto3.client('dynamodb', region_name='eu-central-1')
print(client.list_tables()['TableNames'])
```

## 🎓 Learning the Debugger

Set a breakpoint in `create_activity_log()` and run `test_debug.py`:

**Things to try when stopped:**

1. **Variables Panel** - See all local variables
2. **Watches** - Add: `table._table_name`, `owner`, `activity_type`
3. **Console** - Type: `print(item)` to see what will be saved
4. **Evaluate** (Alt+F8) - Try: `json.dumps(item, indent=2)`
5. **Step Over** (F8) - Execute one line at a time
6. **Step Into** (F7) - Go into `table.put_item()`

## ⚠️ Troubleshooting

**"Module not found" errors:**
- Make sure PyCharm is using the uv Python interpreter
- File → Invalidate Caches → Invalidate and Restart

**Breakpoints not stopping:**
- Click 🐛 Debug button, not ▶️ Run
- Check breakpoint is red, not grey
- Try right-clicking file → Debug directly

**"Table not found":**
- Check `.env` file exists and has TABLE_PREFIX
- Run `find_tables.py` to verify table names
- Set breakpoint in `get_table()` to see constructed name

**Environment variables not loading:**
- Make sure `.env` file is in `/Users/nirpinchas/Projects/LifeTracker/mcp-server/`
- Check the file isn't called `.env.example` or `.env.txt`
- Restart PyCharm after creating `.env`

## 📚 Next Steps

1. ✅ Create `.env` file (step 1 above)
2. ✅ Run `test_debug.py` to verify connection
3. ✅ Set a breakpoint and debug!
4. 📖 Read `PYCHARM_SETUP.md` for advanced features
5. 📖 Read `DEBUGGING.md` for all debugging techniques

## 🎉 You're Ready!

Try this right now:
```bash
cd /Users/nirpinchas/Projects/LifeTracker/mcp-server

# Install deps
uv sync

# Test connection
uv run python test_debug.py
```

Then in PyCharm:
1. Open `main.py`
2. Click line 90 (in `create_activity_log`) to set breakpoint
3. Right-click `test_debug.py` → **Debug 'test_debug'**
4. Choose option 1
5. 🎯 Breakpoint hit!

---

**Questions?** Check the other guides:
- `PYCHARM_SETUP.md` - Detailed PyCharm configuration
- `DEBUGGING.md` - All debugging techniques
- `README.md` - Full MCP server documentation

