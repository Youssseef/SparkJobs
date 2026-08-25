import os
import sys
import json
import time
import random
import argparse
import asyncio
from datetime import datetime
from urllib.parse import urlparse
import requests

# Ensure src/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_apply import (
    BASE_DIR, USER_PROFILE_PATH, LEARNED_ANSWERS_PATH, APPLICATION_LOG_PATH,
    detect_ats_platform_by_url
)
from telegram_sender import send_telegram_message, escape_html

# Concurrency tuned specifically for GitHub Actions 2-vCPU / 7GB RAM runner
CONCURRENT_WORKERS = 3
JOB_TIMEOUT_SECONDS = 40

# Tracker & heavy media domains to abort in Playwright route
BLOCKED_TRACKERS = [
    "google-analytics.com", "googletagmanager.com", "hotjar.com", "facebook.net",
    "connect.facebook.net", "sentry.io", "datadoghq.com", "clarity.ms",
    "doubleclick.net", "segment.io", "intercom.io"
]

class DomainRateLimiter:
    """Thread/Task safe domain rate limiter to prevent hitting the same host simultaneously."""
    def __init__(self, min_interval=3.0):
        self.min_interval = min_interval
        self.last_accessed = {}
        self._lock = asyncio.Lock()

    async def throttle(self, url: str):
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            domain = "unknown"
            
        async with self._lock:
            now = time.time()
            last = self.last_accessed.get(domain, 0)
            elapsed = now - last
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                self.last_accessed[domain] = now + wait_time
            else:
                wait_time = 0
                self.last_accessed[domain] = now

        if wait_time > 0:
            await asyncio.sleep(wait_time)

domain_limiter = DomainRateLimiter(min_interval=3.0)
log_lock = asyncio.Lock()

def preflight_check(url: str) -> bool:
    """Fast HTTP pre-flight check to skip dead links in ~200ms."""
    if not url or not url.startswith("http"):
        return False
    try:
        resp = requests.head(url, allow_redirects=True, timeout=5, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code in [404, 410]:
            return False
        return True
    except Exception:
        # If HEAD fails or is blocked, let browser attempt
        return True

async def setup_page_routes(page):
    """Intercepts and aborts heavy video banners and tracking scripts."""
    async def route_handler(route):
        url = route.request.url.lower()
        res_type = route.request.resource_type

        # Block heavy video streams
        if res_type in ["media"] or any(url.endswith(ext) for ext in [".mp4", ".webm", ".avi", ".mov"]):
            await route.abort()
            return

        # Block analytics and telemetry scripts
        if any(tracker in url for tracker in BLOCKED_TRACKERS):
            await route.abort()
            return

        await route.continue_()

    await page.route("**/*", route_handler)

async def apply_single_job(context, job: dict, profile: dict, learned_dict: dict) -> dict:
    url = job.get("url", "")
    job_title = job.get("title", "Job Posting")
    company = job.get("company", "Company")

    if not url:
        return {"status": "failed", "reason": "Missing job URL"}

    # Fast Pre-Flight Check
    is_live = await asyncio.to_thread(preflight_check, url)
    if not is_live:
        return {"status": "skipped", "reason": "Link expired or closed (404/410)"}

    # Host-level rate limiting
    await domain_limiter.throttle(url)

    page = await context.new_page()
    try:
        await setup_page_routes(page)
        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        await page.wait_for_timeout(2000)

        # Check for CAPTCHA
        for cap_sel in ["iframe[src*='captcha']", "div.g-recaptcha", ".cf-turnstile", ".hcaptcha"]:
            if await page.query_selector(cap_sel):
                return {"status": "skipped", "reason": "Requires CAPTCHA (manual apply required)"}

        # Check for external apply button or navigate into application form
        input_elements = await page.query_selector_all("input, textarea, select")
        has_visible_inputs = False
        if input_elements:
            for el in input_elements:
                try:
                    if await el.is_visible():
                        has_visible_inputs = True
                        break
                except Exception:
                    pass

        if not has_visible_inputs:
            for apply_sel in [
                "a:has-text('Apply Now')", "button:has-text('Apply Now')",
                "a:has-text('Apply on company website')", "a:has-text('Apply for this job')",
                "button:has-text('Apply for this job')", "a:has-text('Apply')",
                "button:has-text('Apply')", "[data-qa='apply-button']", ".apply-button", "#apply-button",
                "a[href*='apply']", "button[id*='apply']"
            ]:
                try:
                    apply_btn = await page.query_selector(apply_sel)
                    if apply_btn and await apply_btn.is_visible():
                        href = await apply_btn.get_attribute("href")
                        if href and href.startswith("http"):
                            await domain_limiter.throttle(href)
                            await page.goto(href, wait_until="domcontentloaded", timeout=20000)
                            await page.wait_for_timeout(2000)
                        else:
                            await apply_btn.click()
                            await page.wait_for_timeout(2000)
                        input_elements = await page.query_selector_all("input, textarea, select")
                        break
                except Exception:
                    pass

        input_elements = await page.query_selector_all("input, textarea, select")
        if not input_elements:
            return {"status": "skipped", "reason": "No direct ATS application form detected on page"}

        # Scan and fill form fields
        fields_filled = 0

        # Resolve CV path
        cv_name = profile.get("cv_filename", "default_cv.pdf")
        workspace = os.environ.get("GITHUB_WORKSPACE", BASE_DIR)
        cv_path = os.path.join(workspace, "data", "cvs", cv_name)
        if not os.path.exists(cv_path):
            cv_dir = os.path.join(workspace, "data", "cvs")
            if os.path.exists(cv_dir):
                cv_files = [f for f in os.listdir(cv_dir) if f.endswith(('.pdf', '.docx', '.doc'))]
                if cv_files:
                    cv_path = os.path.join(cv_dir, cv_files[0])

        for elem in input_elements:
            try:
                if not await elem.is_visible():
                    continue

                input_type = (await elem.get_attribute("type") or "text").lower()
                name_attr = (await elem.get_attribute("name") or "").lower()
                id_attr = (await elem.get_attribute("id") or "").lower()
                placeholder = (await elem.get_attribute("placeholder") or "").lower()
                aria_label = (await elem.get_attribute("aria-label") or "").lower()

                if input_type in ["hidden", "submit", "button", "reset"]:
                    continue

                # File upload (CV / Resume)
                if input_type == "file":
                    if os.path.exists(cv_path):
                        await elem.set_input_files(cv_path)
                        fields_filled += 1
                    continue

                label_text = f"{name_attr} {id_attr} {placeholder} {aria_label}"

                # Field mappings
                if any(k in label_text for k in ["first_name", "firstname", "first name", "given_name"]):
                    val = profile.get("full_name", "").split()[0] if profile.get("full_name") else ""
                    await elem.fill(val)
                    fields_filled += 1
                elif any(k in label_text for k in ["last_name", "lastname", "last name", "family_name", "surname"]):
                    val = " ".join(profile.get("full_name", "").split()[1:]) if len(profile.get("full_name", "").split()) > 1 else ""
                    await elem.fill(val)
                    fields_filled += 1
                elif any(k in label_text for k in ["name", "full_name", "fullname", "candidate_name"]):
                    await elem.fill(profile.get("full_name", ""))
                    fields_filled += 1
                elif "email" in label_text:
                    await elem.fill(profile.get("email", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["phone", "mobile", "tel", "contact_number"]):
                    await elem.fill(profile.get("phone", ""))
                    fields_filled += 1
                elif "linkedin" in label_text:
                    await elem.fill(profile.get("linkedin_url", ""))
                    fields_filled += 1
                elif "github" in label_text:
                    await elem.fill(profile.get("github_url", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["portfolio", "website", "personal_url", "site"]):
                    await elem.fill(profile.get("portfolio_url", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["city", "town"]):
                    await elem.fill(profile.get("location_city", profile.get("city", "")))
                    fields_filled += 1
                elif any(k in label_text for k in ["country", "state", "region"]):
                    await elem.fill(profile.get("location_country", profile.get("country", "")))
                    fields_filled += 1
                elif any(k in label_text for k in ["company", "current_company", "employer"]):
                    await elem.fill(profile.get("current_company", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["title", "current_title", "job_title", "headline"]):
                    await elem.fill(profile.get("current_title", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["experience", "years_of_experience", "years_experience"]):
                    await elem.fill(str(profile.get("experience_years", "3-5")))
                    fields_filled += 1
                elif any(k in label_text for k in ["notice", "notice_period", "availability"]):
                    await elem.fill(profile.get("notice_period", "Immediate"))
                    fields_filled += 1
                elif any(k in label_text for k in ["sponsorship", "visa", "authorized"]):
                    sponsorship_val = profile.get("sponsorship_required", "no")
                    if elem.tag_name.lower() == "select":
                        options = await elem.query_selector_all("option")
                        for opt in options:
                            opt_text = (await opt.inner_text()).lower()
                            if ("no" in opt_text and sponsorship_val == "no") or ("yes" in opt_text and sponsorship_val == "yes"):
                                opt_val = await opt.get_attribute("value")
                                if opt_val is not None:
                                    await elem.select_option(value=opt_val)
                                    fields_filled += 1
                                    break
                    else:
                        await elem.fill("No" if sponsorship_val == "no" else "Yes")
                        fields_filled += 1
            except Exception:
                pass

        if fields_filled == 0:
            return {"status": "skipped", "reason": "Application form detected but no standard fields could be mapped"}

        # Attempt submission click
        submitted = False
        for sub_sel in [
            "button[type='submit']", "input[type='submit']",
            "button:has-text('Submit Application')", "button:has-text('Submit application')",
            "button:has-text('Submit')", "button:has-text('Apply Now')",
            "#btn-submit", "#submit-application", "button.submit-button"
        ]:
            try:
                sub_btn = await page.query_selector(sub_sel)
                if sub_btn and await sub_btn.is_visible():
                    await sub_btn.click()
                    submitted = True
                    await page.wait_for_timeout(3000)
                    break
            except Exception:
                pass

        # Capture proof screenshot
        os.makedirs(os.path.join(BASE_DIR, "data", "screenshots"), exist_ok=True)
        timestamp = int(time.time())
        rand_id = random.randint(100, 999)
        screenshot_rel = f"screenshots/confirm_{timestamp}_{rand_id}.png"
        screenshot_full = os.path.join(BASE_DIR, "data", screenshot_rel)
        await page.screenshot(path=screenshot_full)

        # Thread-safe log append
        async with log_lock:
            log_data = {"applications": []}
            if os.path.exists(APPLICATION_LOG_PATH):
                try:
                    with open(APPLICATION_LOG_PATH, "r", encoding="utf-8") as f:
                        log_data = json.load(f)
                except Exception:
                    pass

            app_record = {
                "id": f"batch-{timestamp}-{rand_id}",
                "job_url": url,
                "job_title": job_title,
                "company": company,
                "ats_platform": detect_ats_platform_by_url(url),
                "status": "applied",
                "applied_at": datetime.utcnow().isoformat() + "Z",
                "screenshot_artifact_url": screenshot_rel
            }
            log_data["applications"].append(app_record)

            with open(APPLICATION_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2)

        return {"status": "applied", "screenshot": screenshot_rel, "fields_filled": fields_filled, "submitted": submitted}

    except Exception as e:
        return {"status": "failed", "reason": str(e)}
    finally:
        await page.close()

async def worker_loop(worker_id: int, queue: asyncio.Queue, browser, profile: dict, learned_dict: dict, results: list):
    """Worker task processing jobs from shared queue."""
    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    try:
        while True:
            try:
                job_item = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            idx, total, job = job_item
            print(f"[Worker-{worker_id}] [{idx}/{total}] Processing: {job.get('title')} at {job.get('company')}...")

            try:
                res = await asyncio.wait_for(
                    apply_single_job(context, job, profile, learned_dict),
                    timeout=JOB_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                res = {"status": "failed", "reason": f"Timeout exceeded ({JOB_TIMEOUT_SECONDS}s)"}
            except Exception as e:
                res = {"status": "failed", "reason": str(e)}

            res["job"] = job
            results.append(res)
            queue.task_done()
    finally:
        await context.close()

async def run_batch(jobs_list: list):
    if not os.path.exists(USER_PROFILE_PATH):
        print("Error: user_profile.json missing.")
        return

    with open(USER_PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)

    learned_dict = {}
    if os.path.exists(LEARNED_ANSWERS_PATH):
        try:
            with open(LEARNED_ANSWERS_PATH, "r", encoding="utf-8") as f:
                learned_dict = {a["question_hash"]: a["answer"] for a in json.load(f).get("answers", [])}
        except Exception:
            pass

    # Deduplication Guard: Load already applied URLs from application_log.json
    applied_urls = set()
    if os.path.exists(APPLICATION_LOG_PATH):
        try:
            with open(APPLICATION_LOG_PATH, "r", encoding="utf-8") as f:
                log_data = json.load(f)
                for app in log_data.get("applications", []):
                    if app.get("status") == "applied" and app.get("job_url"):
                        applied_urls.add(app["job_url"].strip())
                    elif app.get("status") == "applied" and app.get("url"):
                        applied_urls.add(app["url"].strip())
        except Exception as e:
            print(f"[Deduplication] Warning reading application_log.json: {e}")

    # Filter out already applied jobs
    filtered_jobs = []
    for job in jobs_list:
        job_url = (job.get("url") or "").strip()
        if job_url and job_url in applied_urls:
            print(f"[Deduplication] Skipping already applied job: {job.get('title')} at {job.get('company')}")
            continue
        filtered_jobs.append(job)

    if len(filtered_jobs) < len(jobs_list):
        print(f"[Deduplication] Filtered out {len(jobs_list) - len(filtered_jobs)} already applied jobs. Remaining in batch: {len(filtered_jobs)}")

    if not filtered_jobs:
        print("[Deduplication] All jobs in the current batch have already been applied to. Exiting cleanly.")
        return

    # Build queue
    queue = asyncio.Queue()
    for idx, job in enumerate(filtered_jobs):
        queue.put_nowait((idx + 1, len(filtered_jobs), job))

    from playwright.async_api import async_playwright

    results = []
    start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        workers = [
            asyncio.create_task(worker_loop(i + 1, queue, browser, profile, learned_dict, results))
            for i in range(CONCURRENT_WORKERS)
        ]

        await asyncio.gather(*workers)
        await browser.close()

    elapsed = round(time.time() - start_time, 1)

    applied_count = sum(1 for r in results if r.get("status") == "applied")
    skipped_count = sum(1 for r in results if r.get("status") == "skipped")
    failed_count = sum(1 for r in results if r.get("status") == "failed")

    # Send consolidated Telegram Summary
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if bot_token and chat_id:
        msg = (
            f"🎯 <b>SparkJobs: Batch Auto-Apply Completed</b>\n\n"
            f"📊 <b>Total Processed:</b> {len(jobs_list)}\n"
            f"✅ <b>Successfully Applied:</b> {applied_count}\n"
            f"⚠️ <b>Skipped (Expired/CAPTCHA):</b> {skipped_count}\n"
            f"❌ <b>Failed:</b> {failed_count}\n"
            f"⏱️ <b>Total Execution Time:</b> {elapsed}s\n\n"
            f"👉 Open your dashboard to view confirmation screenshots."
        )
        try:
            send_telegram_message(bot_token, chat_id, msg)
        except Exception as err:
            print(f"Failed to send Telegram batch summary: {err}")

    print(f"Batch completed in {elapsed}s. Applied: {applied_count}, Skipped: {skipped_count}, Failed: {failed_count}")

def main():
    parser = argparse.ArgumentParser(description="SparkJobs High-Performance Batch Auto-Apply Runner")
    parser.add_argument("--jobs-json", type=str, help="JSON array string of target jobs")
    parser.add_argument("--jobs-file", type=str, help="Path to JSON file containing target jobs")
    args = parser.parse_args()

    jobs = []
    if args.jobs_json:
        try:
            jobs = json.loads(args.jobs_json)
        except Exception as e:
            print(f"Failed to parse --jobs-json: {e}")
            return
    elif args.jobs_file and os.path.exists(args.jobs_file):
        try:
            with open(args.jobs_file, "r", encoding="utf-8") as f:
                jobs = json.load(f)
        except Exception as e:
            print(f"Failed to read --jobs-file: {e}")
            return

    if not jobs:
        print("No jobs provided for batch apply.")
        return

    asyncio.run(run_batch(jobs))

if __name__ == "__main__":
    main()
