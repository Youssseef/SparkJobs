import os
import sys
import json
import random
import time
from collections import Counter
from datetime import datetime, timedelta

# Ensure src/ directory is in sys.path even when executed as `python src/main.py`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from cv_loader import get_cv_text
from scraper import run_all_scrapes
from fraud_detector import analyze_job_for_fraud
from ai_matcher import analyze_job_match
from deduplicator import load_seen_jobs, save_seen_jobs, is_job_seen, mark_job_as_seen, cleanup_old_jobs
from telegram_sender import send_telegram_alert, send_telegram_message, send_weekly_summary, SPARKGEN_FOOTER
from config_loader import (
    BASE_DIR, CONFIG_PATH, SEEN_JOBS_PATH, STATUS_TRACKER_PATH, CVS_DIR, COVER_LETTER_PATH,
    load_config, load_status_tracker, save_status_tracker
)
from title_matcher import is_title_relevant
from update_checker import check_for_updates
from history_writer import append_to_history




def run_scanner():
    """
    Orchestrator for the periodic job scan.
    """
    print(f"=== Starting SparkJobs Scan Cycle: {datetime.now().isoformat()} ===")
    config = load_config()

    # H-02 Fix: Abort scan cycle cleanly if config.json is empty or corrupted
    if not config:
        print("FATAL: Config is empty or corrupted. Aborting scan cycle.")
        return

    # L-05 Fix: Check for config corruption sentinel file and alert user via Telegram
    sentinel_path = os.path.join(BASE_DIR, "data", ".config_corrupted")
    if os.path.exists(sentinel_path):
        try:
            bot_tok = config.get("telegram_bot_token", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
            c_id = config.get("telegram_chat_id", "") or os.environ.get("TELEGRAM_CHAT_ID", "")
            if bot_tok and c_id:
                err_msg = "⚠️ <b>SparkJobs Alert:</b> Your `data/config.json` file appears corrupted or invalid JSON. Scanning aborted to prevent unpredictable behavior. Please check your settings in the dashboard."
                send_telegram_message(bot_tok, c_id, err_msg + SPARKGEN_FOOTER)
            os.remove(sentinel_path)
        except Exception as alert_err:
            print(f"Error handling corrupted config alert: {alert_err}")

    if config.get("paused", False):
        print("Bot is currently paused. Exiting scan cycle.")
        return
        
    gemini_key = config.get("gemini_api_key", "") or os.environ.get("GEMINI_API_KEY", "")
    bot_token = config.get("telegram_bot_token", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = config.get("telegram_chat_id", "") or os.environ.get("TELEGRAM_CHAT_ID", "")
    scraperapi_key = config.get("scraperapi_key", "") or os.environ.get("SCRAPERAPI_KEY", "")
    profiles = config.get("profiles", [])
    language = config.get("language", "ar")
    
    # H-03 Fix: Early exit if bot_token or chat_id are missing to prevent silent quota burn
    if not bot_token or not chat_id:
        print("FATAL: Missing Telegram bot_token or chat_id. Aborting scan cycle.")
        return

    tracker = load_status_tracker()
    tracker["last_scan_time"] = datetime.now().isoformat()

    # Load seen_jobs database ONCE into memory at start of scan cycle
    seen_jobs = load_seen_jobs(SEEN_JOBS_PATH)

    # Load candidate cover letter if exists
    cover_letter = ""
    if os.path.exists(COVER_LETTER_PATH):
        try:
            with open(COVER_LETTER_PATH, "r", encoding="utf-8") as f:
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

    # Normalize target_countries (supports both string lists and dict lists)
    raw_countries = config.get("target_countries", [])
    target_countries = []
    
    if isinstance(raw_countries, list):
        for item in raw_countries:
            if isinstance(item, str):
                target_countries.append({
                    "country": item,
                    "remote_only": False,
                    "requires_visa": False,
                    "min_match_score": 65,
                    "active": True
                })
            elif isinstance(item, dict):
                target_countries.append(item)

    if not target_countries and profiles:
        p = profiles[0]
        for countryId in p.get("countries", []):
            if isinstance(countryId, str):
                # H-10 & M-16 Fix: Null-safe read for job_types/visa_types & check p.get("remote")
                job_types = p.get("job_types") or []
                visa_types = p.get("visa_types") or []
                is_remote = p.get("remote", False) or ("remote" in job_types)
                requires_visa = "sponsor_required" in visa_types
                target_countries.append({
                    "country": countryId,
                    "remote_only": is_remote,
                    "requires_visa": requires_visa,
                    "min_match_score": p.get("min_match_score", 65),
                    "active": p.get("active", True)
                })
            elif isinstance(countryId, dict):
                target_countries.append(countryId)

    if not target_countries:
        print("No target locations configured. Stopping scanner.")
        save_status_tracker(tracker)
        return

    active_countries = [c for c in target_countries if c.get("active", True)]
    print(f"Found {len(active_countries)} active locations out of {len(target_countries)} total locations.")

    # L-02 Fix: Increment scan counter only after verifying active countries exist
    tracker["scans_completed_this_week"] = tracker.get("scans_completed_this_week", 0) + 1

    scam_jobs_skipped = 0
    total_cycle_jobs = 0
    total_cycle_alerts = 0
    all_missing_keywords = []
    job_sources_count = {}
    match_scores = []
    newly_evaluated_jobs = []

    # Load candidate CV
    cv_text = get_cv_text(cv_version)
    if not cv_text or len(cv_text.strip()) < 150:
        warning_type = "missing" if not cv_text else "scanned"
        tracker_key = f"cv_warning_sent_{warning_type}"
        if not tracker.get(tracker_key, False):
            print(f"Warning: CV is {warning_type}. Sending warning notification via Telegram...")
            if language == "ar":
                if warning_type == "missing":
                    cv_warning_msg = (
                        f"⚠️ <b>تنبيه من SparkJobs:</b> لم نتمكن من العثور على ملف السيرة الذاتية (CV) الخاص بك في المستودع.\n\n"
                        f"تم تشغيل البوت في وضع التدفق الكامل (بدون تصفية)، مما يعني أنك ستتلقى جميع الوظائف دون مطابقة AI.\n"
                        f"يرجى رفع ملف السيرة الذاتية بصيغة PDF أو Word من لوحة التحكم."
                    )
                else:
                    cv_warning_msg = (
                        f"⚠️ <b>تنبيه من SparkJobs:</b> السيرة الذاتية المرفوعة فارغة أو تبدو كصورة ممسوحة ضوئياً (Scanned PDF/Image).\n\n"
                        f"لم يتمكن محرك الذكاء الاصطناعي من قراءة النص في ملفك، وتم تفعيل وضع التدفق الكامل مؤقتاً.\n"
                        f"يرجى إعادة رفع السيرة الذاتية كملف نصي قابل للبحث لتفعيل التصفية الذكية."
                    )
            else:
                if warning_type == "missing":
                    cv_warning_msg = (
                        f"⚠️ <b>SparkJobs Warning:</b> Your resume (CV) file could not be found in the repository.\n\n"
                        f"The bot is running in fallback flow-through mode (no AI filtering). You will receive all scraped jobs.\n"
                        f"Please upload a valid PDF or Word resume from your dashboard settings."
                    )
                else:
                    cv_warning_msg = (
                        f"⚠️ <b>SparkJobs Warning:</b> Your uploaded resume appears to be empty or a scanned image (non-searchable PDF).\n\n"
                        f"The AI model cannot extract text from this file, and the bot is running in fallback flow-through mode.\n"
                        f"Please re-upload your resume as a text-searchable PDF, DOCX, or TXT file to enable smart matching."
                    )
            send_telegram_message(bot_token, chat_id, cv_warning_msg + SPARKGEN_FOOTER)
            tracker[tracker_key] = True
            # M-10 Fix: Removed mid-cycle save_status_tracker call (saved once at end of cycle)
        print(f"Warning: CV is {warning_type}. Running in no-CV fallback mode.")

    for tc in active_countries:
        country_name = tc.get("country", "Worldwide")
        remote_only = tc.get("remote_only", False)
        min_score = tc.get("min_match_score", 65)

        print(f"\n--- Scanning Location: {country_name} (Min Score: {min_score}%) ---")

        for title in job_titles:
            location = "Remote" if remote_only else country_name
            print(f"Scanning for '{title}' in '{location}'...")
            
            jobs = run_all_scrapes(title, location, scraperapi_key)
            
            new_jobs_count = 0
            alerts_sent_count = 0
            
            for job in jobs:
                try:
                    job_id = job["id"]
                    
                    if is_job_seen(seen_jobs, job_id):
                        continue
                    
                    should_exclude = False
                    if exclude_keywords:
                        job_title_lower = job.get("title", "").lower()
                        job_desc_lower = job.get("description", "").lower()
                        job_company_lower = job.get("company", "").lower()
                        for kw in exclude_keywords:
                            kw_clean = kw.strip().lower()
                            if not kw_clean:
                                continue
                            kw_pattern = re.compile(rf'\b{re.escape(kw_clean)}\b')
                            if (kw_pattern.search(job_title_lower) or kw_pattern.search(job_desc_lower) 
                                    or kw_pattern.search(job_company_lower)):
                                should_exclude = True
                                break
                    
                    if should_exclude:
                        print(f"Skipping job matching exclusion filter: {job['title']} at {job['company']}")
                        mark_job_as_seen(seen_jobs, job_id, job["title"], job["company"])
                        continue

                    if not is_title_relevant(job.get("title", ""), job_titles):
                        print(f"Skipping off-field job title: {job['title']} at {job['company']} (not matching targets: {job_titles})")
                        mark_job_as_seen(seen_jobs, job_id, job["title"], job["company"])
                        continue

                    new_jobs_count += 1
                    total_cycle_jobs += 1
                    tracker["jobs_evaluated_this_week"] = tracker.get("jobs_evaluated_this_week", 0) + 1
                    
                    source = job.get("source", "Unknown")
                    job_sources_count[source] = job_sources_count.get(source, 0) + 1
                    
                    fraud_result = analyze_job_for_fraud(job)
                    
                    if fraud_result["risk_level"] == "High":
                        print(f"Skipping High Risk/Scam job: {job['title']} at {job['company']}")
                        mark_job_as_seen(seen_jobs, job_id, job["title"], job["company"])
                        scam_jobs_skipped += 1
                        continue
                    
                    ai_result = analyze_job_match(
                        cv_text=cv_text,
                        job_title=job["title"],
                        job_desc=job["description"],
                        api_key=gemini_key,
                        min_match_score=min_score,
                        cover_letter=cover_letter,
                        years_exp=years_exp
                    )
                    
                    if fraud_result["is_suspicious"]:
                        ai_result["risk_level"] = fraud_result["risk_level"]
                        ai_result["risk_reason"] = ", ".join(fraud_result["reasons"])
                    
                    # H-12 Fix: Coerce match_score to integer safely
                    try:
                        match_score = int(ai_result.get("match_score", 0) or 0)
                    except (ValueError, TypeError):
                        match_score = 0

                    newly_evaluated_jobs.append({
                        "id": job_id,
                        "title": job["title"],
                        "company": job.get("company", ""),
                        "location": job.get("location", "Remote"),
                        "url": job["url"],
                        "source": job.get("source", "unknown"),
                        "match_score": match_score
                    })


                    if match_score > 0:
                        match_scores.append(match_score)
                    
                    all_missing_keywords.extend(ai_result.get("missing_keywords") or [])
                    
                    if match_score >= min_score:
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
                            total_cycle_alerts += 1
                            tracker["alerts_sent_this_week"] = tracker.get("alerts_sent_this_week", 0) + 1
                            mark_job_as_seen(seen_jobs, job_id, job["title"], job["company"])
                            time.sleep(random.uniform(1.0, 2.0))
                    else:
                        mark_job_as_seen(seen_jobs, job_id, job["title"], job["company"])
                except Exception as job_err:
                    print(f"Error processing job '{job.get('title', 'Unknown')}' at '{job.get('company', 'Unknown')}': {job_err}")
                    continue

            print(f"Scrape completed: {new_jobs_count} new postings evaluated. {alerts_sent_count} alerts sent.")
            time.sleep(random.uniform(2.0, 4.0))

    # C-01 Fix: Single persistence write to seen_jobs database at the end of scan cycle
    seen_jobs = cleanup_old_jobs(seen_jobs)
    save_seen_jobs(SEEN_JOBS_PATH, seen_jobs)

    # Report Aggregated Telemetry Ping
    try:
        top_kws = [kw for kw, _ in Counter(all_missing_keywords).most_common(10)]
        top_sources = [{"source": s, "count": c} for s, c in job_sources_count.items()]
        avg_score = round(sum(match_scores) / len(match_scores), 2) if match_scores else 0
        
        telemetry_url = os.environ.get("SPARKJOBS_TELEMETRY_URL", "https://sparkgen-backend.vercel.app/api/jobs/telemetry/ping")
        
        payload = {
            "telegram_chat_id": chat_id,
            "jobs_evaluated": total_cycle_jobs,
            "scams_detected": scam_jobs_skipped,
            "alerts_sent": total_cycle_alerts,
            "avg_match_score": avg_score,
            "top_missing_kws": top_kws,
            "top_job_sources": top_sources
        }
        ping_secret = os.environ.get("SPARKJOBS_PING_SECRET", "")
        
        req_res = requests.post(
            telemetry_url,
            json=payload,
            headers={"x-ping-secret": ping_secret},
            timeout=10
        )
        if req_res.status_code == 200:
            print("Telemetry statistics reported successfully.")
        else:
            print(f"Telemetry report returned status code: {req_res.status_code}. Response: {req_res.text}")
    except Exception as telemetry_err:
        print(f"Failed to report telemetry (non-blocking): {telemetry_err}")

    # Send scam summary alert to Telegram if any were filtered
    if scam_jobs_skipped > 0:
        if language == "ar":
            scam_msg = f"⚠️ <b>SparkJobs:</b> تم تصفية وتخطي {scam_jobs_skipped} وظيفة مشبوهة/احتيالية في دورة البحث الحالية لحماية خصوصيتك."
        else:
            scam_msg = f"⚠️ <b>SparkJobs:</b> Automatically filtered and skipped {scam_jobs_skipped} suspicious/scam jobs in this scan cycle to protect your profile."
        send_telegram_message(bot_token, chat_id, scam_msg + SPARKGEN_FOOTER)

    # Check if 7 days have passed since the last summary (delegated helper to maintain Rule 16 <400 lines)
    send_weekly_summary(bot_token, chat_id, tracker, total_cycle_jobs, total_cycle_alerts, language)

    # Check for repository/bot software updates
    check_for_updates(bot_token, chat_id, tracker, language)

    # Append newly evaluated jobs to jobs_history.json
    append_to_history(newly_evaluated_jobs)

    # Consolidated single save for tracker state at end of cycle (M-02, M-10)
    save_status_tracker(tracker)

    print("=== Scan Cycle Completed ===")

if __name__ == "__main__":
    os.makedirs(CVS_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    run_scanner()
