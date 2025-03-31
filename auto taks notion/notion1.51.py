import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
notion_api_key = ("Your api kay notion")
database_id = ("Your id database")
#notion_api_key = os.environ.get("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")
#database_id = os.environ.get("57f542d3864944b8b266840dbf72f5af")
checkbox_property_name = os.environ.get("NOTION_CHECKBOX_PROPERTY", "Hecho")
due_date_property_name = os.environ.get("NOTION_DUE_DATE_PROPERTY", "Fecha")
# Add configurable reschedule days
reschedule_offset = int(os.environ.get("RESCHEDULE_OFFSET", "1"))

# Validate required configuration
if not notion_api_key:
    print("Error: NOTION_API_KEY is not set in environment variables")
    exit(1)

if not database_id:
    print("Error: NOTION_DATABASE_ID is not set in environment variables")
    exit(1)

# Initialize the Notion client
notion = Client(auth=notion_api_key)

async def get_database_properties(database_id):
    try:
        response = notion.databases.retrieve(database_id=database_id)
        properties = response["properties"]
        print("Database Properties:")
        for name, property_config in properties.items():
            print(f"- {name} ({property_config['type']})")
    except Exception as error:
        print(f"Error retrieving database properties: {error}")

async def reschedule_tasks():
    try:
        print("Starting task rescheduling process...")

        # 1. Query the database with pagination support
        all_tasks = []
        has_more = True
        next_cursor = None

        while has_more:
            response = notion.databases.query(
                database_id=database_id,
                start_cursor=next_cursor,
                page_size=100,
                filter={
                    "and": [
                        {
                            "property": checkbox_property_name,
                            "checkbox": {
                                "equals": False
                            }
                        },
                        {
                            "property": due_date_property_name,
                            "date": {
                                "is_not_empty": True
                            }
                        }
                    ]
                }
            )

            all_tasks.extend(response["results"])
            has_more = response["has_more"]
            next_cursor = response.get("next_cursor")

        print(f"Found {len(all_tasks)} incomplete tasks with due dates")

        last_moved_date = None
        rescheduled_count = 0

        # 2. Iterate through the tasks and reschedule them if necessary
        for task in all_tasks:
            try:
                # Get the due date property
                due_date_value = task["properties"][due_date_property_name]["date"]["start"]

                if not due_date_value:
                    continue

                due_date = datetime.fromisoformat(due_date_value)
                # Make sure due_date is timezone naive for comparison
                if due_date.tzinfo is not None:
                    due_date = due_date.replace(tzinfo=None)
                
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) # Normalize today's date

                # Get task title for logging
                task_title = task["properties"].get("title", {}).get("title", [{}])[0].get("plain_text", task["id"])

                if due_date < today:
                    # Calculate the new due date (tomorrow or sequential)
                    new_due_date = today + timedelta(days=reschedule_offset)

                    if last_moved_date:
                        new_due_date = last_moved_date + timedelta(days=reschedule_offset)

                    # Ensure we don't schedule on weekends if configured
                    if os.environ.get('AVOID_WEEKENDS') == 'true':
                        # 0 = Monday, 6 = Sunday in Python datetime, but getday() in TS was 0 = Sunday, 6 = Saturday
                        while new_due_date.weekday() == 6 or new_due_date.weekday() == 5: # Saturday or Sunday
                            new_due_date += timedelta(days=1)

                    new_due_date_str = new_due_date.isoformat().split('T')[0]


                    # Update the task in Notion
                    notion.pages.update(
                        page_id=task["id"],
                        properties={
                            due_date_property_name: {
                                "date": {
                                    "start": new_due_date_str,
                                }
                            }
                        }
                    )

                    # Add a comment about rescheduling if supported
                    try:
                        notion.comments.create(
                            parent={"page_id": task["id"]},
                            rich_text=[{
                                "text": {
                                    "content": f"Automatically rescheduled from {due_date_value} to {new_due_date_str}"
                                }
                            }]
                        )
                    except Exception as comment_error: # Using generic exception to catch comment errors
                        # Comments might not be available in all Notion plans
                        print(f"Could not add comment to task: {comment_error}")


                    last_moved_date = new_due_date
                    rescheduled_count += 1

                    print(f'Task "{task_title}" rescheduled from {due_date_value} to {new_due_date_str}')

            except Exception as task_error: # Using generic exception to catch task errors
                print(f"Error processing task {task['id']}: {task_error}")
                # Continue with other tasks even if one fails


        print(f"Tasks rescheduling completed: {rescheduled_count} tasks updated")

    except Exception as error: # Using generic exception to catch main errors
        print(f"Error rescheduling tasks: {error}")
        exit(1)

# Execute the function
if __name__ == "__main__":
    import asyncio
    #syncio.run(get_database_properties(database_id)) # Run get_database_properties to list properties
    asyncio.run(reschedule_tasks()) # Comment out reschedule_tasks for now
