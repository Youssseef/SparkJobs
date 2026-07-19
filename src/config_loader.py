import os
import json
from datetime import datetime

# Paths definition
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "data", "config.json")
SEEN_JOBS_PATH = os.path.join(BASE_DIR, "data", "seen_jobs.json")
STATUS_TRACKER_PATH = os.path.join(BASE_DIR, "data", "status_tracker.json")
CVS_DIR = os.path.join(BASE_DIR, "data", "cvs")
COVER_LETTER_PATH = os.path.join(BASE_DIR, "data", "cover_letter.txt")

def load_status_tracker() -> dict:
    if not os.path.exists(STATUS_TRACKER_PATH):
        return {
            "last_summary_sent": datetime.now().isoformat(),
            "scans_completed_this_week": 0,
            "jobs_evaluated_this_week": 0,
            "alerts_sent_this_week": 0
        }
    try:
        with open(STATUS_TRACKER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading status tracker: {e}")
        return {
            "last_summary_sent": datetime.now().isoformat(),
            "scans_completed_this_week": 0,
            "jobs_evaluated_this_week": 0,
            "alerts_sent_this_week": 0
        }

def save_status_tracker(tracker: dict):
    try:
        os.makedirs(os.path.dirname(STATUS_TRACKER_PATH), exist_ok=True)
        with open(STATUS_TRACKER_PATH, "w", encoding="utf-8") as f:
            json.dump(tracker, f, indent=2)
    except (TypeError, OSError) as e:
        print(f"Error saving status tracker: {e}")

def load_config() -> dict:
    """
    Loads configuration settings.
    """
    if not os.path.exists(CONFIG_PATH):
        print(f"Config file not found at {CONFIG_PATH}. Creating empty config template.")
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        default_config = {
            "gemini_api_key": "",
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "scraperapi_key": "",
            "profiles": []
        }
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
        except OSError as e:
            print(f"Error writing default config: {e}")
        return default_config
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading config: {e}")
        return {}
