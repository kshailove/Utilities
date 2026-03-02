import requests
import time
import json
from tqdm import tqdm

# ==============================
# CONFIG
# ==============================

API_TOKEN = "pk_CLICKUP_API_TOKEN" # add your Clickup API token here
LIST_ID = {"901613603056", "901611772335"}   # loop multiple lists

# LIST_ID = {"901613603056"}   # or loop multiple lists
# For example in this list link, https://app.clickup.com/3698397/v/li/11958889/5661685?pr=3845399, 11958889 is the list id.
# For more details, refer to Clickup api documentation

OUTPUT_FILE = "clickup_export.json"

BASE_URL = "https://api.clickup.com/api/v2"

HEADERS = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}

RATE_LIMIT_SLEEP = 0.3


# ==============================
# HELPERS
# ==============================

def api_get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)

    if r.status_code == 400:
        print("BAD REQUEST:", r.text)

    r.raise_for_status()
    return r.json()


# ==============================
# FETCH TASKS
# ==============================

def fetch_all_tasks(list_id):
    print("Fetching tasks...")
    tasks = []
    page = 0

    while True:
        url = f"{BASE_URL}/list/{list_id}/task"
        params = {
            "page": page,
            "subtasks": "true",
            "include_closed": "true"
        }

        data = api_get(url, params)

        batch = data.get("tasks", [])
        if not batch:
            break

        tasks.extend(batch)
        page += 1
        time.sleep(RATE_LIMIT_SLEEP)

    return tasks


# ==============================
# FETCH COMMENTS
# ==============================

def fetch_comments(task_id):
    url = f"{BASE_URL}/task/{task_id}/comment"
    data = api_get(url)

    comments = []
    for c in data.get("comments", []):
        comments.append({
            "comment_id": c["id"],
            "text": c.get("comment_text"),
            "timestamp": c.get("date"),
            "user": c.get("user", {}).get("username"),
            "user_email": c.get("user", {}).get("email"),
            "resolved": c.get("resolved")
        })

    return comments


# ==============================
# FETCH ACTIVITY / TIMELINE
# ==============================

def fetch_activity(task_id):
    url = f"{BASE_URL}/task/{task_id}/activity"
    data = api_get(url)

    events = []

    for e in data:
        events.append({
            "event": e.get("type"),
            "date": e.get("date"),
            "user": e.get("user", {}).get("username"),
            "details": e.get("data")
        })

    return events


# ==============================
# NORMALIZE TASK
# ==============================

def normalize_task(task):
    return {
        "id": task["id"],
        "name": task["name"],
        "description": task.get("description"),
        "status": task.get("status", {}).get("status"),
        "priority": task.get("priority"),
        "created": task.get("date_created"),
        "updated": task.get("date_updated"),
        "due_date": task.get("due_date"),
        "assignees": [
            a["username"] for a in task.get("assignees", [])
        ],
        "tags": [t["name"] for t in task.get("tags", [])],
        "url": task.get("url"),
        "custom_fields": task.get("custom_fields", []),
        "attachments": task.get("attachments", [])
    }


# ==============================
# MAIN EXPORT
# ==============================

def export_clickup():
   
   for thislist in LIST_ID:
        tasks = fetch_all_tasks(thislist)

        print(f"Found total {len(tasks)} tasks in list {thislist}")

        export_data = []

        for task in tqdm(tasks):

            task_id = task["id"]

            normalized = normalize_task(task)

            try:
                normalized["comments"] = fetch_comments(task_id)
            except Exception:
                normalized["comments"] = []

            time.sleep(RATE_LIMIT_SLEEP)

            try:
                normalized["activity"] = fetch_activity(task_id)
            except Exception:
                normalized["activity"] = []

            export_data.append(normalized)

        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)

        print(f"\n✅ Export complete → {OUTPUT_FILE}")


# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    export_clickup()
