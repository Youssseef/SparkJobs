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
    Loads text from CV file. Supports .pdf, .docx, and .txt.
    Tries fallback options if the configured version is missing.
    """
    versions_to_try = []
    if cv_version:
        versions_to_try.append(cv_version)
    if "default_cv" not in versions_to_try:
        versions_to_try.append("default_cv")

    for ver in versions_to_try:
        # Check for PDF
        pdf_path = os.path.join(CVS_DIR, f"{ver}.pdf")
        if os.path.exists(pdf_path):
            return extract_text_from_pdf(pdf_path)
            
        # Check for DOCX
        docx_path = os.path.join(CVS_DIR, f"{ver}.docx")
        if os.path.exists(docx_path):
            return extract_text_from_docx(docx_path)
            
        # Check for TXT fallback
        txt_path = os.path.join(CVS_DIR, f"{ver}.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Error reading txt CV {txt_path}: {e}")
                
    print(f"Warning: CV file not found for versions {versions_to_try} in {CVS_DIR}")
    return ""

def get_role_core(title: str, fillers: set) -> str:
    """
    Extracts the defining core role word from a job title by checking from the end.
    e.g., "Product Designer" -> "designer"
          "UX/UI Developer" -> "developer"
          "Senior Frontend Architect" -> "architect"
    """
    import re
    words = re.findall(r'\b\w+\b', title.lower())
    for word in reversed(words):
        if word not in fillers and len(word) > 3:
            return word
    return words[-1] if words else ""

def is_title_relevant(job_title: str, target_titles: list) -> bool:
    """
    Performs case-insensitive semantic relevance checking.
    Ensures that the job title is relevant to at least one target title by verifying
    direct substring match or overlap of the target's core role word.
    """
    if not target_titles:
        return True
    
    fillers = {
        "senior", "junior", "lead", "staff", "principal", "remote", "hybrid", "onsite", 
        "jobs", "job", "intern", "associate", 
        "middle", "mid", "expert", "specialist", "professional", "director", "vp", "head"
    }
    
    for target in target_titles:
        target_lower = target.lower()
        job_lower = job_title.lower()
        
        # 1. Direct substring match (fast path)
        if target_lower in job_lower:
            return True
            
        # 2. Core role word matching (stops cross-field contamination, e.g. Designer vs Manager)
        core = get_role_core(target_lower, fillers)
        if core and core in job_lower:
            return True
            
    return False

def check_for_updates(bot_token: str, chat_id: str, tracker: dict, language: str):
    """
    Checks the remote template repository for new releases or main updates
    by comparing git hash objects. Sends a single Telegram alert if an update is found.
    """
    try:
        import urllib.request
        import urllib.error
        import hashlib
        
        main_py_path = os.path.join(BASE_DIR, "src", "main.py")
        if not os.path.exists(main_py_path):
            return
            
        with open(main_py_path, "rb") as f:
            local_data = f.read()
        local_header = f"blob {len(local_data)}\0".encode('utf-8')
        sha1 = hashlib.sha1()
        sha1.update(local_header)
        sha1.update(local_data)
        local_sha = sha1.hexdigest()
        
        template_owner = "Youssseef"
        template_repo = "SparkJobs"
        url = f"https://api.github.com/repos/{template_owner}/{template_repo}/contents/src/main.py"
        
        headers = {'User-Agent': 'SparkJobs-Bot'}
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if github_token:
            headers['Authorization'] = f'token {github_token}'
            
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            meta = json.loads(response.read().decode('utf-8'))
            template_sha = meta.get("sha", "")
            
        if template_sha and local_sha != template_sha:
            if tracker.get("last_update_alert_sha") != template_sha:
                print("New bot code template update detected! Sending Telegram notification...")
                if language == "ar":
                    alert_msg = (
                        f"⚠️ <b>تحديث جديد متوفر لكود البوت!</b>\n\n"
                        f"هناك إصدار جديد يحتوي على ميزات وتحسينات لـ SparkJobs.\n"
                        f"يرجى الذهاب للوحة التحكم الخاصة بك والضغط على زر <b>\"تحديث كود البوت\"</b> لتحديث ملفاتك تلقائياً."
                        f"{SPARKGEN_FOOTER}"
                    )
                else:
                    alert_msg = (
                        f"⚠️ <b>New Bot Update Available!</b>\n\n"
                        f"A new template version of SparkJobs is available with bug fixes and enhancements.\n"
                        f"Please go to your dashboard settings and click <b>\"Sync Bot Code\"</b> to update automatically."
                        f"{SPARKGEN_FOOTER}"
                    )
                sent = send_telegram_message(bot_token, chat_id, alert_msg)
                if sent:
                    tracker["last_update_alert_sha"] = template_sha
                    save_status_tracker(tracker)
    except Exception as update_err:
        print(f"Failed to check for template updates (non-blocking): {update_err}")

def run_scanner():
    """
    Orchestrator for the periodic job scan.
    """
    print(f"=== Starting SparkJobs Scan Cycle: {datetime.now().isoformat()} ===")
    config = load_config()
    
    if config.get("paused", False):
        print("Bot is currently paused. Exiting scan cycle.")
        return
        
    gemini_key = config.get("gemini_api_key", "") or os.environ.get("GEMINI_API_KEY", "")
    bot_token = config.get("telegram_bot_token", "") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = config.get("telegram_chat_id", "") or os.environ.get("TELEGRAM_CHAT_ID", "")
    scraperapi_key = config.get("scraperapi_key", "") or os.environ.get("SCRAPERAPI_KEY", "")
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
    total_cycle_jobs = 0
    total_cycle_alerts = 0
    all_missing_keywords = []
    job_sources_count = {}
    match_scores = []

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
            save_status_tracker(tracker)
        print(f"Warning: CV is {warning_type}. Running in no-CV fallback mode.")

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
                try:
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

                    # Strict Title Relevance check (keyword overlap) to prevent wrong field alerts
                    if not is_title_relevant(job.get("title", ""), job_titles):
                        print(f"Skipping off-field job title: {job['title']} at {job['company']} (not matching targets: {job_titles})")
                        mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])
                        continue

                    new_jobs_count += 1
                    total_cycle_jobs += 1
                    tracker["jobs_evaluated_this_week"] += 1
                    
                    # Collect job source telemetry
                    source = job.get("source", "Unknown")
                    job_sources_count[source] = job_sources_count.get(source, 0) + 1
                    
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
                    if match_score > 0:
                        match_scores.append(match_score)
                    
                    # Collect missing keywords telemetry
                    all_missing_keywords.extend(ai_result.get("missing_keywords", []))
                    
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
                            total_cycle_alerts += 1
                            tracker["alerts_sent_this_week"] += 1
                            mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])
                            time.sleep(random.uniform(1.0, 2.0))
                    else:
                        mark_job_as_seen(SEEN_JOBS_PATH, job_id, job["title"], job["company"])
                except Exception as job_err:
                    print(f"Error processing job '{job.get('title', 'Unknown')}' at '{job.get('company', 'Unknown')}': {job_err}")
                    continue

            print(f"Scrape completed: {new_jobs_count} new postings evaluated. {alerts_sent_count} alerts sent.")
            time.sleep(random.uniform(2.0, 4.0))

    # Run Database cleanup
    cleanup_old_jobs(SEEN_JOBS_PATH)
    save_status_tracker(tracker)

    # ─── Report Aggregated Telemetry Ping ───
    try:
        from collections import Counter
        import requests
        
        # Sort and take top 10 missing keywords
        top_kws = [kw for kw, _ in Counter(all_missing_keywords).most_common(10)]
        
        # Format top job sources
        top_sources = [{"source": s, "count": c} for s, c in job_sources_count.items()]
        
        # Calculate average match score
        avg_score = round(sum(match_scores) / len(match_scores), 2) if match_scores else 0
        
        # Read API URL from environment fallback, standard production is sparkgen-backend.vercel.app
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

    # Check for template updates
    check_for_updates(bot_token, chat_id, tracker, language)

    print("=== Scan Cycle Completed ===")

if __name__ == "__main__":
    # Create required data directories locally
    os.makedirs(CVS_DIR, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    run_scanner()
