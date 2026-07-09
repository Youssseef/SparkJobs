import os
import json
import random
import time
from datetime import datetime
from cv_processor import extract_text_from_pdf
from scraper import run_all_scrapes
from fraud_detector import analyze_job_for_fraud
from ai_matcher import analyze_job_match
from deduplicator import is_job_seen, mark_job_as_seen, cleanup_old_jobs
from telegram_sender import send_telegram_alert

# Paths definition
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "data", "config.json")
SEEN_JOBS_PATH = os.path.join(BASE_DIR, "data", "seen_jobs.json")
CVS_DIR = os.path.join(BASE_DIR, "data", "cvs")

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
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        return default_config
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def get_cv_text(cv_version: str) -> str:
    """
    Loads text from CV file. Supports .pdf and .txt.
    """
    if not cv_version:
        return ""
    
    # Check for PDF
    pdf_path = os.path.join(CVS_DIR, f"{cv_version}.pdf")
    if os.path.exists(pdf_path):
        return extract_text_from_pdf(pdf_path)
        
    # Check for TXT fallback
    txt_path = os.path.join(CVS_DIR, f"{cv_version}.txt")
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading txt CV {txt_path}: {e}")
            
    print(f"Warning: CV file not found for '{cv_version}' in {CVS_DIR}")
    return ""

def run_scanner():
    """
    Orchestrator for the periodic job scan.
    """
    print(f"=== Starting SparkJobs Scan Cycle: {datetime.now().isoformat()} ===")
    config = load_config()
    
    gemini_key = config.get("gemini_api_key", "")
    bot_token = config.get("telegram_bot_token", "")
    chat_id = config.get("telegram_chat_id", "")
    scraperapi_key = config.get("scraperapi_key", "")
    profiles = config.get("profiles", [])
    
    if not profiles:
        print("No job profiles configured. Stopping scanner.")
        return

    active_profiles = [p for p in profiles if p.get("active", True)]
    print(f"Found {len(active_profiles)} active profiles out of {len(profiles)} total profiles.")

    for profile in active_profiles:
        profile_name = profile.get("name", "Default Profile")
        job_titles = profile.get("job_titles", [])
        countries = profile.get("countries", [])
        remote_only = profile.get("remote", False)
        min_score = profile.get("min_match_score", 65)
        cv_version = profile.get("cv_version", "default_cv")

        print(f"\n--- Scanning Profile: {profile_name} (Min Score: {min_score}%) ---")
        
        # Load candidate CV
        cv_text = get_cv_text(cv_version)
        if not cv_text:
            print(f"Skipping profile '{profile_name}' due to missing CV.")
            continue

        for title in job_titles:
            for country in countries:
                location = "Remote" if remote_only else country
                print(f"Scanning for '{title}' in '{location}'...")
                
                # Fetch fresh postings
                jobs = run_all_scrapes(title, location, scraperapi_key)
                
                # Filter, deduplicate, and notify
                new_jobs_count = 0
                alerts_sent_count = 0
                
                for job in jobs:
                    job_id = job["id"]
                    
                    # 1. Check Deduplication
                    if is_job_seen(SEEN_JOBS_PATH, job_id):
                        continue
                    
                    new_jobs_count += 1
                    
                    # 2. Check Local Fraud Heuristics
                    fraud_result = analyze_job_for_fraud(job)
                    
                    # If high risk scam, we log it and skip to protect user
                    if fraud_result["risk_level"] == "High":
                        print(f"Skipping High Risk/Scam job: {job['title']} at {job['company']}")
                        # Mark as seen so we don't scan it again
                        mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])
                        continue
                    
                    # 3. AI Semantic Match & Custom Outreach Generation
                    ai_result = analyze_job_match(
                        cv_text=cv_text,
                        job_title=job["title"],
                        job_desc=job["description"],
                        api_key=gemini_key,
                        min_match_score=min_score
                    )
                    
                    # Merge local fraud alerts with AI risk comments
                    if fraud_result["is_suspicious"]:
                        ai_result["risk_level"] = fraud_result["risk_level"]
                        ai_result["risk_reason"] = ", ".join(fraud_result["reasons"])
                    
                    match_score = ai_result.get("match_score", 0)
                    
                    # 4. Score Threshold Check
                    if match_score >= min_score:
                        # Send alert to Telegram
                        success = send_telegram_alert(
                            bot_token=bot_token,
                            chat_id=chat_id,
                            job=job,
                            ai_analysis=ai_result,
                            profile_name=profile_name
                        )
                        if success:
                            alerts_sent_count += 1
                            # Mark as seen to prevent future duplicate triggers
                            mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])
                            # Anti-spam delay between Telegram alerts
                            time.sleep(random.uniform(1.0, 2.0))
                    else:
                        # Match score too low. We mark it as seen so we don't evaluate it again
                        mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])

                print(f"Scrape completed: {new_jobs_count} new postings evaluated. {alerts_sent_count} alerts sent.")
                # Politeness delay between search query switches
                time.sleep(random.uniform(2.0, 4.0))

    # Run Database cleanup
    cleanup_old_jobs(SEEN_JOBS_PATH)
    print("=== Scan Cycle Completed ===")

if __name__ == "__main__":
    # Create required data directories locally
    os.makedirs(CVS_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    run_scanner()
