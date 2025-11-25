"""
LifeTracker MCP Server

An MCP server that provides tools to interact with LifeTracker DynamoDB tables.
Supports reading and writing to ActivityLog, UserProfile, MemoryEntry, and QuickAction tables.
"""
import logging
import os
import json
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict, List, Annotated
from dotenv import load_dotenv

import boto3
from boto3.dynamodb.conditions import Key, Attr
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Load environment variables (only needed for local development with .env file)
# Cloud deployments provide env vars directly, so this is optional
try:
    load_dotenv()
except Exception:
    pass  # Ignore if .env doesn't exist or can't be loaded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("LifeTracker")

# AWS Configuration
# Boto3 looks for AWS_DEFAULT_REGION first, then AWS_REGION
AWS_REGION = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "eu-central-1"
TABLE_PREFIX = os.getenv("TABLE_PREFIX", "")  # e.g., "UserProfile-abc123-staging"

# Lazy initialization of DynamoDB to avoid asyncio conflicts
_dynamodb = None

def get_dynamodb():
    """Get or create DynamoDB resource (lazy initialization)."""
    global _dynamodb
    if _dynamodb is None:
        logger.info(f"Initializing DynamoDB client with region: {AWS_REGION}")
        _dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    return _dynamodb

def get_table(table_name: str):
    """Get DynamoDB table reference with proper naming."""
    full_table_name = f"{table_name}-{TABLE_PREFIX}" if TABLE_PREFIX else table_name
    dynamodb = get_dynamodb()
    return dynamodb.Table(full_table_name)

# ============================================================================
# ACTIVITY LOG TOOLS
# ============================================================================
# description: Human-readable explanation of the parameter (shown to LLMs)
# ge/gt/le/lt: Greater/less than (or equal) constraints
# min_length/max_length: String or collection length constraints
# pattern: Regex pattern for string validation
# default: Default value if parameter is omitted

class ActivityTypes(Enum):
    food = "food"
    drink = "drink"
    sleep = "sleep"
    smoking = "smoking"
    exercise = "exercise"
    supplement = "supplement"
    stomach = "stomach"

class FoodAndDrinkActivityTypes(Enum):
    food = "food"
    drink = "drink"


class ProcessedDataDrinkAndFood(BaseModel):
    """Nutritional data for food or drink items."""
    description: Annotated[str, Field(description="LLM's detailed interpretation of the food/drink item (e.g., 'one cup of black coffee', '1 medium avocado', '150g grilled chicken breast')")]
    estimated_portion_size: Annotated[Optional[str], Field(description="Estimated portion size (e.g., '1 cup', '100g', '1 medium avocado')", default=None)]
    macro_nutrients: Annotated[Dict[str, float], Field(description="Macronutrients in grams: {'protein': 2.0, 'carbs': 9.0, 'fat': 15.0, 'fiber': 7.0}")]
    micro_nutrients: Annotated[Dict[str, str], Field(description="Key micronutrients with amounts: {'vitamin_e': '2.7mg', 'potassium': '485mg', 'folate': '81mcg'}")]
    glycemic_load: Annotated[int, Field(description="Estimated glycemic load (0-10 scale, where 0-10 is low, 11-19 medium, 20+ high)", ge=0, le=50)]

class ProcessedDataExercise(BaseModel):
    """Exercise activity data."""
    duration_min: Annotated[int, Field(description="Duration of exercise in minutes", ge=1)]
    exercise_type: Annotated[str, Field(description="Type of exercise (e.g., 'running', 'weightlifting', 'yoga', 'swimming')")]
    intensity: Annotated[Optional[str], Field(description="Intensity level: 'low', 'moderate', or 'high'", default=None)] = None

@mcp.tool()
def create_food_or_drink_activity_log(
    activity_type: Annotated[FoodAndDrinkActivityTypes, Field(description="Type of food or drink activity: 'food' or 'drink'")],
    raw_input: Annotated[str, Field(description="Original text/voice/image input from the user describing what they ate or drank")],
    processed_data: Annotated[
        ProcessedDataDrinkAndFood,
        Field(description="Nutritional data including: description (detailed interpretation of food/drink), estimated_portion_size (optional string), macro_nutrients (dict with protein/carbs/fat/fiber as floats), micro_nutrients (dict with vitamin amounts as strings), and glycemic_load (int 0-50)")
    ],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
    owner: Annotated[Optional[str], Field(description="User ID or email address to associate this activity with", default=None)] = None,
) -> str:
    """
    Create a food or drink activity log entry in DynamoDB with structured nutritional data.
    """
    try:
        table = get_table("ActivityLog")
        logger.info(f"Creating new activity log entry for {activity_type}")
        # Generate ID and timestamps
        item_id = f"activity-{datetime.utcnow().timestamp()}"
        now = datetime.utcnow().isoformat() + "Z"
        timestamp = timestamp or now
        
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "activityType": activity_type.value,  # Convert Enum to string
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        # Add optional fields
        if processed_data:
            # Convert Pydantic model to dict, then to JSON string
            item["processedData"] = json.dumps(processed_data.model_dump())
        if owner:
            item["owner"] = owner
            
        # Put item in DynamoDB
        table.put_item(Item=item)

        return json.dumps({
            "success": True,
            "message": "Activity log created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_activity_logs(
    owner: Annotated[Optional[str], Field(description="Filter by owner/user ID or email address", default=None)] = None,
    activity_type: Annotated[Optional[str], Field(description="Filter by activity type (food, drink, exercise, supplement, sleep, smoking, stomach)", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum number of items to return", ge=1, le=100, default=50)] = 50,
    start_date: Annotated[Optional[str], Field(description="Filter activities after this date (ISO format: YYYY-MM-DDTHH:MM:SSZ)", default=None)] = None,
    end_date: Annotated[Optional[str], Field(description="Filter activities before this date (ISO format: YYYY-MM-DDTHH:MM:SSZ)", default=None)] = None
) -> str:
    """
    Fetch activity log entries from DynamoDB with optional filters for owner, type, and date range.
    """
    try:
        table = get_table("ActivityLog")
        
        # Build scan parameters
        scan_kwargs = {
            "Limit": limit
        }
        
        # Build filter expression
        filter_expressions = []
        
        if owner:
            filter_expressions.append(Attr("owner").eq(owner))
        
        if activity_type:
            filter_expressions.append(Attr("activityType").eq(activity_type))
            
        if start_date:
            filter_expressions.append(Attr("timestamp").gte(start_date))
            
        if end_date:
            filter_expressions.append(Attr("timestamp").lte(end_date))
        
        # Combine filters
        if filter_expressions:
            filter_expr = filter_expressions[0]
            for expr in filter_expressions[1:]:
                filter_expr = filter_expr & expr
            scan_kwargs["FilterExpression"] = filter_expr
        
        # Perform scan
        response = table.scan(**scan_kwargs)
        items = response.get("Items", [])
        
        # Parse JSON strings back to objects
        for item in items:
            if "processedData" in item and isinstance(item["processedData"], str):
                try:
                    item["processedData"] = json.loads(item["processedData"])
                except:
                    pass
        
        return json.dumps({
            "success": True,
            "count": len(items),
            "data": items
        }, indent=2, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# # ============================================================================
# # USER PROFILE TOOLS
# # ============================================================================
#
# @mcp.tool()
# def get_user_profile(owner: str) -> str:
#     """
#     Fetch user profile from DynamoDB.
#
#     Args:
#         owner: User ID/email to fetch profile for
#
#     Returns:
#         JSON string with the user profile data
#     """
#     try:
#         table = get_table("UserProfile")
#
#         # Scan for profile with this owner
#         response = table.scan(
#             FilterExpression=Attr("owner").eq(owner),
#             Limit=1
#         )
#
#         items = response.get("Items", [])
#
#         if not items:
#             return json.dumps({
#                 "success": False,
#                 "message": "User profile not found"
#             }, indent=2)
#
#         return json.dumps({
#             "success": True,
#             "data": items[0]
#         }, indent=2, default=str)
#
#     except Exception as e:
#         return json.dumps({
#             "success": False,
#             "error": str(e)
#         }, indent=2)
#
#
# @mcp.tool()
# def update_user_profile(
#     owner: str,
#     email: Optional[str] = None,
#     gender: Optional[str] = None,
#     date_of_birth: Optional[str] = None,
#     weight: Optional[float] = None,
#     height: Optional[float] = None,
#     activity_level: Optional[str] = None,
#     dietary_preferences: Optional[str] = None,
#     health_goals: Optional[str] = None,
#     allergies: Optional[str] = None,
#     medications: Optional[str] = None
# ) -> str:
#     """
#     Create or update user profile in DynamoDB.
#
#     Args:
#         owner: User ID/email
#         email: User's email
#         gender: User's gender
#         date_of_birth: Date of birth (YYYY-MM-DD format)
#         weight: Weight in kg
#         height: Height in cm
#         activity_level: Activity level (sedentary, light, moderate, active, very_active)
#         dietary_preferences: Dietary preferences
#         health_goals: Health goals
#         allergies: Known allergies
#         medications: Current medications
#
#     Returns:
#         JSON string with the updated profile
#     """
#     try:
#         table = get_table("UserProfile")
#
#         # Check if profile exists
#         response = table.scan(
#             FilterExpression=Attr("owner").eq(owner),
#             Limit=1
#         )
#
#         items = response.get("Items", [])
#         now = datetime.utcnow().isoformat() + "Z"
#
#         if items:
#             # Update existing profile
#             item_id = items[0]["id"]
#             update_expr = "SET updatedAt = :now"
#             expr_values = {":now": now}
#             expr_names = {}
#
#             # Build update expression for provided fields
#             fields = {
#                 "email": email,
#                 "gender": gender,
#                 "dateOfBirth": date_of_birth,
#                 "weight": weight,
#                 "height": height,
#                 "activityLevel": activity_level,
#                 "dietaryPreferences": dietary_preferences,
#                 "healthGoals": health_goals,
#                 "allergies": allergies,
#                 "medications": medications
#             }
#
#             for field_name, value in fields.items():
#                 if value is not None:
#                     placeholder = f":{field_name}"
#                     name_placeholder = f"#{field_name}"
#                     update_expr += f", {name_placeholder} = {placeholder}"
#                     expr_values[placeholder] = value
#                     expr_names[name_placeholder] = field_name
#
#             table.update_item(
#                 Key={"id": item_id},
#                 UpdateExpression=update_expr,
#                 ExpressionAttributeValues=expr_values,
#                 ExpressionAttributeNames=expr_names if expr_names else None
#             )
#
#             # Fetch updated item
#             updated = table.get_item(Key={"id": item_id})
#
#             return json.dumps({
#                 "success": True,
#                 "message": "Profile updated successfully",
#                 "data": updated.get("Item", {})
#             }, indent=2, default=str)
#
#         else:
#             # Create new profile
#             item_id = f"profile-{datetime.utcnow().timestamp()}"
#
#             item = {
#                 "id": item_id,
#                 "owner": owner,
#                 "createdAt": now,
#                 "updatedAt": now,
#             }
#
#             # Add all provided fields
#             if email: item["email"] = email
#             if gender: item["gender"] = gender
#             if date_of_birth: item["dateOfBirth"] = date_of_birth
#             if weight: item["weight"] = weight
#             if height: item["height"] = height
#             if activity_level: item["activityLevel"] = activity_level
#             if dietary_preferences: item["dietaryPreferences"] = dietary_preferences
#             if health_goals: item["healthGoals"] = health_goals
#             if allergies: item["allergies"] = allergies
#             if medications: item["medications"] = medications
#
#             table.put_item(Item=item)
#
#             return json.dumps({
#                 "success": True,
#                 "message": "Profile created successfully",
#                 "data": item
#             }, indent=2, default=str)
#
#     except Exception as e:
#         return json.dumps({
#             "success": False,
#             "error": str(e)
#         }, indent=2)
#
#
# # ============================================================================
# # MEMORY ENTRY TOOLS
# # ============================================================================
#
# @mcp.tool()
# def create_memory_entry(
#     entry_type: str,
#     name: str,
#     data: Dict[str, Any],
#     owner: Optional[str] = None
# ) -> str:
#     """
#     Create a new memory entry (saved food, exercise, etc.) in DynamoDB.
#
#     Args:
#         entry_type: Type of entry (food, exercise, custom)
#         name: Name of the item (e.g., "Greek Yogurt", "Morning Run")
#         data: Structured data about the item (nutritional info, exercise details, etc.)
#         owner: User ID/email (owner of the record)
#
#     Returns:
#         JSON string with the created memory entry
#     """
#     try:
#         table = get_table("MemoryEntry")
#
#         # Generate ID and timestamps
#         item_id = f"memory-{datetime.utcnow().timestamp()}"
#         now = datetime.utcnow().isoformat() + "Z"
#
#         item = {
#             "id": item_id,
#             "entryType": entry_type,
#             "name": name,
#             "data": json.dumps(data),
#             "createdAt": now,
#             "updatedAt": now,
#         }
#
#         if owner:
#             item["owner"] = owner
#
#         # Put item in DynamoDB
#         table.put_item(Item=item)
#
#         return json.dumps({
#             "success": True,
#             "message": "Memory entry created successfully",
#             "data": item
#         }, indent=2)
#
#     except Exception as e:
#         return json.dumps({
#             "success": False,
#             "error": str(e)
#         }, indent=2)
#
#
# @mcp.tool()
# def get_memory_entries(
#     owner: Optional[str] = None,
#     entry_type: Optional[str] = None,
#     name_contains: Optional[str] = None,
#     limit: int = 50
# ) -> str:
#     """
#     Fetch memory entries from DynamoDB.
#
#     Args:
#         owner: Filter by owner/user ID
#         entry_type: Filter by entry type (food, exercise, custom)
#         name_contains: Filter by entries whose name contains this string
#         limit: Maximum number of items to return (default: 50)
#
#     Returns:
#         JSON string with the list of memory entries
#     """
#     try:
#         table = get_table("MemoryEntry")
#
#         # Build scan parameters
#         scan_kwargs = {
#             "Limit": limit
#         }
#
#         # Build filter expression
#         filter_expressions = []
#
#         if owner:
#             filter_expressions.append(Attr("owner").eq(owner))
#
#         if entry_type:
#             filter_expressions.append(Attr("entryType").eq(entry_type))
#
#         if name_contains:
#             filter_expressions.append(Attr("name").contains(name_contains))
#
#         # Combine filters
#         if filter_expressions:
#             filter_expr = filter_expressions[0]
#             for expr in filter_expressions[1:]:
#                 filter_expr = filter_expr & expr
#             scan_kwargs["FilterExpression"] = filter_expr
#
#         # Perform scan
#         response = table.scan(**scan_kwargs)
#         items = response.get("Items", [])
#
#         # Parse JSON strings back to objects
#         for item in items:
#             if "data" in item and isinstance(item["data"], str):
#                 try:
#                     item["data"] = json.loads(item["data"])
#                 except:
#                     pass
#
#         return json.dumps({
#             "success": True,
#             "count": len(items),
#             "data": items
#         }, indent=2, default=str)
#
#     except Exception as e:
#         return json.dumps({
#             "success": False,
#             "error": str(e)
#         }, indent=2)


# ============================================================================
# RESOURCES - Provide data context to LLMs
# ============================================================================

# @mcp.resource("profile://{owner}")
# def get_profile_resource(owner: str) -> str:
#     """Get user profile as a resource for LLM context."""
#     result = get_user_profile(owner)
#     return result


@mcp.resource("recent-activities://{owner}")
def get_recent_activities_resource(owner: str) -> str:
    """Get recent activity logs as a resource for LLM context."""
    result = get_activity_logs(owner=owner, limit=20)
    return result


# ============================================================================
# MAIN - Run the server
# ============================================================================

# The 'mcp' object is automatically used by:
# - Local development: `uv run mcp dev main.py`
# - Cloud deployment: FastMCP imports and serves this object via HTTP
# - Claude Desktop: Add this file to claude_desktop_config.json
#
# Only call mcp.run() if you're running this file directly with Python
# (not recommended - use 'mcp dev' instead)
if __name__ == "__main__":
    # This block is not needed for normal FastMCP usage
    # Uncomment below only if you want to run with `python main.py` directly
    # mcp.run()
    pass
