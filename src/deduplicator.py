import os
import json
import tempfile
from datetime import datetime, timedelta

def load_seen_jobs(file_path: str) -> dict:
    """
    Loads the seen jobs dictionary from the JSON database file.
    M-13 Fix: Validates root JSON is a dict to prevent array corruption crashes.
    """
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            print(f"Warning: seen_jobs database at {file_path} root is not a dict ({type(data).__name__}). Resetting.")
            return {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading seen_jobs database: {e}")
        return {}

def save_seen_jobs(file_path: str, data: dict):
    """
    C-07 & M-08 Fix: Saves the seen jobs dictionary atomically to prevent file corruption,
    and cleans up temp files on failure.
    """
    tmp_path = None
    try:
        dir_name = os.path.dirname(file_path)
        os.makedirs(dir_name, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="seen_", suffix=".tmp")
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, file_path)
        tmp_path = None
    except (TypeError, OSError) as e:
        print(f"Error saving seen_jobs database: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

import hashlib
import re

def normalize_text_key(text: str) -> str:
    """Normalizes title or company name to alphanumeric lowercase for fuzzy deduplication."""
    if not text or not isinstance(text, str):
        return ""
    # Strip common suffixes like Inc, LLC, Ltd, GmbH, Corp
    cleaned = re.sub(r'(?i)\b(inc|llc|ltd|gmbh|corp|corporation|co|company|technologies|tech)\b', '', text)
    # Remove all non-alphanumeric chars
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', cleaned).lower()
    return cleaned

def get_job_signature(title: str, company: str) -> str:
    """Generates a stable cross-platform signature hash for a job."""
    norm_t = normalize_text_key(title)
    norm_c = normalize_text_key(company)
    if not norm_t and not norm_c:
        return ""
    return f"sig-{hashlib.md5(f'{norm_t}::{norm_c}'.encode()).hexdigest()[:12]}"

def get_url_signature(url: str) -> str:
    """Generates a stable hash for a normalized job URL."""
    if not url or not isinstance(url, str):
        return ""
    # Strip tracking parameters (?utm_*, ?trk=*, &ref=*)
    clean_url = url.split("?")[0].rstrip("/").lower()
    return f"url-{hashlib.md5(clean_url.encode()).hexdigest()[:12]}"

def is_job_seen(db: dict | str, job_id: str, title: str = "", company: str = "", url: str = "") -> bool:
    """
    Triple-Shield Deduplication Check:
    1. Exact job_id match (e.g. 'linkedin-12345')
    2. Cross-platform title + company signature match (e.g. 'sig-a1b2c3d4e5f6')
    3. Normalized URL signature match (e.g. 'url-9f8e7d6c5b4a')
    """
    seen_jobs = db if isinstance(db, dict) else load_seen_jobs(db)
    if not seen_jobs:
        return False

    # Shield 1: Direct Job ID
    if job_id and job_id in seen_jobs:
        return True

    # Shield 2: Cross-Platform Title + Company Signature
    if title or company:
        sig = get_job_signature(title, company)
        if sig and sig in seen_jobs:
            return True

    # Shield 3: Clean Canonical URL Signature
    if url:
        url_sig = get_url_signature(url)
        if url_sig and url_sig in seen_jobs:
            return True

    return False

def mark_job_as_seen(db: dict | str, job_id: str, title: str, company: str, url: str = ""):
    """
    Saves a job_id with metadata and current timestamp to the seen jobs database,
    along with cross-platform title+company and URL signatures.
    """
    iso_now = datetime.utcnow().isoformat() + "Z"
    meta = {
        "title": title,
        "company": company,
        "date": iso_now
    }
    if url:
        meta["url"] = url

    target_dict = db if isinstance(db, dict) else load_seen_jobs(db)
    
    # 1. Primary job ID
    if job_id:
        target_dict[job_id] = meta

    # 2. Cross-platform signature
    sig = get_job_signature(title, company)
    if sig:
        target_dict[sig] = meta

    # 3. Canonical URL signature
    if url:
        url_sig = get_url_signature(url)
        if url_sig:
            target_dict[url_sig] = meta

    if not isinstance(db, dict):
        save_seen_jobs(db, target_dict)

def cleanup_old_jobs(db: dict | str, days_to_keep: int = 30) -> dict:
    """
    Prunes the database, deleting entries older than the retention limit (default 30 days)
    to prevent file size bloat. Handles offset-aware and offset-naive timestamps safely.
    """
    seen_jobs = db if isinstance(db, dict) else load_seen_jobs(db)
    if not seen_jobs:
        return {}

    cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
    pruned_jobs = {}
    pruned_count = 0

    for job_id, meta in seen_jobs.items():
        try:
            job_date_str = meta.get("date", "")
            if job_date_str:
                job_date = datetime.fromisoformat(job_date_str.replace("Z", "+00:00"))
                if job_date.tzinfo is not None:
                    job_date = job_date.replace(tzinfo=None)
                if job_date > cutoff:
                    pruned_jobs[job_id] = meta
                else:
                    pruned_count += 1
            else:
                pruned_jobs[job_id] = meta
        except Exception as err:
            print(f"Warning: Failed to parse date '{meta.get('date')}' for job {job_id}: {err}")
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
