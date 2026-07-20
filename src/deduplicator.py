import os
import json
from datetime import datetime, timedelta

def load_seen_jobs(file_path: str) -> dict:
    """
    Loads the seen jobs dictionary from the JSON database file.
    """
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading seen_jobs database: {e}")
        return {}

import tempfile

def save_seen_jobs(file_path: str, data: dict):
    """
    C-07 Fix: Saves the seen jobs dictionary atomically to prevent file corruption.
    """
    try:
        dir_name = os.path.dirname(file_path)
        os.makedirs(dir_name, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="seen_", suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, file_path)
    except (TypeError, OSError) as e:
        print(f"Error saving seen_jobs database: {e}")

def is_job_seen(db: [dict, str], job_id: str) -> bool:
    """
    Checks if a job_id has been seen before.
    Supports either a pre-loaded dict (in-memory fast path) or a file path string.
    """
    if isinstance(db, dict):
        return job_id in db
    seen_jobs = load_seen_jobs(db)
    return job_id in seen_jobs

def mark_job_as_seen(db: [dict, str], job_id: str, title: str, company: str):
    """
    Saves a job_id with metadata and current timestamp to the seen jobs database.
    Supports mutating an in-memory dict or disk persistence.
    """
    if isinstance(db, dict):
        db[job_id] = {
            "title": title,
            "company": company,
            "date": datetime.now().isoformat()
        }
        return

    seen_jobs = load_seen_jobs(db)
    seen_jobs[job_id] = {
        "title": title,
        "company": company,
        "date": datetime.now().isoformat()
    }
    save_seen_jobs(db, seen_jobs)

def cleanup_old_jobs(db: [dict, str], days_to_keep: int = 30) -> dict:
    """
    Prunes the database, deleting entries older than the retention limit (default 30 days)
    to prevent file size bloat.
    """
    seen_jobs = db if isinstance(db, dict) else load_seen_jobs(db)
    if not seen_jobs:
        return {}

    cutoff = datetime.now() - timedelta(days=days_to_keep)
    pruned_jobs = {}
    pruned_count = 0

    for job_id, meta in seen_jobs.items():
        try:
            job_date_str = meta.get("date", "")
            if job_date_str:
                job_date = datetime.fromisoformat(job_date_str)
                if job_date > cutoff:
                    pruned_jobs[job_id] = meta
                else:
                    pruned_count += 1
            else:
                pruned_jobs[job_id] = meta
        except Exception:
            pruned_jobs[job_id] = meta

    if pruned_count > 0:
        print(f"Cleaned up {pruned_count} old jobs from database.")
        if isinstance(db, str):
            save_seen_jobs(db, pruned_jobs)
            
    return pruned_jobs

if __name__ == "__main__":
    test_db = "data/seen_jobs_test.json"
    mark_job_as_seen(test_db, "test-123", "Developer", "Acme")
    print(f"Is test-123 seen: {is_job_seen(test_db, 'test-123')}")
    print(f"Is test-456 seen: {is_job_seen(test_db, 'test-456')}")
    cleanup_old_jobs(test_db)
    if os.path.exists(test_db):
        os.remove(test_db)
