# SparkJobs Engine v2.4.2 - Ubuntu 24.04 LTS CI Runner Allocation & Universal Update Alerts
import os
import sys
import json
import random
import time
import re
import hashlib
from collections import Counter
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    get_base_dir, get_config_path, get_seen_jobs_path, get_status_tracker_path,
    get_cvs_dir, get_cover_letter_path, get_jobs_history_path,
    load_config, load_status_tracker, save_status_tracker
)
from title_matcher import is_title_relevant
from update_checker import check_for_updates
from history_writer import append_to_history


def evaluate_single_job(job, cv_text, gemini_key, min_score, cover_letter, years_exp, requires_visa=False, target_country=""):
    """Evaluates fraud detection and AI match score concurrently, checking visa restriction if required."""
    fraud_result = analyze_job_for_fraud(job)
    if fraud_result.get("risk_level") == "High":
        return {"job": job, "is_scam": True, "ai_result": None, "fraud_result": fraud_result}
    
    ai_result = analyze_job_match(
        cv_text=cv_text,
        job_title=job["title"],
        job_desc=job["description"],
        api_key=gemini_key,
        min_match_score=min_score,
        cover_letter=cover_letter,
        years_exp=years_exp,
        requires_visa=requires_visa,
        target_country=target_country
    )
    if fraud_result.get("is_suspicious"):
        ai_result["risk_level"] = fraud_result["risk_level"]
        ai_result["risk_reason"] = ", ".join(fraud_result["reasons"])
        
    return {"job": job, "is_scam": False, "ai_result": ai_result, "fraud_result": fraud_result}


def run_scanner():
    """
    Orchestrator for the periodic job scan with Smart Dual-Pacing and Parallel AI.
    """
    cycle_start_time = time.time()
    print(f"=== Starting SparkJobs Scan Cycle: {datetime.now().isoformat()} ===")
    config = load_config()

    if not config:
        print("FATAL: Config is empty or corrupted. Aborting scan cycle.")
        return

    sentinel_path = os.path.join(get_base_dir(), "data", ".config_corrupted")
    if os.path.exists(sentinel_path):
        try:
            bot_tok = config.get("telegram_bot_token", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
            c_id = config.get("telegram_chat_id", "") or os.environ.get("TELEGRAM_CHAT_ID", "")
            if bot_tok and c_id:
                err_msg = "⚠️ <b>SparkJobs Alert:</b> Your `data/config.json` file appears corrupted. Scanning aborted."
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
    
    if not bot_token or not chat_id:
        print("FATAL: Missing Telegram bot_token or chat_id. Aborting scan cycle.")
        return

    tracker = load_status_tracker()
    tracker["last_scan_time"] = datetime.now().isoformat()

    # 1. Smart Dual-Pacing & Monthly Usage Management
    current_month_str = datetime.utcnow().strftime("%Y-%m")
    if tracker.get("billing_cycle_month") != current_month_str:
        print(f"[Cycle] New billing cycle detected ({current_month_str}). Resetting monthly minutes counter.")
        tracker["billing_cycle_month"] = current_month_str
        tracker["monthly_minutes_used"] = 0.0
        tracker["monthly_runs_count"] = 0
        save_status_tracker(tracker)

    monthly_minutes = tracker.get("monthly_minutes_used", 0.0)
    last_scan_iso = tracker.get("last_successful_scan_time")

    # If monthly usage >= 1,500 min, enforce strict 1-hour interval (fast-exit if < 55m elapsed)
    if monthly_minutes >= 1500 and last_scan_iso:
        try:
            last_scan_dt = datetime.fromisoformat(last_scan_iso.replace("Z", ""))
            elapsed_min = (datetime.utcnow() - last_scan_dt).total_seconds() / 60.0
            if elapsed_min < 55.0:
                print(f"⏳ Adaptive Pacing Active (Monthly usage: {monthly_minutes:.1f}m >= 1500m).")
                print(f"Paced to 1-hour interval. Last scan was {elapsed_min:.1f}m ago. Fast-exiting in 2 seconds.")
                return
        except Exception as pe:
            print(f"Pacing check error: {pe}")

    seen_jobs = load_seen_jobs(get_seen_jobs_path())

    cover_letter = ""
    cover_letter_path = get_cover_letter_path()
    if os.path.exists(cover_letter_path):
        try:
            with open(cover_letter_path, "r", encoding="utf-8") as f:
                cover_letter = f.read().strip()
        except Exception as e:
            print(f"Error reading cover letter: {e}")

    global_search = config.get("global_search", {})
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
    tracker["scans_completed_this_week"] = tracker.get("scans_completed_this_week", 0) + 1

    scam_jobs_skipped = 0
    total_cycle_jobs = 0
    total_cycle_alerts = 0
    all_missing_keywords = []
    job_sources_count = {}
    match_scores = []
    newly_evaluated_jobs = []

    cv_text = get_cv_text(cv_version)
    if cv_text is None or len(cv_text.strip()) < 150:
        warning_type = "missing" if cv_text is None else "scanned"
        tracker_key = f"cv_warning_sent_{warning_type}"
        if not tracker.get(tracker_key, False):
            print(f"Warning: CV is {warning_type}. Sending warning notification via Telegram...")
            if language == "ar":
                cv_warning_msg = "⚠️ <b>تنبيه من SparkJobs:</b> يرجى رفع ملف السيرة الذاتية (CV) من لوحة التحكم لتفعيل التصفية الذكية."
            else:
                cv_warning_msg = "⚠️ <b>SparkJobs Warning:</b> Please upload a valid resume from your dashboard to enable AI matching."
            send_telegram_message(bot_token, chat_id, cv_warning_msg + SPARKGEN_FOOTER)
            tracker[tracker_key] = True

    dorks_executed = set()
    for tc in active_countries:
        country_name = tc.get("country", "Worldwide")
        remote_only = tc.get("remote_only", False)
        min_score = tc.get("min_match_score", 65)
        requires_visa = tc.get("requires_visa", False)

        print(f"\n--- Scanning Location: {country_name} (Min Score: {min_score}%, Visa Needed: {requires_visa}) ---")

        for title in job_titles:
            if country_name.lower() in ["worldwide", "remote", "global"]:
                location = "Remote"
                is_remote_flag = True
            else:
                location = country_name
                is_remote_flag = remote_only

            should_run_dorks = title not in dorks_executed
            if should_run_dorks:
                dorks_executed.add(title)

            print(f"Scanning for '{title}' in '{location}' (Remote: {is_remote_flag}, ATS Dorks: {should_run_dorks})...")
            
            jobs = run_all_scrapes(
                title, location, scraperapi_key,
                hours_old=24, is_remote=is_remote_flag,
                seen_jobs=seen_jobs, include_ats_dorks=should_run_dorks
            )

            
            # Step 1: Pre-filter candidate jobs that are un-seen and match keyword rules
            candidate_jobs = []
            for job in jobs:
                try:
                    job_id = job["id"]
                    job_title = job.get("title", "")
                    job_company = job.get("company", "")
                    job_url = job.get("url", "")
                    if is_job_seen(seen_jobs, job_id, title=job_title, company=job_company, url=job_url):
                        continue
                    
                    should_exclude = False
                    if exclude_keywords:
                        job_title_lower = job_title.lower()
                        job_desc_lower = job.get("description", "").lower()
                        job_company_lower = job_company.lower()
                        for kw in exclude_keywords:
                            kw_clean = kw.strip().lower()
                            if not kw_clean:
                                continue
                            kw_escaped = re.escape(kw_clean)
                            start_b = r'\b' if kw_clean[0].isalnum() else ''
                            end_b = r'\b' if kw_clean[-1].isalnum() else ''
                            kw_pattern = re.compile(rf'{start_b}{kw_escaped}{end_b}')
                            if (kw_pattern.search(job_title_lower) or kw_pattern.search(job_desc_lower) 
                                    or kw_pattern.search(job_company_lower)):
                                should_exclude = True
                                break
                    
                    if should_exclude:
                        mark_job_as_seen(seen_jobs, job_id, job_title, job_company, url=job_url)
                        continue

                    if not is_title_relevant(job_title, job_titles):
                        mark_job_as_seen(seen_jobs, job_id, job_title, job_company, url=job_url)
                        continue

                    candidate_jobs.append(job)
                except Exception as filter_err:
                    print(f"Error filtering job: {filter_err}")
            
            print(f"Discovered {len(candidate_jobs)} new un-seen candidate jobs for '{title}' in '{location}'.")

            # Step 2: Parallel Batch Evaluation with Gemini AI & Fraud Detector
            if candidate_jobs:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    eval_futures = [
                        executor.submit(evaluate_single_job, j, cv_text, gemini_key, min_score, cover_letter, years_exp, requires_visa, country_name)
                        for j in candidate_jobs
                    ]
                    
                    for future in as_completed(eval_futures):
                        try:
                            res = future.result()
                            job = res["job"]
                            job_id = job["id"]
                            
                            if res["is_scam"]:
                                print(f"Skipping High Risk/Scam job: {job['title']} at {job.get('company')}")
                                mark_job_as_seen(seen_jobs, job_id, job["title"], job["company"], url=job.get("url", ""))
                                scam_jobs_skipped += 1
                                continue
                                
                            ai_result = res["ai_result"]
                            total_cycle_jobs += 1
                            tracker["jobs_evaluated_this_week"] = tracker.get("jobs_evaluated_this_week", 0) + 1
                            
                            source = job.get("source", "Unknown")
                            job_sources_count[source] = job_sources_count.get(source, 0) + 1
                            
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
                                    total_cycle_alerts += 1
                                    tracker["alerts_sent_this_week"] = tracker.get("alerts_sent_this_week", 0) + 1
                                    time.sleep(random.uniform(0.5, 1.2))
                            
                            mark_job_as_seen(seen_jobs, job_id, job["title"], job["company"], url=job.get("url", ""))
                        except Exception as eval_err:
                            print(f"Error in parallel AI eval: {eval_err}")

    # Single persistence write to seen_jobs database at the end of scan cycle
    seen_jobs = cleanup_old_jobs(seen_jobs)
    save_seen_jobs(get_seen_jobs_path(), seen_jobs)

    # Report Aggregated Telemetry Ping
    try:
        top_kws = [kw for kw, _ in Counter(all_missing_keywords).most_common(10)]
        top_sources = [{"source": s, "count": c} for s, c in job_sources_count.items()]
        avg_score = round(sum(match_scores) / len(match_scores), 2) if match_scores else 0
        
        telemetry_url = os.environ.get("SPARKJOBS_TELEMETRY_URL", "https://sparkgen-backend.vercel.app/api/jobs/telemetry/ping")
        payload = {
            "telegram_chat_id": str(chat_id) if chat_id else "anonymous",
            "jobs_evaluated": total_cycle_jobs,
            "scams_detected": scam_jobs_skipped,
            "alerts_sent": total_cycle_alerts,
            "avg_match_score": avg_score,
            "top_missing_kws": top_kws,
            "top_job_sources": top_sources
        }
        ping_secret = os.environ.get("SPARKJOBS_PING_SECRET", "")
        requests.post(telemetry_url, json=payload, headers={"x-ping-secret": ping_secret}, timeout=10)
    except Exception as telemetry_err:
        print(f"Telemetry report non-blocking error: {telemetry_err}")

    if scam_jobs_skipped > 0:
        if language == "ar":
            scam_msg = f"⚠️ <b>SparkJobs:</b> تم تصفية وتخطي {scam_jobs_skipped} وظيفة مشبوهة/احتيالية لحماية خصوصيتك."
        else:
            scam_msg = f"⚠️ <b>SparkJobs:</b> Automatically filtered and skipped {scam_jobs_skipped} suspicious/scam jobs."
        send_telegram_message(bot_token, chat_id, scam_msg + SPARKGEN_FOOTER)

    send_weekly_summary(bot_token, chat_id, tracker, total_cycle_jobs, total_cycle_alerts, language)
    check_for_updates(bot_token, chat_id, tracker, language)
    append_to_history(newly_evaluated_jobs)

    # Update execution duration and save tracker state
    elapsed_cycle_minutes = (time.time() - cycle_start_time) / 60.0
    tracker["monthly_minutes_used"] = round(tracker.get("monthly_minutes_used", 0.0) + max(elapsed_cycle_minutes, 0.4), 2)
    tracker["monthly_runs_count"] = tracker.get("monthly_runs_count", 0) + 1
    tracker["last_successful_scan_time"] = datetime.utcnow().isoformat()
    save_status_tracker(tracker)

    print(f"=== Scan Cycle Completed in {elapsed_cycle_minutes * 60.0:.1f}s (Monthly used: {tracker['monthly_minutes_used']:.1f}m) ===")


if __name__ == "__main__":
    os.makedirs(get_cvs_dir(), exist_ok=True)
    os.makedirs(os.path.join(get_base_dir(), "data"), exist_ok=True)
    run_scanner()
