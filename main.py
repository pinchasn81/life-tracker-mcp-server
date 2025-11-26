"""
LifeTracker MCP Server

An MCP server that provides tools to interact with LifeTracker DynamoDB tables.
Supports reading and writing to ActivityLog, UserProfile, MemoryEntry, and QuickAction tables.
"""
import logging
import os
import json
from datetime import datetime, UTC
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Override any existing configuration
)

# Use root logger or module logger
logger = logging.getLogger("LifeTracker")
logger.setLevel(logging.INFO)

# Helper function to ensure logs appear in FastMCP server logs
def log(level: str, message: str):
    """Log message to both Python logger and stdout for FastMCP visibility."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)
    print(message)  # Ensures visibility in FastMCP server logs

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
        log("info", f"Initializing DynamoDB client with region: {AWS_REGION}")
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

class ProcessedDataSleep(BaseModel):
    """Sleep activity data."""
    duration_hours: Annotated[float, Field(description="Duration of sleep in hours (e.g., 7.5)", ge=0, le=24)]
    quality: Annotated[Optional[str], Field(description="Sleep quality: 'poor', 'fair', 'good', or 'excellent'", default=None)] = None
    notes: Annotated[Optional[str], Field(description="Additional notes about sleep (e.g., 'woke up twice', 'had nightmares')", default=None)] = None

class ProcessedDataSmoking(BaseModel):
    """Smoking activity data."""
    type: Annotated[str, Field(description="Type of smoking (e.g., 'cigarette', 'vape', 'cigar', 'hookah')")]
    quantity: Annotated[int, Field(description="Number of cigarettes/sessions", ge=1)]
    notes: Annotated[Optional[str], Field(description="Additional notes (e.g., brand, triggers, feelings)", default=None)] = None

class ProcessedDataSupplement(BaseModel):
    """Supplement/medication intake data."""
    name: Annotated[str, Field(description="Name of the supplement or medication (e.g., 'Vitamin D', 'Omega-3', 'Magnesium')")]
    dosage: Annotated[float, Field(description="Dosage amount as a number (e.g., 1000, 500)", ge=0)]
    unit: Annotated[str, Field(description="Dosage unit (e.g., 'mg', 'mcg', 'IU', 'tablets', 'capsules')")]
    notes: Annotated[Optional[str], Field(description="Additional notes (e.g., 'with food', 'morning dose')", default=None)] = None

class ProcessedDataStomach(BaseModel):
    """Stomach issues/digestive symptoms data."""
    symptoms: Annotated[list[str], Field(description="List of symptoms (e.g., ['bloating', 'gas', 'diarrhea', 'constipation', 'cramping', 'nausea'])")]
    severity: Annotated[Optional[str], Field(description="Severity level: 'mild', 'moderate', or 'severe'", default=None)] = None
    notes: Annotated[Optional[str], Field(description="Additional context (e.g., 'after eating dairy', 'lasted 2 hours')", default=None)] = None

class ProcessedDataGeneric(BaseModel):
    """Generic/freestyle activity data for activities not covered by specific types."""
    description: Annotated[str, Field(description="Detailed description of the activity/event (e.g., 'feeling tired and fatigued', 'came down with a cold', 'feeling energetic and positive')")]
    category: Annotated[Optional[str], Field(description="Optional category/tag for this activity (e.g., 'illness', 'mood', 'symptom', 'energy_level')", default=None)] = None
    severity: Annotated[Optional[str], Field(description="Severity or intensity if applicable: 'mild', 'moderate', or 'severe'", default=None)] = None
    notes: Annotated[Optional[str], Field(description="Additional notes or context", default=None)] = None

@mcp.tool()
def create_food_or_drink_activity_log(
    activity_type: Annotated[FoodAndDrinkActivityTypes, Field(description="Type of food or drink activity: 'food' or 'drink'")],
    raw_input: Annotated[str, Field(description="Original text/voice/image input from the user describing what they ate or drank")],
    processed_data: Annotated[
        ProcessedDataDrinkAndFood,
        Field(description="Nutritional data including: description (detailed interpretation of food/drink), estimated_portion_size (optional string), macro_nutrients (dict with protein/carbs/fat/fiber as floats), micro_nutrients (dict with vitamin amounts as strings), and glycemic_load (int 0-50)")
    ],
    user_name: Annotated[str, Field(description="User name/identifier to associate this activity with")],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
) -> str:
    """
    Create a food or drink activity log entry in DynamoDB with structured nutritional data.
    """
    log("info", f"[create_food_or_drink_activity_log] START - activity_type={activity_type.value}, user_name={user_name}, raw_input='{raw_input}', timestamp={timestamp}")
    try:
        table = get_table("ActivityLog")
        
        # Generate ID and timestamps
        item_id = f"activity-{datetime.now(UTC).timestamp()}"
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
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
        
        item["user_name"] = user_name
            
        # Put item in DynamoDB
        response = table.put_item(Item=item)
        
        log("info", f"[create_food_or_drink_activity_log] SUCCESS - created activity_id={item_id}, user_name={user_name}, activity_type={activity_type.value}")

        return json.dumps({
            "success": True,
            "message": "Activity log created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        log("error", f"[create_food_or_drink_activity_log] ERROR - user_name={user_name}, activity_type={activity_type}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_exercise_activity_log(
    raw_input: Annotated[str, Field(description="Original text/voice/image input from the user describing the exercise activity")],
    processed_data: Annotated[
        ProcessedDataExercise,
        Field(description="Exercise data including: duration_min (int, minutes of exercise), exercise_type (string, e.g. 'running', 'yoga'), and intensity (optional: 'low', 'moderate', or 'high')")
    ],
    user_name: Annotated[str, Field(description="User name/identifier to associate this activity with")],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
    activity_type: Annotated[str, Field(description="Activity type, defaults to 'exercise'", default="exercise")] = "exercise",
) -> str:
    """
    Create an exercise activity log entry in DynamoDB with structured exercise data.
    """
    log("info", f"[create_exercise_activity_log] START - user_name={user_name}, raw_input='{raw_input}', processed_data={processed_data.model_dump()}, activity_type={activity_type}, timestamp={timestamp}")
    try:
        table = get_table("ActivityLog")
        # Generate ID and timestamps
        item_id = f"activity-{datetime.now(UTC).timestamp()}"
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        timestamp = timestamp or now
        
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "activityType": activity_type,
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        # Add optional fields
        if processed_data:
            # Convert Pydantic model to dict, then to JSON string
            item["processedData"] = json.dumps(processed_data.model_dump())
        
        item["user_name"] = user_name
            
        # Put item in DynamoDB
        response = table.put_item(Item=item)
        
        log("info", f"[create_exercise_activity_log] SUCCESS - created activity_id={item_id}, user_name={user_name}, activity_type={activity_type}")

        return json.dumps({
            "success": True,
            "message": "Exercise log created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        log("error", f"[create_exercise_activity_log] ERROR - user_name={user_name}, activity_type={activity_type}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_sleep_activity_log(
    raw_input: Annotated[str, Field(description="Original text/voice input from the user describing their sleep")],
    processed_data: Annotated[
        ProcessedDataSleep,
        Field(description="Sleep data including: duration_hours (float, hours slept), quality (optional: 'poor', 'fair', 'good', 'excellent'), and notes (optional additional context)")
    ],
    user_name: Annotated[str, Field(description="User name/identifier to associate this activity with")],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
    activity_type: Annotated[str, Field(description="Activity type, defaults to 'sleep'", default="sleep")] = "sleep",
) -> str:
    """
    Create a sleep activity log entry in DynamoDB with structured sleep data.
    """
    log("info", f"[create_sleep_activity_log] START - user_name={user_name}, raw_input='{raw_input}', processed_data={processed_data.model_dump()}, activity_type={activity_type}, timestamp={timestamp}")
    try:
        table = get_table("ActivityLog")
        item_id = f"activity-{datetime.now(UTC).timestamp()}"
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        timestamp = timestamp or now
        
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "activityType": activity_type,
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        if processed_data:
            item["processedData"] = json.dumps(processed_data.model_dump())
        if user_name:
            item["user_name"] = user_name
            
        response = table.put_item(Item=item)
        
        log("info", f"[create_sleep_activity_log] SUCCESS - created activity_id={item_id}, user_name={user_name}, duration={processed_data.duration_hours}h")

        return json.dumps({
            "success": True,
            "message": "Sleep log created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        log("error", f"[create_sleep_activity_log] ERROR - user_name={user_name}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_smoking_activity_log(
    raw_input: Annotated[str, Field(description="Original text/voice input from the user describing their smoking activity")],
    processed_data: Annotated[
        ProcessedDataSmoking,
        Field(description="Smoking data including: type (e.g., 'cigarette', 'vape'), quantity (int, number of cigarettes/sessions), and notes (optional)")
    ],
    user_name: Annotated[str, Field(description="User name/identifier to associate this activity with")],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
    activity_type: Annotated[str, Field(description="Activity type, defaults to 'smoking'", default="smoking")] = "smoking",
) -> str:
    """
    Create a smoking activity log entry in DynamoDB with structured smoking data.
    """
    log("info", f"[create_smoking_activity_log] START - user_name={user_name}, raw_input='{raw_input}', processed_data={processed_data.model_dump()}, activity_type={activity_type}, timestamp={timestamp}")
    try:
        table = get_table("ActivityLog")
        item_id = f"activity-{datetime.now(UTC).timestamp()}"
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        timestamp = timestamp or now
        
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "activityType": activity_type,
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        if processed_data:
            item["processedData"] = json.dumps(processed_data.model_dump())
        if user_name:
            item["user_name"] = user_name
            
        response = table.put_item(Item=item)
        
        log("info", f"[create_smoking_activity_log] SUCCESS - created activity_id={item_id}, user_name={user_name}, type={processed_data.type}, quantity={processed_data.quantity}")

        return json.dumps({
            "success": True,
            "message": "Smoking log created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        log("error", f"[create_smoking_activity_log] ERROR - user_name={user_name}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_supplement_activity_log(
    raw_input: Annotated[str, Field(description="Original text/voice input from the user describing the supplement/medication taken")],
    processed_data: Annotated[
        ProcessedDataSupplement,
        Field(description="Supplement data including: name (supplement name), dosage (float, amount), unit (e.g., 'mg', 'IU', 'tablets'), and notes (optional)")
    ],
    user_name: Annotated[str, Field(description="User name/identifier to associate this activity with")],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
    activity_type: Annotated[str, Field(description="Activity type, defaults to 'supplement'", default="supplement")] = "supplement",
) -> str:
    """
    Create a supplement/medication activity log entry in DynamoDB with structured supplement data.
    """
    log("info", f"[create_supplement_activity_log] START - user_name={user_name}, raw_input='{raw_input}', processed_data={processed_data.model_dump()}, activity_type={activity_type}, timestamp={timestamp}")
    try:
        table = get_table("ActivityLog")
        item_id = f"activity-{datetime.now(UTC).timestamp()}"
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        timestamp = timestamp or now
        
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "activityType": activity_type,
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        if processed_data:
            item["processedData"] = json.dumps(processed_data.model_dump())
        if user_name:
            item["user_name"] = user_name
            
        response = table.put_item(Item=item)
        
        log("info", f"[create_supplement_activity_log] SUCCESS - created activity_id={item_id}, user_name={user_name}, supplement={processed_data.name}, dosage={processed_data.dosage}{processed_data.unit}")

        return json.dumps({
            "success": True,
            "message": "Supplement log created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        log("error", f"[create_supplement_activity_log] ERROR - user_name={user_name}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_stomach_activity_log(
    raw_input: Annotated[str, Field(description="Original text/voice input from the user describing their stomach issues/symptoms")],
    processed_data: Annotated[
        ProcessedDataStomach,
        Field(description="Stomach issues data including: symptoms (list of strings like ['bloating', 'gas', 'diarrhea']), severity (optional: 'mild', 'moderate', 'severe'), and notes (optional context)")
    ],
    user_name: Annotated[str, Field(description="User name/identifier to associate this activity with")],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
    activity_type: Annotated[str, Field(description="Activity type, defaults to 'stomach'", default="stomach")] = "stomach",
) -> str:
    """
    Create a stomach issues activity log entry in DynamoDB with structured symptom data.
    """
    log("info", f"[create_stomach_activity_log] START - user_name={user_name}, raw_input='{raw_input}', processed_data={processed_data.model_dump()}, activity_type={activity_type}, timestamp={timestamp}")
    try:
        table = get_table("ActivityLog")
        item_id = f"activity-{datetime.now(UTC).timestamp()}"
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        timestamp = timestamp or now
        
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "activityType": activity_type,
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        if processed_data:
            item["processedData"] = json.dumps(processed_data.model_dump())
        if user_name:
            item["user_name"] = user_name
            
        table.put_item(Item=item)

        return json.dumps({
            "success": True,
            "message": "Stomach issues log created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_activity_log(
    activity_type: Annotated[str, Field(description="Type of activity (e.g., 'illness', 'mood', 'energy', 'pain', 'medication', or any custom type)")],
    raw_input: Annotated[str, Field(description="Original text/voice input from the user describing the activity")],
    processed_data: Annotated[
        ProcessedDataGeneric,
        Field(description="Generic activity data including: description (detailed description), severity (optional: 'mild', 'moderate', 'severe'), tags (optional list for categorization), and notes (optional)")
    ],
    user_name: Annotated[str, Field(description="User name/identifier to associate this activity with")],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
) -> str:
    """
    Create a generic activity log entry in DynamoDB for any activity type (illness, mood, energy, pain, etc.).
    """
    log("info", f"[create_activity_log] START - activity_type={activity_type}, user_name={user_name}, raw_input='{raw_input}', processed_data={processed_data.model_dump()}, timestamp={timestamp}")
    try:
        table = get_table("ActivityLog")
        item_id = f"activity-{datetime.now(UTC).timestamp()}"
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        timestamp = timestamp or now
        
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "activityType": activity_type,
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        if processed_data:
            item["processedData"] = json.dumps(processed_data.model_dump())
        
        item["user_name"] = user_name
            
        response = table.put_item(Item=item)
        
        log("info", f"[create_activity_log] SUCCESS - created activity_id={item_id}, user_name={user_name}, activity_type={activity_type}")

        return json.dumps({
            "success": True,
            "message": f"{activity_type.capitalize()} log created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        log("error", f"[create_activity_log] ERROR - user_name={user_name}, activity_type={activity_type}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_generic_activity_log(
    activity_type: Annotated[str, Field(description="Type of activity (e.g., 'illness', 'mood', 'symptom', 'energy_level', 'feeling', or any custom type)")],
    raw_input: Annotated[str, Field(description="Original text/voice input from the user describing the activity or event")],
    processed_data: Annotated[
        ProcessedDataGeneric,
        Field(description="Generic activity data including: description (detailed description), category (optional tag/category), severity (optional: 'mild', 'moderate', 'severe'), and notes (optional additional context)")
    ],
    user_name: Annotated[str, Field(description="User name/identifier to associate this activity with")],
    timestamp: Annotated[Optional[str], Field(description="ISO format timestamp (defaults to current UTC time if not provided)", default=None)] = None,
) -> str:
    """
    Create a generic/freestyle activity log entry for activities not covered by specific types (e.g., illness, mood, symptoms, energy levels).
    """
    log("info", f"[create_generic_activity_log] START - activity_type={activity_type}, user_name={user_name}, raw_input='{raw_input}', processed_data={processed_data.model_dump()}, timestamp={timestamp}")
    try:
        table = get_table("ActivityLog")
        item_id = f"activity-{datetime.now(UTC).timestamp()}"
        now = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        timestamp = timestamp or now
        
        item = {
            "id": item_id,
            "timestamp": timestamp,
            "activityType": activity_type,
            "rawInput": raw_input,
            "createdAt": now,
            "updatedAt": now,
        }
        
        if processed_data:
            item["processedData"] = json.dumps(processed_data.model_dump())
        if user_name:
            item["user_name"] = user_name
            
        response = table.put_item(Item=item)
        
        log("info", f"[create_generic_activity_log] SUCCESS - created activity_id={item_id}, user_name={user_name}, activity_type={activity_type}")

        return json.dumps({
            "success": True,
            "message": f"Generic activity log ({activity_type}) created successfully",
            "data": item
        }, indent=2)
        
    except Exception as e:
        log("error", f"[create_generic_activity_log] ERROR - user_name={user_name}, activity_type={activity_type}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_activity_logs(
    user_name: Annotated[Optional[str], Field(description="Filter by user_name/user ID or email address", default=None)] = None,
    activity_type: Annotated[Optional[str], Field(description="Filter by activity type (food, drink, exercise, supplement, sleep, smoking, stomach)", default=None)] = None,
    limit: Annotated[int, Field(description="Maximum number of items to return", ge=1, le=100, default=50)] = 50,
    start_date: Annotated[Optional[str], Field(description="Filter activities after this date (ISO format: YYYY-MM-DDTHH:MM:SSZ)", default=None)] = None,
    end_date: Annotated[Optional[str], Field(description="Filter activities before this date (ISO format: YYYY-MM-DDTHH:MM:SSZ)", default=None)] = None
) -> str:
    """
    Fetch activity log entries from DynamoDB with optional filters for user_name, type, and date range.
    """
    log("info", f"[get_activity_logs] START - user_name={user_name}, activity_type={activity_type}, limit={limit}, start_date={start_date}, end_date={end_date}")
    try:
        table = get_table("ActivityLog")
        
        # If user_name is provided, try to use Query on GSI for better performance
        # Fall back to Scan if GSI doesn't exist
        if user_name:
            try:
                log("info", f"[get_activity_logs] Attempting Query on user_name GSI")
                
                # Build query parameters
                query_kwargs = {
                    "IndexName": "user_name-index",  # GSI name - adjust if different
                    "KeyConditionExpression": Key("user_name").eq(user_name),
                    "Limit": limit,
                }
                
                # Build additional filters for activity_type and dates
                filter_expressions = []
                
                if activity_type:
                    filter_expressions.append(Attr("activityType").eq(activity_type))
                    
                if start_date:
                    filter_expressions.append(Attr("timestamp").gte(start_date))
                    
                if end_date:
                    filter_expressions.append(Attr("timestamp").lte(end_date))
                
                # Add filter expression if we have additional filters
                if filter_expressions:
                    filter_expr = filter_expressions[0]
                    for expr in filter_expressions[1:]:
                        filter_expr = filter_expr & expr
                    query_kwargs["FilterExpression"] = filter_expr
                
                # Perform query
                response = table.query(**query_kwargs)
                log("info", f"[get_activity_logs] Query successful on GSI")
                
            except Exception as gsi_error:
                # GSI doesn't exist or error - fall back to Scan
                log("warning", f"[get_activity_logs] GSI query failed ({str(gsi_error)}), falling back to Scan with ConsistentRead")
                
                scan_kwargs = {
                    "Limit": limit,
                    "ConsistentRead": True,  # Use strongly consistent reads
                    "FilterExpression": Attr("user_name").eq(user_name)
                }
                
                # Build additional filters
                filter_expressions = [Attr("user_name").eq(user_name)]
                
                if activity_type:
                    filter_expressions.append(Attr("activityType").eq(activity_type))
                    
                if start_date:
                    filter_expressions.append(Attr("timestamp").gte(start_date))
                    
                if end_date:
                    filter_expressions.append(Attr("timestamp").lte(end_date))
                
                # Combine filters
                filter_expr = filter_expressions[0]
                for expr in filter_expressions[1:]:
                    filter_expr = filter_expr & expr
                scan_kwargs["FilterExpression"] = filter_expr
                
                response = table.scan(**scan_kwargs)
        else:
            log("info", f"[get_activity_logs] Using Scan (no user_name filter)")
            
            # Build scan parameters
            scan_kwargs = {
                "Limit": limit,
                "ConsistentRead": True,  # Use strongly consistent reads for better accuracy
            }
            
            # Build filter expression
            filter_expressions = []
            
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
        
        log("info", f"[get_activity_logs] SUCCESS - found {len(items)} activity logs")
        
        return json.dumps({
            "success": True,
            "count": len(items),
            "data": items
        }, indent=2, default=str)
        
    except Exception as e:
        log("error", f"[get_activity_logs] ERROR - user_name={user_name}, activity_type={activity_type}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def delete_activity_log(
    activity_id: Annotated[str, Field(description="The ID of the activity log entry to delete (e.g., 'activity-1234567890.123')")]
) -> str:
    """
    Delete an activity log entry from DynamoDB by its ID.
    """
    log("info", f"[delete_activity_log] START - activity_id={activity_id}")
    try:
        table = get_table("ActivityLog")
        
        # Delete the item from DynamoDB
        response = table.delete_item(
            Key={"id": activity_id},
            ReturnValues="ALL_OLD"  # Return the deleted item
        )
        
        # Check if item was actually deleted
        deleted_item = response.get("Attributes")
        if deleted_item:
            log("info", f"[delete_activity_log] SUCCESS - deleted activity_id={activity_id}")
            return json.dumps({
                "success": True,
                "message": f"Activity log {activity_id} deleted successfully",
                "deleted_item": deleted_item
            }, indent=2, default=str)
        else:
            log("warning", f"[delete_activity_log] NOT_FOUND - activity_id={activity_id}")
            return json.dumps({
                "success": False,
                "message": f"Activity log {activity_id} not found"
            }, indent=2)
        
    except Exception as e:
        log("error", f"[delete_activity_log] ERROR - activity_id={activity_id}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def delete_all_user_activities(
    user_name: Annotated[str, Field(description="User name/identifier whose all activity logs should be deleted")]
) -> str:
    """
    Delete all activity log entries for a specific user from DynamoDB.
    """
    log("info", f"[delete_all_user_activities] START - user_name={user_name}")
    try:
        table = get_table("ActivityLog")
        
        # Try Query on GSI first, fall back to Scan if GSI doesn't exist
        try:
            log("info", f"[delete_all_user_activities] Attempting Query on user_name GSI")
            response = table.query(
                IndexName="user_name-index",  # GSI name - adjust if different
                KeyConditionExpression=Key("user_name").eq(user_name)
            )
            using_query = True
        except Exception as gsi_error:
            log("warning", f"[delete_all_user_activities] GSI query failed ({str(gsi_error)}), falling back to Scan")
            response = table.scan(
                FilterExpression=Attr("user_name").eq(user_name),
                ConsistentRead=True
            )
            using_query = False
        
        items = response.get("Items", [])
        deleted_count = 0
        
        log("info", f"[delete_all_user_activities] Found {len(items)} items to delete")
        
        # Delete each item
        for item in items:
            table.delete_item(Key={"id": item["id"]})
            deleted_count += 1
        
        # Handle pagination if there are more items
        while "LastEvaluatedKey" in response:
            if using_query:
                response = table.query(
                    IndexName="user_name-index",
                    KeyConditionExpression=Key("user_name").eq(user_name),
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
            else:
                response = table.scan(
                    FilterExpression=Attr("user_name").eq(user_name),
                    ConsistentRead=True,
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
            items = response.get("Items", [])
            log("info", f"[delete_all_user_activities] Found {len(items)} more items in next page")
            for item in items:
                table.delete_item(Key={"id": item["id"]})
                deleted_count += 1
        
        log("info", f"[delete_all_user_activities] SUCCESS - deleted {deleted_count} activities for user_name={user_name}")
        
        return json.dumps({
            "success": True,
            "message": f"Deleted {deleted_count} activity log(s) for user {user_name}",
            "deleted_count": deleted_count,
            "user_name": user_name
        }, indent=2)
        
    except Exception as e:
        log("error", f"[delete_all_user_activities] ERROR - user_name={user_name}, error={str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# # ============================================================================
# # USER PROFILE TOOLS
# # ============================================================================
#
# @mcp.tool()
# def get_user_profile(user_name: str) -> str:
#     """
#     Fetch user profile from DynamoDB.
#
#     Args:
#         user_name: User ID/email to fetch profile for
#
#     Returns:
#         JSON string with the user profile data
#     """
#     try:
#         table = get_table("UserProfile")
#
#         # Scan for profile with this user_name
#         response = table.scan(
#             FilterExpression=Attr("user_name").eq(user_name),
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
#     user_name: str,
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
#         user_name: User ID/email
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
#             FilterExpression=Attr("user_name").eq(user_name),
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
#                 "user_name": user_name,
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
#     user_name: Optional[str] = None
# ) -> str:
#     """
#     Create a new memory entry (saved food, exercise, etc.) in DynamoDB.
#
#     Args:
#         entry_type: Type of entry (food, exercise, custom)
#         name: Name of the item (e.g., "Greek Yogurt", "Morning Run")
#         data: Structured data about the item (nutritional info, exercise details, etc.)
#         user_name: User ID/email (user_name of the record)
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
#         if user_name:
#             item["user_name"] = user_name
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
#     user_name: Optional[str] = None,
#     entry_type: Optional[str] = None,
#     name_contains: Optional[str] = None,
#     limit: int = 50
# ) -> str:
#     """
#     Fetch memory entries from DynamoDB.
#
#     Args:
#         user_name: Filter by user_name/user ID
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
#         if user_name:
#             filter_expressions.append(Attr("user_name").eq(user_name))
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

# @mcp.resource("profile://{user_name}")
# def get_profile_resource(user_name: str) -> str:
#     """Get user profile as a resource for LLM context."""
#     result = get_user_profile(user_name)
#     return result


@mcp.resource("recent-activities://{user_name}")
def get_recent_activities_resource(user_name: str, limit: int = 20) -> str:
    """Get recent activity logs as a resource for LLM context."""
    log("info", f"[get_recent_activities_resource] START - user_name={user_name}, limit={limit}")
    try:
        result = get_activity_logs(user_name=user_name, limit=limit)
        log("info", f"[get_recent_activities_resource] SUCCESS - fetched activities for user_name={user_name}")
        return result
    except Exception as e:
        log("error", f"[get_recent_activities_resource] ERROR - user_name={user_name}, error={str(e)}")
        return json.dumps({"success": False, "error": str(e)}, indent=2)


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
