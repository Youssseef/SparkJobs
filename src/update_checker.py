import os
import json
import hashlib
import requests
from telegram_sender import send_telegram_message, SPARKGEN_FOOTER
from config_loader import BASE_DIR

def check_for_updates(bot_token: str, chat_id: str, tracker: dict, language: str):
    """
    Checks the remote template repository for new releases or main updates
    by comparing git hash objects. Sends a single Telegram alert if an update is found.
    M-06 Fix: Migrated from urllib to requests.
    C-02 Fix: Removed mid-cycle save_status_tracker call (main.py saves tracker at cycle end).
    """
    try:
        files_to_check = [
            "src/main.py",
            ".github/workflows/scan.yml",
            ".github/workflows/analyze_form.yml",
            ".github/workflows/submit_application.yml"
        ]
        
        template_owner = os.environ.get("SPARKJOBS_TEMPLATE_OWNER", "Youssseef")
        template_repo = os.environ.get("SPARKJOBS_TEMPLATE_REPO", "SparkJobs")
        
        headers = {'User-Agent': 'SparkJobs-Bot'}
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        update_available = False
        latest_sha = ""
        
        for path in files_to_check:
            local_file_path = os.path.join(BASE_DIR, path.replace("/", os.sep))
            local_sha = ""
            if os.path.exists(local_file_path):
                with open(local_file_path, "rb") as f:
                    local_data = f.read()
                local_header = f"blob {len(local_data)}\0".encode('utf-8')
                sha1 = hashlib.sha1()
                sha1.update(local_header)
                sha1.update(local_data)
                local_sha = sha1.hexdigest()
                
            url = f"https://api.github.com/repos/{template_owner}/{template_repo}/contents/{path}"
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                meta = response.json()
                template_sha = meta.get("sha", "")
                if path == "src/main.py":
                    latest_sha = template_sha
                if template_sha and local_sha != template_sha:
                    update_available = True
                    break

        if update_available and latest_sha:
            if tracker.get("last_update_alert_sha") != latest_sha:
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
                    tracker["last_update_alert_sha"] = latest_sha
    except Exception as update_err:
        print(f"Failed to check for template updates (non-blocking): {update_err}")
