import os
import json
import tempfile
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
    """
    C-07 Fix: Saves status tracker dictionary atomically to prevent file corruption.
    """
    try:
        dir_name = os.path.dirname(STATUS_TRACKER_PATH)
        os.makedirs(dir_name, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="tracker_", suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(tracker, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, STATUS_TRACKER_PATH)
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
        # L-05 Fix: Flag config corruption via sentinel file so scanner can notify Telegram
        try:
            sentinel_path = os.path.join(os.path.dirname(CONFIG_PATH), ".config_corrupted")
            with open(sentinel_path, "w") as sf:
                sf.write(str(e))
        except Exception:
            pass
        return {}
