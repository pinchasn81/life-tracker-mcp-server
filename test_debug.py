#!/usr/bin/env python3
"""
Test script for debugging individual MCP server functions.
Use this to test and debug functions without running the full MCP server.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your MCP functions
from main import (
    create_activity_log,
    get_activity_logs,
    get_user_profile,
    update_user_profile,
    create_memory_entry,
    get_memory_entries,
    create_quick_action,
    get_quick_actions,
    get_table
)


def print_result(title: str, result: str):
    """Pretty print a result."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    try:
        data = json.loads(result)
        print(json.dumps(data, indent=2))
    except:
        print(result)
    print()


def test_table_connection():
    """Test that we can connect to DynamoDB tables."""
    print("\n🔍 Testing DynamoDB Connection...")
    print(f"Region: {os.getenv('AWS_REGION')}")
    print(f"Table Prefix: {os.getenv('TABLE_PREFIX')}")
    
    tables_to_test = ["ActivityLog", "UserProfile", "MemoryEntry", "QuickAction"]
    
    for table_name in tables_to_test:
        try:
            table = get_table(table_name)
            print(f"✅ {table_name} → {table.table_name}")
        except Exception as e:
            print(f"❌ {table_name} → Error: {e}")
    
    print()


def test_activity_logs():
    """Test activity log operations."""
    test_owner = "debug@example.com"
    
    # Create a test activity log
    print_result(
        "Creating Activity Log",
        create_activity_log(
            activity_type="food",
            raw_input="Debugging: ate a sandwich with turkey and cheese",
            processed_data={
                "food_name": "Turkey Sandwich",
                "calories": 350,
                "protein": 25
            },
            owner=test_owner
        )
    )
    
    # Fetch activity logs
    print_result(
        "Fetching Activity Logs",
        get_activity_logs(
            owner=test_owner,
            limit=5
        )
    )


def test_user_profile():
    """Test user profile operations."""
    test_owner = "debug@example.com"
    
    # Update/create profile
    print_result(
        "Updating User Profile",
        update_user_profile(
            owner=test_owner,
            email=test_owner,
            gender="male",
            weight=75.0,
            height=180.0,
            activity_level="moderate",
            health_goals="Maintain weight and build muscle"
        )
    )
    
    # Fetch profile
    print_result(
        "Fetching User Profile",
        get_user_profile(owner=test_owner)
    )


def test_memory_entries():
    """Test memory entry operations."""
    test_owner = "debug@example.com"
    
    # Create a memory entry
    print_result(
        "Creating Memory Entry",
        create_memory_entry(
            entry_type="food",
            name="Greek Yogurt",
            data={
                "calories": 100,
                "protein": 10,
                "carbs": 6,
                "fat": 0,
                "serving_size": "170g"
            },
            owner=test_owner
        )
    )
    
    # Fetch memory entries
    print_result(
        "Fetching Memory Entries",
        get_memory_entries(
            owner=test_owner,
            entry_type="food"
        )
    )


def test_quick_actions():
    """Test quick action operations."""
    test_owner = "debug@example.com"
    
    # Create a quick action
    print_result(
        "Creating Quick Action",
        create_quick_action(
            category="DRINK",
            label="Water",
            icon="💧",
            data={
                "amount": 250,
                "unit": "ml"
            },
            order=1,
            owner=test_owner
        )
    )
    
    # Fetch quick actions
    print_result(
        "Fetching Quick Actions",
        get_quick_actions(
            owner=test_owner,
            category="DRINK"
        )
    )


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 MCP Server Debug Test Suite")
    print("="*60)
    
    # Test connection first
    test_table_connection()
    
    # Ask user what to test
    print("\nWhat would you like to test?")
    print("1. Activity Logs")
    print("2. User Profile")
    print("3. Memory Entries")
    print("4. Quick Actions")
    print("5. All of the above")
    print("0. Just test connection (already done)")
    
    choice = input("\nEnter choice (1-5, or 0 to exit): ").strip()
    
    if choice == "1":
        test_activity_logs()
    elif choice == "2":
        test_user_profile()
    elif choice == "3":
        test_memory_entries()
    elif choice == "4":
        test_quick_actions()
    elif choice == "5":
        print("\n🏃 Running all tests...\n")
        test_activity_logs()
        test_user_profile()
        test_memory_entries()
        test_quick_actions()
    elif choice == "0":
        print("\n✅ Connection test complete!")
    else:
        print("\n❌ Invalid choice")
    
    print("\n" + "="*60)
    print("✅ Debug session complete!")
    print("="*60 + "\n")
    
    print("💡 Debugging tips:")
    print("   - Set breakpoints in main.py before running this script")
    print("   - Right-click this file and select 'Debug test_debug'")
    print("   - Use PyCharm's debugger to step through code")
    print("   - Check variables in the Variables panel")
    print()


if __name__ == "__main__":
    main()

