import os
import json
import tempfile
from datetime import datetime, timedelta

# Paths definition
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "data", "config.json")
SEEN_JOBS_PATH = os.path.join(BASE_DIR, "data", "seen_jobs.json")
STATUS_TRACKER_PATH = os.path.join(BASE_DIR, "data", "status_tracker.json")
CVS_DIR = os.path.join(BASE_DIR, "data", "cvs")
COVER_LETTER_PATH = os.path.join(BASE_DIR, "data", "cover_letter.txt")
JOBS_HISTORY_PATH = os.path.join(BASE_DIR, "data", "jobs_history.json")

JOBS_HISTORY_MAX_ENTRIES = 1000
JOBS_HISTORY_DAYS = 7

def load_jobs_history() -> dict:
    if not os.path.exists(JOBS_HISTORY_PATH):
        return {"jobs": []}
    try:
        with open(JOBS_HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"jobs": []}

def save_jobs_history(history: dict):
    """
    Saves jobs history atomically, enforcing 7-day expiry and a 1,000-entry safety cap.
    """
    cutoff = (datetime.utcnow() - timedelta(days=JOBS_HISTORY_DAYS)).isoformat() + "Z"
    history["jobs"] = [j for j in history.get("jobs", []) if j.get("scraped_at", "") >= cutoff]
    if len(history["jobs"]) > JOBS_HISTORY_MAX_ENTRIES:
        history["jobs"] = history["jobs"][-JOBS_HISTORY_MAX_ENTRIES:]
    
    tmp_path = None
    try:
        dir_name = os.path.dirname(JOBS_HISTORY_PATH)
        os.makedirs(dir_name, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="history_", suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, JOBS_HISTORY_PATH)
        tmp_path = None
    except (TypeError, OSError) as e:
        print(f"Error saving jobs history: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


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
    C-07 & M-08 Fix: Saves status tracker dictionary atomically to prevent file corruption,
    and cleans up temp files on failure.
    """
    tmp_path = None
    try:
        dir_name = os.path.dirname(STATUS_TRACKER_PATH)
        os.makedirs(dir_name, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="tracker_", suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(tracker, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, STATUS_TRACKER_PATH)
        tmp_path = None
    except (TypeError, OSError) as e:
        print(f"Error saving status tracker: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

def load_config() -> dict:
    """
    Loads configuration settings.
    L-05 Fix: Uses atomic write pattern for default config creation.
    """
    if not os.path.exists(CONFIG_PATH):
        print(f"Config file not found at {CONFIG_PATH}. Creating empty config template.")
        dir_name = os.path.dirname(CONFIG_PATH)
        os.makedirs(dir_name, exist_ok=True)
        default_config = {
            "gemini_api_key": "",
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "scraperapi_key": "",
            "profiles": []
        }
        tmp_path = None
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="cfg_", suffix=".tmp")
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, CONFIG_PATH)
            tmp_path = None
        except (TypeError, OSError) as e:
            print(f"Error writing default config: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
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
