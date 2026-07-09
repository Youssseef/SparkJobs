import requests
import html

def escape_html(text: str) -> str:
    """
    Escapes special HTML characters so Telegram doesn't crash.
    """
    if not text:
        return ""
    return html.escape(str(text))

def send_telegram_alert(bot_token: str, chat_id: str, job: dict, ai_analysis: dict, profile_name: str) -> bool:
    """
    Sends a beautifully formatted HTML job alert message to Telegram.
    """
    if not bot_token or not chat_id:
        print("Missing Telegram bot_token or chat_id. Alert not sent.")
        return False

    # 1. Format the Safety/Risk Rating Badge
    risk_level = ai_analysis.get("risk_level", "Low")
    if risk_level == "High":
        safety_badge = "🔴 <b>HIGH RISK (SCAM/GHOST)</b>"
    elif risk_level == "Medium":
        safety_badge = "🟡 <b>MEDIUM RISK</b>"
    else:
        safety_badge = "🟢 <b>LOW RISK</b>"

    risk_reason = ai_analysis.get("risk_reason", "")
    if risk_reason:
        safety_badge += f"\n   <i>└ {escape_html(risk_reason)}</i>"

    # 2. Extract job metrics
    match_score = ai_analysis.get("match_score", 0)
    pros = "\n".join([f"• {escape_html(p)}" for p in ai_analysis.get("pros", [])])
    cons = "\n".join([f"• {escape_html(c)}" for c in ai_analysis.get("cons", [])])
    missing = ", ".join([escape_html(m) for m in ai_analysis.get("missing_keywords", [])])

    # 3. Format outreach message
    outreach = ai_analysis.get("outreach_message", "")
    
    # 4. Construct the HTML message body
    message = f"""🔔 <b>وظيفة جديدة | {escape_html(profile_name)}</b>

💼 <b>{escape_html(job.get('title', ''))}</b>
🏢 <b>{escape_html(job.get('company', ''))}</b> · {escape_html(job.get('location', ''))}
🌐 المصدر: {escape_html(job.get('source', ''))}

──────────────────
🛡️ <b>تقييم الأمان:</b> {safety_badge}

🎯 <b>توافق الـ CV:</b> {match_score}%
{"<b>✅ نقاط القوة:</b>\n" + pros if pros else ""}
{"<b>⚠️ فجوات:</b>\n" + cons if cons else ""}
{"<b>🔍 كلمات مفتاحية ناقصة:</b> " + missing if missing else ""}

✉️ <b>رسالة التواصل مع الـ Recruiter:</b>
<code>{escape_html(outreach)}</code>

──────────────────
🔗 <a href="{job.get('url', '')}">قدّم الآن (Apply Now)</a>
"""
    
    # Send request to Telegram
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram alert sent successfully.")
            return True
        else:
            print(f"Failed to send Telegram alert: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")
        return False

if __name__ == "__main__":
    # Quick mock test
    dummy_job = {
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
        "pros": ["Strong JavaScript foundation", "React experience aligns perfectly"],
        "cons": ["Lacks Docker expertise"],
        "missing_keywords": ["Docker", "GraphQL"],
        "outreach_message": "Hi Recruiting Team, I noticed your opening for a React Developer at Tech Solutions. My skills align well with your stack..."
    }
    # To run test, set keys or check mock output:
    print("Formatted message template check:")
    print("Test will run silently as no keys are provided.")
    send_telegram_alert("", "", dummy_job, dummy_analysis, "React Developer")
