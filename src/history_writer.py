import os
from datetime import datetime
from config_loader import load_jobs_history, save_jobs_history

def detect_ats_platform(url: str) -> str:
    # Phase 1 stub, will be replaced with real two-tier detection in Phase 2
    return "unknown"

def append_to_history(new_jobs: list):
    """
    Appends newly evaluated jobs to jobs_history.json.
    """
    if not new_jobs:
        return
    
    history = load_jobs_history()
    for job in new_jobs:
        history["jobs"].append({
            "id": job["id"],
            "title": job["title"],
            "company": job.get("company", ""),
            "location": job.get("location", "Remote"),
            "url": job["url"],
            "source": job.get("source", "unknown"),
            "match_score": job.get("match_score", 0),
            "scraped_at": datetime.utcnow().isoformat() + "Z",
            "ats_platform": detect_ats_platform(job["url"])
        })
    save_jobs_history(history)
