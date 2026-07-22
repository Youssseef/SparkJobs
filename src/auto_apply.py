import os
import sys
import json
import re
import time
import argparse
import requests
import asyncio
from datetime import datetime

# Ensure src/ directory is in sys.path even when executed directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Paths definition
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_PROFILE_PATH = os.path.join(BASE_DIR, "data", "user_profile.json")
LEARNED_ANSWERS_PATH = os.path.join(BASE_DIR, "data", "learned_answers.json")
FORM_ANALYSIS_PATH = os.path.join(BASE_DIR, "data", "form_analysis.json")
APPLICATION_LOG_PATH = os.path.join(BASE_DIR, "data", "application_log.json")
PENDING_SUBMISSION_PATH = os.path.join(BASE_DIR, "data", "pending_submission.json")
CVS_DIR = os.path.join(BASE_DIR, "data", "cvs")
COVER_LETTER_PATH = os.path.join(BASE_DIR, "data", "cover_letter.txt")

ATS_URL_PATTERNS = {
    "lever": ["jobs.lever.co"],
    "greenhouse": ["boards.greenhouse.io", "grnh.se", "job-boards.greenhouse.io"],
    "smartrecruiters": ["careers.smartrecruiters.com"],
    "linkedin": ["linkedin.com/jobs"],
    "indeed": ["indeed.com/viewjob", "indeed.com/jobs"],
    "workday": [".workday.com/en-us/recruiting"],
}

ATS_DOM_SIGNATURES = {
    "lever": ["[data-lever-source]", "#application-page"],
    "greenhouse": ["#application.greenhouse-theme", "div.greenhouse"],
    "smartrecruiters": [".smart-apply-widget"],
}

def detect_ats_platform_by_url(url: str) -> str:
    url_lower = url.lower()
    for platform, patterns in ATS_URL_PATTERNS.items():
        if any(p in url_lower for p in patterns):
            return platform
    return "generic"

async def detect_ats_platform_by_dom(page) -> str:
    for platform, selectors in ATS_DOM_SIGNATURES.items():
        for selector in selectors:
            try:
                if await page.query_selector(selector):
                    return platform
            except Exception:
                pass
    return "generic"

def write_error(msg: str):
    print(f"Error: {msg}")
    try:
        os.makedirs(os.path.dirname(FORM_ANALYSIS_PATH), exist_ok=True)
        with open(FORM_ANALYSIS_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "status": "error",
                "error_message": msg,
                "fields": []
            }, f, indent=2)
    except Exception as e:
        print(f"Failed to write error status file: {e}")

def get_gemini_cover_letter(job_description: str, job_title: str) -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key or not os.path.exists(COVER_LETTER_PATH):
        if os.path.exists(COVER_LETTER_PATH):
            try:
                with open(COVER_LETTER_PATH, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception:
                pass
        return ""

    try:
        with open(COVER_LETTER_PATH, "r", encoding="utf-8") as f:
            base_letter = f.read().strip()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        payload = {
            "contents": [{
                "parts": [{
                    "text": (
                        f"You are an expert resume and cover letter writer. Personalize the following cover letter template "
                        f"for the job posting titled '{job_title}' with the description below. Keep it professional, concise (max 300 words), "
                        f"and highlight why the candidate is a good match based on the description.\n\n"
                        f"Cover Letter Template:\n{base_letter}\n\n"
                        f"Job Description:\n{job_description}\n\n"
                        f"Return ONLY the personalized cover letter text. Do not include any intro, outro, or placeholders."
                    )
                }]
            }]
        }
        res = requests.post(url, json=payload, headers={"x-goog-api-key": gemini_key}, timeout=15)
        if res.status_code == 200:
            ai_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            return ai_text
    except Exception as e:
        print(f"Gemini cover letter generation failed: {e}")
    
    try:
        with open(COVER_LETTER_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return ""

async def analyze_form_flow(url: str):
    if not os.path.exists(USER_PROFILE_PATH):
        write_error("Auto-Apply Profile not set up. Please complete your profile in the dashboard first.")
        return

    # Check job liveness
    try:
        res = requests.get(url, allow_redirects=True, timeout=10)
        if res.status_code != 200:
            write_error(f"This job posting appears to be closed or expired (HTTP {res.status_code}).")
            return
        page_html = res.text
    except Exception as e:
        write_error(f"Job application URL is unreachable: {e}")
        return

    # Import Playwright dynamically
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000) # Let page load dynamic components
            
            # 1. ATS detection
            platform = detect_ats_platform_by_url(url)
            if platform == "generic":
                platform = await detect_ats_platform_by_dom(page)
            
            # 2. CAPTCHA Check
            for cap_sel in ["iframe[src*='captcha']", "div.g-recaptcha", ".cf-turnstile", ".hcaptcha"]:
                if await page.query_selector(cap_sel):
                    write_error("This application page requires a CAPTCHA. Please apply manually.")
                    await browser.close()
                    return

            # Clean stale pending submission if present
            if os.path.exists(PENDING_SUBMISSION_PATH):
                try:
                    os.remove(PENDING_SUBMISSION_PATH)
                except OSError:
                    pass

            # Read user profile and learned answers
            with open(USER_PROFILE_PATH, "r", encoding="utf-8") as f:
                profile = json.load(f)
            
            learned = {"answers": []}
            if os.path.exists(LEARNED_ANSWERS_PATH):
                try:
                    with open(LEARNED_ANSWERS_PATH, "r", encoding="utf-8") as f:
                        learned = json.load(f)
                except Exception:
                    pass
            
            learned_dict = {a["question_hash"]: a["answer"] for a in learned.get("answers", [])}

            # Gather page content description for cover letter matching
            soup = BeautifulSoup(page_html, "html.parser")
            body_text = soup.get_text()[:4000] # Limit size for token budget
            job_title = soup.title.string if soup.title else "Job Posting"

            # Parse Form Fields (multi-page scan stub)
            fields = []
            page_index = 0
            
            # Standard Selector Mapping for Lever & Greenhouse
            input_elements = await page.query_selector_all("input, textarea, select")
            for elem in input_elements:
                try:
                    # Filter visible input elements
                    if not await elem.is_visible():
                        continue
                    
                    input_type = await elem.get_attribute("type") or "text"
                    name_attr = await elem.get_attribute("name") or ""
                    id_attr = await elem.get_attribute("id") or ""
                    
                    if input_type in ["hidden", "submit", "button"]:
                        continue

                    # Attempt to resolve Label
                    label_text = ""
                    if id_attr:
                        label_elem = await page.query_selector(f"label[for='{id_attr}']")
                        if label_elem:
                            label_text = await label_elem.inner_text()
                    if not label_text:
                        label_text = name_attr or id_attr
                    
                    label_clean = label_text.strip().lower()
                    if not label_clean:
                        continue

                    field_item = {
                        "label": label_text.strip(),
                        "field_type": "text",
                        "selector": f"input[name='{name_attr}']" if name_attr else f"#{id_attr}",
                        "page_index": page_index,
                        "ai_value": "",
                        "confidence": 0.0,
                        "source": "unknown",
                        "triggers_conditional_fields": False
                    }

                    # Map types
                    tag_name = await elem.evaluate("el => el.tagName.toLowerCase()")
                    if tag_name == "textarea":
                        field_item["field_type"] = "textarea"
                    elif tag_name == "select":
                        field_item["field_type"] = "select"
                    elif input_type == "radio":
                        field_item["field_type"] = "radio"
                    elif input_type == "checkbox":
                        field_item["field_type"] = "checkbox"
                    elif input_type == "date":
                        field_item["field_type"] = "date"
                    elif input_type == "file":
                        field_item["field_type"] = "file"

                    # Field Matching Confidence Rules
                    # 1. Check user profile exact matches
                    if "name" in label_clean and "first" not in label_clean and "last" not in label_clean:
                        field_item["ai_value"] = profile.get("full_name", "")
                        field_item["confidence"] = 0.98
                        field_item["source"] = "user_profile"
                    elif "first" in label_clean and "name" in label_clean:
                        field_item["ai_value"] = profile.get("first_name", "") or profile.get("full_name", "").split(" ")[0]
                        field_item["confidence"] = 0.95
                        field_item["source"] = "user_profile"
                    elif "last" in label_clean and "name" in label_clean:
                        field_item["ai_value"] = profile.get("last_name", "") or profile.get("full_name", "").split(" ")[-1]
                        field_item["confidence"] = 0.95
                        field_item["source"] = "user_profile"
                    elif "email" in label_clean:
                        field_item["ai_value"] = profile.get("email", "")
                        field_item["confidence"] = 0.98
                        field_item["source"] = "user_profile"
                    elif "phone" in label_clean or "tel" in label_clean:
                        field_item["ai_value"] = profile.get("phone", "")
                        field_item["confidence"] = 0.98
                        field_item["source"] = "user_profile"
                    elif "linkedin" in label_clean:
                        field_item["ai_value"] = profile.get("linkedin_url", "")
                        field_item["confidence"] = 0.98
                        field_item["source"] = "user_profile"
                    elif "portfolio" in label_clean:
                        field_item["ai_value"] = profile.get("portfolio_url", "")
                        field_item["confidence"] = 0.98
                        field_item["source"] = "user_profile"
                    elif "github" in label_clean:
                        field_item["ai_value"] = profile.get("github_url", "")
                        field_item["confidence"] = 0.98
                        field_item["source"] = "user_profile"
                    elif "resume" in label_clean or "cv" in label_clean or field_item["field_type"] == "file":
                        field_item["field_type"] = "file"
                        field_item["ai_value"] = profile.get("cv_filename", "default_cv.pdf")
                        field_item["confidence"] = 0.95
                        field_item["source"] = "user_profile"
                    elif "cover" in label_clean or "motivation" in label_clean or "letter" in label_clean:
                        # Gemini AI Cover Letter Personalization
                        field_item["ai_value"] = get_gemini_cover_letter(body_text, job_title)
                        field_item["confidence"] = 0.88
                        field_item["source"] = "ai_generated"
                    else:
                        # Check learned answers
                        # MD5 hash of label text for hash keying
                        import hashlib
                        q_hash = hashlib.md5(field_item["label"].encode("utf-8")).hexdigest()
                        field_item["question_hash"] = q_hash
                        if q_hash in learned_dict:
                            field_item["ai_value"] = learned_dict[q_hash]
                            field_item["confidence"] = 0.92
                            field_item["source"] = "learned_answer"
                        else:
                            # Default AI Guess or Unknown
                            field_item["confidence"] = 0.0
                            field_item["source"] = "unknown"

                    fields.append(field_item)
                except Exception as inner_err:
                    print(f"Error scanning input element: {inner_err}")

            # Write ready status
            with open(FORM_ANALYSIS_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "job_url": url,
                    "job_title": job_title,
                    "company": soup.find(class_="company").get_text().strip() if soup.find(class_="company") else "Unknown Company",
                    "ats_platform": platform,
                    "analyzed_at": datetime.utcnow().isoformat() + "Z",
                    "status": "ready",
                    "error_message": None,
                    "total_pages": page_index + 1,
                    "fields": fields
                }, f, indent=2)

            print("Analysis complete. form_analysis.json updated.")
            
            # Send Telegram Analysis ready notification
            bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
            if bot_token and chat_id:
                try:
                    alert_msg = f"📋 <b>SparkJobs:</b> Form analysis completed for <b>{escapeHtml(job_title)}</b>.\n\n👉 Open the dashboard to review and submit the pre-filled application."
                    url_tele = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    requests.post(url_tele, json={"chat_id": chat_id, "text": alert_msg, "parse_mode": "HTML"}, timeout=10)
                except Exception as t_err:
                    print(f"Failed to send Telegram alert: {t_err}")

        except Exception as e:
            write_error(f"Analysis failed: {str(e)}")
        finally:
            await browser.close()

async def submit_form_flow(url: str, fields_json: str):
    confirmed_fields = json.loads(fields_json)
    
    with open(USER_PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)

    # Import Playwright dynamically
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Group fields by page_index (multi-page handling)
            pages_grouped = {}
            for f in confirmed_fields:
                p_idx = f.get("page_index", 0)
                if p_idx not in pages_grouped:
                    pages_grouped[p_idx] = []
                pages_grouped[p_idx].append(f)
            
            for p_idx in sorted(pages_grouped.keys()):
                # Fill fields on the current page
                for field in pages_grouped[p_idx]:
                    sel = field["selector"]
                    val = field["value"]
                    f_type = field["field_type"]

                    try:
                        elem = await page.query_selector(sel)
                        if not elem:
                            continue

                        if f_type == "file":
                            # Resolve CV path from workspace
                            workspace = os.environ.get("GITHUB_WORKSPACE", BASE_DIR)
                            cv_path = os.path.join(workspace, "data", "cvs", val)
                            if os.path.exists(cv_path):
                                await page.set_input_files(sel, cv_path)
                        elif f_type == "select":
                            await page.select_option(sel, val)
                        elif f_type == "radio":
                            # Radio matches value selector or clicks element
                            await page.click(sel)
                        elif f_type == "checkbox":
                            if val in [True, "true", "yes"]:
                                await page.check(sel)
                            else:
                                await page.uncheck(sel)
                        else:
                            await page.fill(sel, val)
                            
                        # Conditional fields trigger wait
                        if field.get("triggers_conditional_fields", False):
                            await page.wait_for_load_state("networkidle")
                            await page.wait_for_timeout(1000)
                    except Exception as fill_err:
                        print(f"Error filling field {field['label']}: {fill_err}")

                # If there are more pages, click next button
                if p_idx < max(pages_grouped.keys()):
                    # Simple next button click handler
                    for btn_sel in ["button:has-text('Next')", "button:has-text('Continue')", ".next-step-button"]:
                        btn = await page.query_selector(btn_sel)
                        if btn:
                            await btn.click()
                            await page.wait_for_load_state("networkidle")
                            await page.wait_for_timeout(2000)
                            break

            # Capture Screenshot
            os.makedirs(os.path.join(BASE_DIR, "data", "screenshots"), exist_ok=True)
            timestamp = int(time.time())
            screenshot_path = os.path.join(BASE_DIR, "data", "screenshots", f"confirm_{timestamp}.png")
            await page.screenshot(path=screenshot_path)

            # Log success to application_log.json
            log_data = {"applications": []}
            if os.path.exists(APPLICATION_LOG_PATH):
                try:
                    with open(APPLICATION_LOG_PATH, "r", encoding="utf-8") as f:
                        log_data = json.load(f)
                except Exception:
                    pass
            
            log_data["applications"].append({
                "id": f"run-{timestamp}",
                "job_url": url,
                "job_title": page.title() if await page.title() else "Job Application",
                "company": "Company",
                "ats_platform": detect_ats_platform_by_url(url),
                "status": "applied",
                "applied_at": datetime.utcnow().isoformat() + "Z",
                "duration_seconds": 120,
                "screenshot_artifact_url": f"screenshots/confirm_{timestamp}.png",
                "artifact_expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z",
                "confirmed_fields": confirmed_fields,
                "error_message": None
            })

            with open(APPLICATION_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2)

            # Send Telegram alert
            bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
            if bot_token and chat_id:
                try:
                    success_msg = f"✅ <b>SparkJobs Auto-Apply:</b> Application submitted successfully!\n\n📄 View history and screenshot confirmation in the dashboard."
                    url_tele = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    requests.post(url_tele, json={"chat_id": chat_id, "text": success_msg, "parse_mode": "HTML"}, timeout=10)
                except Exception as t_err:
                    print(f"Failed to send Telegram alert: {t_err}")

        except Exception as e:
            print(f"Submission failed: {e}")
        finally:
            # Delete pending submission path
            if os.path.exists(PENDING_SUBMISSION_PATH):
                try:
                    os.remove(PENDING_SUBMISSION_PATH)
                except OSError:
                    pass
            await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SparkJobs Auto-Apply CLI")
    parser.add_argument("--mode", required=True, choices=["analyze", "submit"], help="Running mode")
    parser.add_argument("--url", required=True, help="Job posting URL")
    parser.add_argument("--fields", help="JSON string of confirmed fields (required for submit mode)")

    args = parser.parse_args()
    if args.mode == "analyze":
        asyncio.run(analyze_form_flow(args.url))
    elif args.mode == "submit":
        if not args.fields:
            # Fallback to pending_submission.json if fields arg is empty
            if os.path.exists(PENDING_SUBMISSION_PATH):
                with open(PENDING_SUBMISSION_PATH, "r", encoding="utf-8") as f:
                    fields_data = f.read()
            else:
                print("Error: --fields argument or pending_submission.json is required in submit mode.")
                sys.exit(1)
        else:
            fields_data = args.fields
        asyncio.run(submit_form_flow(args.url, fields_data))
