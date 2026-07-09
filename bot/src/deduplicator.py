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
    except Exception as e:
        print(f"Error loading seen_jobs database: {e}")
        return {}

def save_seen_jobs(file_path: str, data: dict):
    """
    Saves the seen jobs dictionary back to the JSON database.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving seen_jobs database: {e}")

def is_job_seen(file_path: str, job_id: str) -> bool:
    """
    Checks if a job_id has been seen before.
    """
    seen_jobs = load_seen_jobs(file_path)
    return job_id in seen_jobs

def mark_job_as_seen(file_path: str, job_id: str, title: str, company: str):
    """
    Saves a job_id with metadata and current timestamp to the seen jobs database.
    """
    seen_jobs = load_seen_jobs(file_path)
    seen_jobs[job_id] = {
        "title": title,
        "company": company,
        "date": datetime.now().isoformat()
    }
    save_seen_jobs(file_path, seen_jobs)

def cleanup_old_jobs(file_path: str, days_to_keep: int = 30):
    """
    Prunes the database, deleting entries older than the retention limit (default 30 days)
    to prevent file size bloat.
    """
    seen_jobs = load_seen_jobs(file_path)
    if not seen_jobs:
        return

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
                # Keep if date is missing to be safe
                pruned_jobs[job_id] = meta
        except Exception:
            # Keep on parsing errors
            pruned_jobs[job_id] = meta

    if pruned_count > 0:
        print(f"Cleaned up {pruned_count} old jobs from database.")
        save_seen_jobs(file_path, pruned_jobs)

if __name__ == "__main__":
    # Test execution
    test_db = "data/seen_jobs_test.json"
    mark_job_as_seen(test_db, "test-123", "Developer", "Acme")
    print(f"Is test-123 seen: {is_job_seen(test_db, 'test-123')}")
    print(f"Is test-456 seen: {is_job_seen(test_db, 'test-456')}")
    cleanup_old_jobs(test_db)
    if os.path.exists(test_db):
        os.remove(test_db)
