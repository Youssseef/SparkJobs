import requests
import html
import hashlib
import time
import traceback
from datetime import datetime, timedelta

SPARKGEN_FOOTER = "\n\n─────────────────\nPowered by <a href='https://sparkgen.net'>SparkGen</a>"

def escape_html(text: str) -> str:
    """
    Escapes special HTML characters so Telegram doesn't crash.
    """
    if not text:
        return ""
    return html.escape(str(text))

def safe_callback_id(job_id: str, action: str = "applied") -> str:
    """
    H-02 Fix: Guarantees callback_data stays under Telegram's 64-byte limit.
    """
    prefix = f"{action}:"
    raw_str = f"{prefix}{job_id}"
    if len(raw_str.encode('utf-8')) <= 64:
        return raw_str
    
    # Hash long IDs deterministically to fit 64-byte budget
    hashed_id = hashlib.md5(job_id.encode('utf-8')).hexdigest()[:32]
    return f"{prefix}{hashed_id}"

def post_with_retry(url: str, json_payload: dict, max_retries: int = 3, timeout: int = 10):
    """
    M-01 Fix: Retries POST request on transient network errors or HTTP 429/5xx status codes
    using exponential backoff.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, json=json_payload, timeout=timeout)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                try:
                    retry_after = int(response.headers.get("Retry-After", 2 * attempt))
                except (ValueError, TypeError):
                    retry_after = 2 * attempt
                print(f"Telegram API 429 Rate Limited. Waiting {retry_after}s before retry {attempt}/{max_retries}...")
                time.sleep(retry_after)
            elif response.status_code >= 500:
                print(f"Telegram API {response.status_code} server error. Waiting {2 ** attempt}s before retry {attempt}/{max_retries}...")
                time.sleep(2 ** attempt)
            else:
                return response
        except requests.RequestException as e:
            if attempt == max_retries:
                print(f"Network error on final attempt {attempt}/{max_retries}. Request failed.")
                return None
            print(f"Network error on attempt {attempt}/{max_retries}: {e}. Retrying in {2 ** attempt}s...")
            time.sleep(2 ** attempt)
    return None

def send_telegram_alert(bot_token: str, chat_id: str, job: dict, ai_analysis: dict, profile_name: str, language: str = "ar") -> bool:
    """
    Sends a formatted HTML job alert message to Telegram.
    """
    if not bot_token or not chat_id:
        print("Missing Telegram bot_token or chat_id. Alert not sent.")
        return False

    # 1. Format Safety/Risk Rating Badge
    risk_level = ai_analysis.get("risk_level", "Low")
    if language == "ar":
        if risk_level == "High":
            safety_badge = "🔴 <b>مخاطر عالية (وظيفة وهمية/احتيال)</b>"
        elif risk_level == "Medium":
            safety_badge = "🟡 <b>مخاطر متوسطة</b>"
        else:
            safety_badge = "🟢 <b>مخاطر منخفضة</b>"
    else:
        if risk_level == "High":
            safety_badge = "🔴 <b>HIGH RISK (SCAM/GHOST)</b>"
        elif risk_level == "Medium":
            safety_badge = "🟡 <b>MEDIUM RISK</b>"
        else:
            safety_badge = "🟢 <b>LOW RISK</b>"

    risk_reason = ai_analysis.get("risk_reason", "")
    if risk_reason:
        safety_badge += f"\n   <i>└ {escape_html(risk_reason)}</i>"

    # 2. Extract job metrics (H-11 Fix: null safety for arrays/strings)
    match_score = ai_analysis.get("match_score", 0)
    estimated_salary = ai_analysis.get("estimated_salary") or ("غير محدد" if language == "ar" else "Not specified")
    pros_list = ai_analysis.get("pros") or []
    cons_list = ai_analysis.get("cons") or []
    missing_list = ai_analysis.get("missing_keywords") or []
    
    pros = "\n".join([f"• {escape_html(p)}" for p in pros_list])
    cons = "\n".join([f"• {escape_html(c)}" for c in cons_list])
    missing = ", ".join([escape_html(m) for m in missing_list])

    # 3. Format outreach message
    outreach = ai_analysis.get("outreach_message") or ""
    
    if language == "ar":
        pros_section = f"\n<b>✅ نقاط القوة:</b>\n{pros}" if pros else ""
        cons_section = f"\n<b>⚠️ فجوات:</b>\n{cons}" if cons else ""
        missing_section = f"\n<b>🔍 كلمات مفتاحية ناقصة:</b> {missing}" if missing else ""
    else:
        pros_section = f"\n<b>✅ Strengths:</b>\n{pros}" if pros else ""
        cons_section = f"\n<b>⚠️ Gaps:</b>\n{cons}" if cons else ""
        missing_section = f"\n<b>🔍 Missing Keywords:</b> {missing}" if missing else ""

    # C-03 Fix: HTML escape and validate job URL
    raw_url = job.get('url', '')
    safe_url = escape_html(raw_url)
    if not (raw_url.startswith('http://') or raw_url.startswith('https://')):
        safe_url = "https://sparkgen.net"

    # 4. Construct HTML message body
    if language == "ar":
        message = f"""<b>وظيفة جديدة | {escape_html(profile_name)}</b>
 
<b>{escape_html(job.get('title', ''))}</b>
<b>{escape_html(job.get('company', ''))}</b> · {escape_html(job.get('location', ''))}
المصدر: {escape_html(job.get('source', ''))}
 
──────────────────
تقييم الأمان: {safety_badge}
 
الراتب التقديري: {escape_html(estimated_salary)}
 
توافق الـ CV: {match_score}%{pros_section}{cons_section}{missing_section}
 
رسالة التواصل مع الـ Recruiter:
<code>{escape_html(outreach)}</code>
 
──────────────────
رابط التقديم: <a href="{safe_url}">قدّم الآن (Apply Now)</a>{SPARKGEN_FOOTER}
"""
    else:
        message = f"""<b>New Job Match | {escape_html(profile_name)}</b>
 
<b>{escape_html(job.get('title', ''))}</b>
<b>{escape_html(job.get('company', ''))}</b> · {escape_html(job.get('location', ''))}
Source: {escape_html(job.get('source', ''))}
 
──────────────────
Safety Rating: {safety_badge}
 
Est. Salary: {escape_html(estimated_salary)}
 
CV Match Score: {match_score}%{pros_section}{cons_section}{missing_section}
 
Recruiter Outreach Message:
<code>{escape_html(outreach)}</code>
 
──────────────────
Application Link: <a href="{safe_url}">Apply Now</a>{SPARKGEN_FOOTER}
"""

    # H-08 Fix: Telegram 4096 character limit guard
    MAX_TG_LENGTH = 4096
    if len(message.encode('utf-8')) > MAX_TG_LENGTH:
        if len(outreach) > 300:
            truncated_outreach = outreach[:300] + "..."
            message = message.replace(escape_html(outreach), escape_html(truncated_outreach))
        if len(message.encode('utf-8')) > MAX_TG_LENGTH:
            message = message[:4050] + "\n...\n" + SPARKGEN_FOOTER

    btn_applied = "تم التقديم ✅" if language == "ar" else "Applied ✅"
    btn_ignore = "تجاهل ❌" if language == "ar" else "Ignore ❌"
    
    # H-02 & M-06 Fix: Truncate callback_data safely & align action name to 'ignored'
    job_id = str(job.get('id', ''))
    cb_applied = safe_callback_id(job_id, "applied")
    cb_ignored = safe_callback_id(job_id, "ignored")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": btn_applied, "callback_data": cb_applied},
                    {"text": btn_ignore, "callback_data": cb_ignored}
                ]
            ]
        }
    }
    
    try:
        response = post_with_retry(url, json_payload=payload)
        if response and response.status_code == 200:
            print("Telegram alert sent successfully.")
            return True
        else:
            err_text = response.text if response else "No response"
            print(f"Failed to send Telegram alert: {err_text}")
            return False
    except Exception as e:
        sanitized_err = str(e).replace(bot_token, "[REDACTED]") if bot_token else str(e)
        print(f"Error sending Telegram alert: {sanitized_err}")
        return False

def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    """
    Sends a plain text message to Telegram with retry support.
    """
    if not bot_token or not chat_id:
        print("Missing Telegram bot_token or chat_id. Message not sent.")
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True}
    }
    try:
        response = post_with_retry(url, json_payload=payload)
        if response and response.status_code == 200:
            print("Telegram message sent successfully.")
            return True
        else:
            err_text = response.text if response else "No response"
            print(f"Failed to send Telegram message: {err_text}")
            return False
    except Exception as e:
        sanitized_err = str(e).replace(bot_token, "[REDACTED]") if bot_token else str(e)
        print(f"Error sending Telegram message: {sanitized_err}")
        return False

def send_weekly_summary(bot_token: str, chat_id: str, tracker: dict, total_cycle_jobs: int, total_cycle_alerts: int, language: str = "ar") -> bool:
    """
    Checks if 7 days have passed since the last weekly report and dispatches a summary to Telegram.
    """
    try:
        last_summary_dt = datetime.fromisoformat(tracker.get("last_summary_sent", datetime.now().isoformat()))
        if datetime.now() - last_summary_dt >= timedelta(days=7):
            print("Sending weekly status summary to Telegram...")
            completed_scans = tracker.get('scans_completed_this_week', 0)
            evaluated_jobs = tracker.get('jobs_evaluated_this_week', 0)
            alerts_sent = tracker.get('alerts_sent_this_week', 0)
            
            if language == "ar":
                summary_text = (
                    f"<b>تقرير النشاط الأسبوعي لبوت SparkJobs</b>\n\n"
                    f"• عمليات الفحص المكتملة: <b>{completed_scans}</b>\n"
                    f"• الوظائف التي تم تقييمها: <b>{evaluated_jobs}</b>\n"
                    f"• التنبيهات المرسلة: <b>{alerts_sent}</b>\n\n"
                    f"البوت يعمل بكفاءة ويبحث عن جديد الوظائف على مدار الساعة."
                    f"{SPARKGEN_FOOTER}"
                )
            else:
                summary_text = (
                    f"<b>SparkJobs Weekly Activity Report</b>\n\n"
                    f"• Scans completed: <b>{completed_scans}</b>\n"
                    f"• Jobs evaluated: <b>{evaluated_jobs}</b>\n"
                    f"• Alerts sent: <b>{alerts_sent}</b>\n\n"
                    f"The bot is running smoothly, scanning for new job postings 24/7."
                    f"{SPARKGEN_FOOTER}"
                )
            sent = send_telegram_message(bot_token, chat_id, summary_text)
            if sent:
                tracker["scans_completed_this_week"] = 0
                tracker["jobs_evaluated_this_week"] = 0
                tracker["alerts_sent_this_week"] = 0
                tracker["last_summary_sent"] = datetime.now().isoformat()
                return True
    except Exception as e:
        print(f"Error executing weekly summary routine: {e}")
    return False
def _human_age(scraped_at_str: str, language: str = "en") -> str:
    if not scraped_at_str:
        return "unknown" if language == "en" else "غير معروف"
    try:
        scraped_at = datetime.fromisoformat(scraped_at_str.replace("Z", "+00:00"))
        delta = datetime.now(scraped_at.tzinfo) - scraped_at
        if delta.days > 0:
            if delta.days == 1:
                return "1 day ago" if language == "en" else "منذ يوم"
            return f"{delta.days} days ago" if language == "en" else f"منذ {delta.days} أيام"
        hours = delta.seconds // 3600
        if hours > 0:
            if hours == 1:
                return "1 hour ago" if language == "en" else "منذ ساعة"
            return f"{hours} hours ago" if language == "en" else f"منذ {hours} ساعات"
        minutes = (delta.seconds % 3600) // 60
        if minutes == 1:
            return "1 minute ago" if language == "en" else "منذ دقيقة"
        return f"{minutes} minutes ago" if language == "en" else f"منذ {minutes} دقائق"
    except Exception:
        return "just now" if language == "en" else "الآن"

def send_search_results(bot_token: str, chat_id: str, results: list, query: str, last_scan_at: str = None, language: str = "en") -> bool:
    """
    Renders up to 5 job search results and sends them to Telegram.
    Includes stale-bot feedback when last scan is old.
    """
    if not results:
        is_stale = False
        last_scan_text = ""
        if last_scan_at:
            try:
                last_scan = datetime.fromisoformat(last_scan_at.replace("Z", "+00:00"))
                delta = datetime.now(last_scan.tzinfo) - last_scan
                if delta.total_seconds() > 48 * 3600:
                    is_stale = True
                    last_scan_text = _human_age(last_scan_at, language)
            except Exception:
                pass

        if language == "ar":
            if is_stale:
                msg = f"🔍 لم يتم العثور على وظائف تطابق <b>{escape_html(query)}</b> في آخر 48 ساعة.\n\n⚠️ <i>ملاحظة: آخر فحص تم {last_scan_text} — يرجى التأكد من أن البوت يعمل بشكل صحيح.</i>"
            else:
                msg = f"🔍 لم يتم العثور على وظائف تطابق <b>{escape_html(query)}</b> في آخر 48 ساعة."
        else:
            if is_stale:
                msg = f"🔍 No jobs found matching <b>{escape_html(query)}</b> in the last 48 hours.\n\n⚠️ <i>Note: Last scan was {last_scan_text} — please check that your bot is running.</i>"
            else:
                msg = f"🔍 No jobs found matching <b>{escape_html(query)}</b> in the last 48 hours."
        return send_telegram_message(bot_token, chat_id, msg + SPARKGEN_FOOTER)

    if language == "ar":
        msg = f"🔍 <b>نتائج البحث عن:</b> <i>{escape_html(query)}</i>\n\n"
    else:
        msg = f"🔍 <b>Search results for:</b> <i>{escape_html(query)}</i>\n\n"

    for i, job in enumerate(results[:5], 1):
        age = _human_age(job.get("scraped_at", ""), language)
        apply_label = "تقدم الآن" if language == "ar" else "Apply Now"
        msg += (
            f"<b>{i}. {escape_html(job['title'])}</b>\n"
            f"🏢 {escape_html(job.get('company',''))}  •  🎯 {job.get('match_score',0)}%  •  🕐 {age}\n"
            f"<a href='{job['url']}'>{apply_label} →</a>\n\n"
        )
    return send_telegram_message(bot_token, chat_id, msg + SPARKGEN_FOOTER)

if __name__ == "__main__":
    dummy_job = {
        "id": "test-job-12345",
        "title": "React Developer",
        "company": "Tech Solutions",
        "location": "Remote (Germany)",
        "source": "Google Jobs",
        "url": "https://example.com/job"
    }
    dummy_analysis = {
        "match_score": 85,
        "risk_level": "Low",
        "risk_reason": "Verified corporate site",
        "pros": ["Strong JavaScript foundation"],
        "cons": ["Lacks Docker expertise"],
        "missing_keywords": ["Docker"],
        "outreach_message": "Hi Recruiting Team..."
    }
    print("Formatted message template check:")
    send_telegram_alert("", "", dummy_job, dummy_analysis, "React Developer")
