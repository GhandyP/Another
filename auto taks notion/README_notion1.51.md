# Notion Task Rescheduler (`notion1.51.py`)

## Overview

This Python script connects to the Notion API to automatically reschedule overdue tasks in a specified Notion database. It finds tasks that are marked as incomplete (checkbox unchecked) and whose due date is in the past. These tasks are then updated with a new due date, typically set to a configured number of days from today or sequentially after the previously rescheduled task.

## Dependencies

The script requires the following Python libraries:

*   `os`: For accessing environment variables.
*   `datetime`: For handling dates and times.
*   `dotenv`: For loading environment variables from a `.env` file.
*   `notion-client`: The official Notion API client library.

You can install the necessary libraries using pip:

```bash
pip install python-dotenv notion-client
```

## Configuration

The script is configured using environment variables, which can be set directly in your system or placed in a `.env` file in the same directory as the script.

**Required:**

*   `NOTION_API_KEY`: Your Notion integration's API key. **Crucial for authentication.**
    *   _Script variable:_ `notion_api_key`
    *   _Default placeholder in script:_ `"Your api kay notion"` (This **must** be replaced or overridden by the environment variable).
*   `NOTION_DATABASE_ID`: The ID of the Notion database containing the tasks you want to manage.
    *   _Script variable:_ `database_id`
    *   _Default placeholder in script:_ `"Your id database"` (This **must** be replaced or overridden by the environment variable).

**Optional (with defaults):**

*   `NOTION_CHECKBOX_PROPERTY`: The exact name of the checkbox property in your Notion database that indicates if a task is completed.
    *   _Script variable:_ `checkbox_property_name`
    *   _Default:_ `"Hecho"`
*   `NOTION_DUE_DATE_PROPERTY`: The exact name of the date property in your Notion database that holds the task's due date.
    *   _Script variable:_ `due_date_property_name`
    *   _Default:_ `"Fecha"`
*   `RESCHEDULE_OFFSET`: The number of days to push an overdue task forward from today (or the last rescheduled task's date).
    *   _Script variable:_ `reschedule_offset`
    *   _Default:_ `1` (meaning reschedule to tomorrow or the next available day).
*   `AVOID_WEEKENDS`: Set to `'true'` if you want the script to skip Saturdays and Sundays when calculating the new due date. Any other value (or if omitted) will allow scheduling on weekends.
    *   _Script variable:_ `avoid_weekends`
    *   _Default:_ `false`

**Example `.env` file:**

```dotenv
NOTION_API_KEY="secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
NOTION_DATABASE_ID="yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
NOTION_CHECKBOX_PROPERTY="Done"
NOTION_DUE_DATE_PROPERTY="Due Date"
RESCHEDULE_OFFSET="1"
AVOID_WEEKENDS="true"
```

## How it Works

1.  **Load Configuration:** Reads the API key, database ID, and other settings from environment variables (using `.env` if present).
2.  **Validation:** Checks if the `NOTION_API_KEY` and `NOTION_DATABASE_ID` are set. Exits if they are missing or still have the placeholder values.
3.  **Initialize Client:** Creates an instance of the Notion client using the provided API key.
4.  **Query Database (`reschedule_tasks` function):**
    *   Sends a query to the specified Notion database.
    *   Uses a filter to find pages (tasks) that meet **both** conditions:
        *   The checkbox property (`NOTION_CHECKBOX_PROPERTY`) is `false` (unchecked).
        *   The date property (`NOTION_DUE_DATE_PROPERTY`) is not empty.
    *   Handles pagination to retrieve all matching tasks, even if there are more than 100.
5.  **Iterate and Reschedule:**
    *   Loops through each task found in the query results.
    *   Extracts the current due date from the task's properties.
    *   Compares the due date with today's date (normalized to the start of the day).
    *   **If the task is overdue (due date < today):**
        *   Calculates the `new_due_date`:
            *   It starts from `today + RESCHEDULE_OFFSET`.
            *   If other tasks were already rescheduled in this run, it schedules sequentially: `last_moved_date + RESCHEDULE_OFFSET`. This prevents multiple overdue tasks from piling up on the same future date.
            *   If `AVOID_WEEKENDS` is `true`, it increments the `new_due_date` until it falls on a weekday (Monday-Friday).
        *   Formats the `new_due_date` as a `YYYY-MM-DD` string.
        *   **Updates the task in Notion:** Sends an API request to change the task's due date property to the `new_due_date_str`.
        *   **Adds a Comment (Optional):** Attempts to add a comment to the Notion page indicating that the task was automatically rescheduled and the original date. This might fail depending on the Notion plan or permissions, but the script will print a warning and continue.
        *   Updates `last_moved_date` for sequential scheduling.
        *   Prints a confirmation message to the console.
6.  **Completion Message:** After processing all tasks, prints a summary of how many tasks were rescheduled.

## How to Use

1.  **Set up Notion Integration:**
    *   Go to [Notion's My Integrations page](https://www.notion.so/my-integrations).
    *   Create a new integration. Give it a name (e.g., "Task Rescheduler").
    *   Copy the "Internal Integration Token" - this is your `NOTION_API_KEY`.
    *   Go to the Notion database you want to use. Click the `...` menu > "Add connections" and select the integration you just created.
    *   Find your `NOTION_DATABASE_ID`: It's the part of the database URL between the last `/` and the `?v=...`. For example, in `https://www.notion.so/your-workspace/abcdef1234567890abcdef1234567890?v=...`, the ID is `abcdef1234567890abcdef1234567890`.
2.  **Configure the Script:**
    *   Create a `.env` file in the same directory as `notion1.51.py`.
    *   Add your `NOTION_API_KEY` and `NOTION_DATABASE_ID` to the `.env` file.
    *   Adjust `NOTION_CHECKBOX_PROPERTY`, `NOTION_DUE_DATE_PROPERTY`, `RESCHEDULE_OFFSET`, and `AVOID_WEEKENDS` in the `.env` file if your database uses different names or you want different behavior.
3.  **Install Dependencies:**
    ```bash
    pip install python-dotenv notion-client
    ```
4.  **Run the Script:**
    ```bash
    python notion1.51.py
    ```
    You can schedule this script to run automatically (e.g., daily) using tools like `cron` (Linux/macOS) or Task Scheduler (Windows).

## Debugging

*   **Check Property Names:** If the script reports errors like `KeyError` or doesn't find tasks you expect, double-check the exact names of your "Done" checkbox and "Due Date" properties in Notion and ensure they match the values in your `.env` file or the script defaults.
*   **`get_database_properties` Function:** The script includes a commented-out function `get_database_properties`. You can uncomment the line `asyncio.run(get_database_properties(database_id))` and comment out `asyncio.run(reschedule_tasks())` in the `if __name__ == "__main__":` block. Running the script then will print a list of all properties in your database and their types, which can help verify the correct names.
*   **API Key/Database ID:** Ensure the API key and Database ID are correct and that the integration has been shared with the database.
*   **Permissions:** Make sure the Notion integration has permission to read and update pages in the database, and potentially add comments if you want that feature.
