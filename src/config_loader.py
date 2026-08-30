import os
import json
import tempfile
from datetime import datetime, timedelta

def get_base_dir():
    return os.environ.get("SPARKJOBS_WORKSPACE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_path():
    return os.path.join(get_base_dir(), "data", "config.json")

def get_seen_jobs_path():
    return os.path.join(get_base_dir(), "data", "seen_jobs.json")

def get_status_tracker_path():
    return os.path.join(get_base_dir(), "data", "status_tracker.json")

def get_cvs_dir():
    return os.path.join(get_base_dir(), "data", "cvs")

def get_cover_letter_path():
    return os.path.join(get_base_dir(), "data", "cover_letter.txt")

def get_jobs_history_path():
    return os.path.join(get_base_dir(), "data", "jobs_history.json")

BASE_DIR = get_base_dir()
CONFIG_PATH = get_config_path()
SEEN_JOBS_PATH = get_seen_jobs_path()
STATUS_TRACKER_PATH = get_status_tracker_path()
CVS_DIR = get_cvs_dir()
COVER_LETTER_PATH = get_cover_letter_path()
JOBS_HISTORY_PATH = get_jobs_history_path()

JOBS_HISTORY_MAX_ENTRIES = 1000
JOBS_HISTORY_DAYS = 7

def load_jobs_history() -> dict:
    path = get_jobs_history_path()
    if not os.path.exists(path):
        return {"jobs": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"jobs": []}

def save_jobs_history(history: dict):
    path = get_jobs_history_path()
    cutoff = datetime.utcnow() - timedelta(days=JOBS_HISTORY_DAYS)
    fresh_jobs = []
    for j in history.get("jobs", []):
        scraped_at_str = j.get("scraped_at", "")
        if not scraped_at_str:
            fresh_jobs.append(j)
            continue
        try:
            job_dt = datetime.fromisoformat(scraped_at_str.replace("Z", "+00:00"))
            if job_dt.tzinfo is not None:
                job_dt = job_dt.replace(tzinfo=None)
            if job_dt >= cutoff:
                fresh_jobs.append(j)
        except Exception:
            fresh_jobs.append(j)

    history["jobs"] = fresh_jobs
    if len(history["jobs"]) > JOBS_HISTORY_MAX_ENTRIES:
        history["jobs"] = history["jobs"][-JOBS_HISTORY_MAX_ENTRIES:]
    
    tmp_path = None
    try:
        dir_name = os.path.dirname(path)
        os.makedirs(dir_name, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="history_", suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
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
    path = get_status_tracker_path()
    if not os.path.exists(path):
        return {
            "last_summary_sent": datetime.now().isoformat(),
            "scans_completed_this_week": 0,
            "jobs_evaluated_this_week": 0,
            "alerts_sent_this_week": 0
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
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
    path = get_status_tracker_path()
    tmp_path = None
    try:
        dir_name = os.path.dirname(path)
        os.makedirs(dir_name, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="tracker_", suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(tracker, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
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
    path = get_config_path()
    if not os.path.exists(path):
        print(f"Config file not found at {path}. Creating empty config template.")
        dir_name = os.path.dirname(path)
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
            os.replace(tmp_path, path)
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
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading config: {e}")
        try:
            sentinel_path = os.path.join(os.path.dirname(path), ".config_corrupted")
            with open(sentinel_path, "w") as sf:
                sf.write(str(e))
        except Exception:
            pass
        return {}
