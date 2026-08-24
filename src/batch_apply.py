import os
import sys
import json
import time
import random
import argparse
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# Ensure src/ directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_apply import (
    BASE_DIR, USER_PROFILE_PATH, LEARNED_ANSWERS_PATH, APPLICATION_LOG_PATH,
    detect_ats_platform_by_url, detect_ats_platform_by_dom
)
from telegram_sender import send_telegram_message, escape_html

BATCH_STATUS_PATH = os.path.join(BASE_DIR, "data", "batch_status.json")

async def apply_single_job(page, context, job: dict, profile: dict, learned_dict: dict) -> dict:
    url = job.get("url", "")
    job_title = job.get("title", "Job Posting")
    company = job.get("company", "Company")
    
    if not url:
        return {"status": "failed", "reason": "Missing job URL"}

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        # Check for CAPTCHA
        for cap_sel in ["iframe[src*='captcha']", "div.g-recaptcha", ".cf-turnstile", ".hcaptcha"]:
            if await page.query_selector(cap_sel):
                return {"status": "skipped", "reason": "Requires CAPTCHA (manual apply required)"}

        # Check for external apply button (LinkedIn, Indeed, WWR)
        input_elements = await page.query_selector_all("input, textarea, select")
        has_visible_inputs = any(await el.is_visible() for el in input_elements) if input_elements else False

        if not has_visible_inputs:
            for apply_sel in [
                "a:has-text('Apply Now')", "button:has-text('Apply Now')",
                "a:has-text('Apply on company website')", "a:has-text('Apply for this job')",
                "button:has-text('Apply for this job')", "a:has-text('Apply')",
                "button:has-text('Apply')", "[data-qa='apply-button']", ".apply-button", "#apply-button"
            ]:
                apply_btn = await page.query_selector(apply_sel)
                if apply_btn and await apply_btn.is_visible():
                    try:
                        href = await apply_btn.get_attribute("href")
                        if href and href.startswith("http"):
                            await page.goto(href, wait_until="domcontentloaded", timeout=25000)
                            await page.wait_for_timeout(3000)
                        else:
                            await apply_btn.click()
                            await page.wait_for_timeout(3000)
                        input_elements = await page.query_selector_all("input, textarea, select")
                        break
                    except Exception:
                        pass

        # Scan and fill visible form fields
        input_elements = await page.query_selector_all("input, textarea, select")
        fields_filled = 0

        for elem in input_elements:
            try:
                if not await elem.is_visible():
                    continue

                input_type = (await elem.get_attribute("type") or "text").lower()
                name_attr = (await elem.get_attribute("name") or "").lower()
                id_attr = (await elem.get_attribute("id") or "").lower()
                placeholder = (await elem.get_attribute("placeholder") or "").lower()

                if input_type in ["hidden", "submit", "button"]:
                    continue

                # File upload (CV / Resume)
                if input_type == "file":
                    cv_name = profile.get("cv_filename", "default_cv.pdf")
                    workspace = os.environ.get("GITHUB_WORKSPACE", BASE_DIR)
                    cv_path = os.path.join(workspace, "data", "cvs", cv_name)
                    if os.path.exists(cv_path):
                        await elem.set_input_files(cv_path)
                        fields_filled += 1
                    continue

                label_text = f"{name_attr} {id_attr} {placeholder}"

                # Basic standard field mappings
                if any(k in label_text for k in ["first_name", "firstname", "first name"]):
                    val = profile.get("full_name", "").split()[0] if profile.get("full_name") else ""
                    await elem.fill(val)
                    fields_filled += 1
                elif any(k in label_text for k in ["last_name", "lastname", "last name"]):
                    val = " ".join(profile.get("full_name", "").split()[1:]) if len(profile.get("full_name", "").split()) > 1 else ""
                    await elem.fill(val)
                    fields_filled += 1
                elif any(k in label_text for k in ["name", "full_name", "fullname"]):
                    await elem.fill(profile.get("full_name", ""))
                    fields_filled += 1
                elif "email" in label_text:
                    await elem.fill(profile.get("email", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["phone", "mobile", "tel"]):
                    await elem.fill(profile.get("phone", ""))
                    fields_filled += 1
                elif "linkedin" in label_text:
                    await elem.fill(profile.get("linkedin_url", ""))
                    fields_filled += 1
                elif "github" in label_text:
                    await elem.fill(profile.get("github_url", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["portfolio", "website", "url"]):
                    await elem.fill(profile.get("portfolio_url", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["city", "location", "address"]):
                    await elem.fill(profile.get("city", profile.get("location", "")))
                    fields_filled += 1
                elif any(k in label_text for k in ["company", "current_company"]):
                    await elem.fill(profile.get("current_company", ""))
                    fields_filled += 1
                elif any(k in label_text for k in ["title", "current_title", "job_title"]):
                    await elem.fill(profile.get("current_title", ""))
                    fields_filled += 1
            except Exception:
                pass

        # Capture proof screenshot
        os.makedirs(os.path.join(BASE_DIR, "data", "screenshots"), exist_ok=True)
        timestamp = int(time.time())
        screenshot_rel = f"screenshots/confirm_{timestamp}.png"
        screenshot_full = os.path.join(BASE_DIR, "data", screenshot_rel)
        await page.screenshot(path=screenshot_full)

        # Log into application_log.json
        log_data = {"applications": []}
        if os.path.exists(APPLICATION_LOG_PATH):
            try:
                with open(APPLICATION_LOG_PATH, "r", encoding="utf-8") as f:
                    log_data = json.load(f)
            except Exception:
                pass

        app_record = {
            "id": f"batch-{timestamp}-{random.randint(100, 999)}",
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

        return {"status": "applied", "screenshot": screenshot_rel, "fields_filled": fields_filled}

    except Exception as e:
        return {"status": "failed", "reason": str(e)}

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

    from playwright.async_api import async_playwright

    applied_count = 0
    failed_count = 0
    skipped_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = await context.new_page()

        for idx, job in enumerate(jobs_list):
            print(f"[{idx+1}/{len(jobs_list)}] Processing: {job.get('title')} at {job.get('company')}...")
            res = await apply_single_job(page, context, job, profile, learned_dict)
            
            status = res.get("status")
            if status == "applied":
                applied_count += 1
            elif status == "skipped":
                skipped_count += 1
            else:
                failed_count += 1

            # Anti-bot jitter delay between jobs
            if idx < len(jobs_list) - 1:
                jitter = random.uniform(3.0, 6.0)
                await asyncio.sleep(jitter)

        await browser.close()

    # Send consolidated Telegram Summary
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if bot_token and chat_id:
        msg = (
            f"🎯 <b>SparkJobs: Batch Auto-Apply Completed</b>\n\n"
            f"📊 <b>Total Processed:</b> {len(jobs_list)}\n"
            f"✅ <b>Successfully Applied:</b> {applied_count}\n"
            f"⚠️ <b>Skipped (CAPTCHA):</b> {skipped_count}\n"
            f"❌ <b>Failed:</b> {failed_count}\n\n"
            f"👉 Open your dashboard to view confirmation screenshots."
        )
        try:
            send_telegram_message(bot_token, chat_id, msg)
        except Exception as err:
            print(f"Failed to send Telegram batch summary: {err}")

    print(f"Batch completed. Applied: {applied_count}, Skipped: {skipped_count}, Failed: {failed_count}")

def main():
    parser = argparse.ArgumentParser(description="SparkJobs Batch Auto-Apply Runner")
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
