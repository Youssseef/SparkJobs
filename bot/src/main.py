import os
import json
import random
import time
from datetime import datetime, timedelta
from cv_processor import extract_text_from_pdf, extract_text_from_docx
from scraper import run_all_scrapes
from fraud_detector import analyze_job_for_fraud
from ai_matcher import analyze_job_match
from deduplicator import is_job_seen, mark_job_as_seen, cleanup_old_jobs
from telegram_sender import send_telegram_alert, send_telegram_message, SPARKGEN_FOOTER

# Paths definition
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "data", "config.json")
SEEN_JOBS_PATH = os.path.join(BASE_DIR, "data", "seen_jobs.json")
STATUS_TRACKER_PATH = os.path.join(BASE_DIR, "data", "status_tracker.json")
CVS_DIR = os.path.join(BASE_DIR, "data", "cvs")

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
    except Exception:
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
    except Exception as e:
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
        
    # Check for DOCX
    docx_path = os.path.join(CVS_DIR, f"{cv_version}.docx")
    if os.path.exists(docx_path):
        return extract_text_from_docx(docx_path)
        
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
    
    if config.get("paused", False):
        print("Bot is currently paused. Exiting scan cycle.")
        return
        
    gemini_key = config.get("gemini_api_key", "")
    bot_token = config.get("telegram_bot_token", "")
    chat_id = config.get("telegram_chat_id", "")
    scraperapi_key = config.get("scraperapi_key", "")
    profiles = config.get("profiles", [])
    language = config.get("language", "ar")
    
    tracker = load_status_tracker()
    tracker["scans_completed_this_week"] += 1
    tracker["last_scan_time"] = datetime.now().isoformat()

    # Load candidate cover letter if exists
    cl_path = os.path.join(BASE_DIR, "data", "cover_letter.txt")
    cover_letter = ""
    if os.path.exists(cl_path):
        try:
            with open(cl_path, "r", encoding="utf-8") as f:
                cover_letter = f.read().strip()
            print("Loaded candidate cover letter template for AI outreach guidance.")
        except Exception as e:
            print(f"Error reading cover letter: {e}")

    global_search = config.get("global_search", {})
    
    # Backwards compatibility fallback mappings
    if not global_search and profiles:
        p = profiles[0]
        global_search = {
            "job_titles": p.get("job_titles", []),
            "years_of_experience": p.get("years_of_experience", "3-5"),
            "exclude_keywords": p.get("exclude_keywords", []),
            "cv_version": p.get("cv_version", "default_cv")
        }

    job_titles = global_search.get("job_titles", [])
    years_exp = global_search.get("years_of_experience", "3-5")
    exclude_keywords = global_search.get("exclude_keywords", [])
    cv_version = global_search.get("cv_version", "default_cv")

    target_countries = config.get("target_countries", [])
    if not target_countries and profiles:
        p = profiles[0]
        for countryId in p.get("countries", []):
            target_countries.append({
                "country": countryId,
                "remote_only": "remote" in p.get("job_types", []),
                "requires_visa": "sponsor_required" in p.get("visa_types", []),
                "min_match_score": p.get("min_match_score", 65),
                "active": p.get("active", True)
            })

    if not target_countries:
        print("No target locations configured. Stopping scanner.")
        save_status_tracker(tracker)
        return

    active_countries = [c for c in target_countries if c.get("active", True)]
    print(f"Found {len(active_countries)} active locations out of {len(target_countries)} total locations.")

    scam_jobs_skipped = 0

    # Load candidate CV
    cv_text = get_cv_text(cv_version)
    if not cv_text:
        print("Warning: CV not found or empty. Running in no-CV fallback mode.")

    for tc in active_countries:
        country_name = tc.get("country", "Worldwide")
        remote_only = tc.get("remote_only", False)
        requires_visa = tc.get("requires_visa", False)
        min_score = tc.get("min_match_score", 65)

        print(f"\n--- Scanning Location: {country_name} (Min Score: {min_score}%) ---")

        for title in job_titles:
            location = "Remote" if remote_only else country_name
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
                
                # Check exclusion keywords (case-insensitive)
                should_exclude = False
                if exclude_keywords:
                    job_title_lower = job.get("title", "").lower()
                    job_desc_lower = job.get("description", "").lower()
                    job_company_lower = job.get("company", "").lower()
                    for kw in exclude_keywords:
                        kw_lower = kw.lower()
                        if kw_lower in job_title_lower or kw_lower in job_desc_lower or kw_lower in job_company_lower:
                            should_exclude = True
                            break
                
                if should_exclude:
                    print(f"Skipping job matching exclusion filter: {job['title']} at {job['company']}")
                    mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])
                    continue

                new_jobs_count += 1
                tracker["jobs_evaluated_this_week"] += 1
                
                # 2. Check Local Fraud Heuristics
                fraud_result = analyze_job_for_fraud(job)
                
                # If high risk scam, we log it and skip to protect user
                if fraud_result["risk_level"] == "High":
                    print(f"Skipping High Risk/Scam job: {job['title']} at {job['company']}")
                    mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])
                    scam_jobs_skipped += 1
                    continue
                
                # 3. AI Semantic Match & Custom Outreach Generation
                ai_result = analyze_job_match(
                    cv_text=cv_text,
                    job_title=job["title"],
                    job_desc=job["description"],
                    api_key=gemini_key,
                    min_match_score=min_score,
                    cover_letter=cover_letter,
                    years_exp=years_exp
                )
                
                # Merge local fraud alerts with AI risk comments
                if fraud_result["is_suspicious"]:
                    ai_result["risk_level"] = fraud_result["risk_level"]
                    ai_result["risk_reason"] = ", ".join(fraud_result["reasons"])
                
                match_score = ai_result.get("match_score", 0)
                
                # 4. Score Threshold Check
                if match_score >= min_score:
                    # Send alert to Telegram
                    alert_label = f"{title} ({country_name})"
                    success = send_telegram_alert(
                        bot_token=bot_token,
                        chat_id=chat_id,
                        job=job,
                        ai_analysis=ai_result,
                        profile_name=alert_label,
                        language=language
                    )
                    if success:
                        alerts_sent_count += 1
                        tracker["alerts_sent_this_week"] += 1
                        mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])
                        time.sleep(random.uniform(1.0, 2.0))
                else:
                    mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])

            print(f"Scrape completed: {new_jobs_count} new postings evaluated. {alerts_sent_count} alerts sent.")
            time.sleep(random.uniform(2.0, 4.0))

    # Run Database cleanup
    cleanup_old_jobs(SEEN_JOBS_PATH)
    save_status_tracker(tracker)

    # Send scam summary alert to Telegram if any were filtered
    if scam_jobs_skipped > 0:
        if language == "ar":
            scam_msg = f"⚠️ <b>SparkJobs:</b> تم تصفية وتخطي {scam_jobs_skipped} وظيفة مشبوهة/احتيالية في دورة البحث الحالية لحماية خصوصيتك."
        else:
            scam_msg = f"⚠️ <b>SparkJobs:</b> Automatically filtered and skipped {scam_jobs_skipped} suspicious/scam jobs in this scan cycle to protect your profile."
        send_telegram_message(bot_token, chat_id, scam_msg + SPARKGEN_FOOTER)

    # Check if 7 days have passed since the last summary
    try:
        last_summary_dt = datetime.fromisoformat(tracker.get("last_summary_sent", datetime.now().isoformat()))
        if datetime.now() - last_summary_dt >= timedelta(days=7):
            print("Sending weekly status summary to Telegram...")
            if language == "ar":
                summary_text = (
                    f"<b>تقرير النشاط الأسبوعي لبوت SparkJobs</b>\n\n"
                    f"• عمليات الفحص المكتملة: <b>{tracker['scans_completed_this_week']}</b>\n"
                    f"• الوظائف التي تم تقييمها: <b>{tracker['jobs_evaluated_this_week']}</b>\n"
                    f"• التنبيهات المرسلة: <b>{tracker['alerts_sent_this_week']}</b>\n\n"
                    f"البوت يعمل بكفاءة ويبحث عن جديد الوظائف على مدار الساعة."
                    f"{SPARKGEN_FOOTER}"
                )
            else:
                summary_text = (
                    f"<b>SparkJobs Weekly Activity Report</b>\n\n"
                    f"• Scans completed: <b>{tracker['scans_completed_this_week']}</b>\n"
                    f"• Jobs evaluated: <b>{tracker['jobs_evaluated_this_week']}</b>\n"
                    f"• Alerts sent: <b>{tracker['alerts_sent_this_week']}</b>\n\n"
                    f"The bot is running smoothly, scanning for new job postings 24/7."
                    f"{SPARKGEN_FOOTER}"
                )
            sent = send_telegram_message(bot_token, chat_id, summary_text)
            if sent:
                tracker["scans_completed_this_week"] = 0
                tracker["jobs_evaluated_this_week"] = 0
                tracker["alerts_sent_this_week"] = 0
                tracker["last_summary_sent"] = datetime.now().isoformat()
                save_status_tracker(tracker)
    except Exception as e:
        print(f"Error executing weekly summary routine: {e}")

    print("=== Scan Cycle Completed ===")

if __name__ == "__main__":
    # Create required data directories locally
    os.makedirs(CVS_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    run_scanner()
