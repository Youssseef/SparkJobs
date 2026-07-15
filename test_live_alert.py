import os
import sys

# Add src folder to import path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from ai_matcher import analyze_job_match
from telegram_sender import send_telegram_alert

# ─────────────────────────────────────────────────────────────────────────────
# ⚠️  NEVER hardcode real credentials here.
#     Set these as environment variables when running locally:
#
#     $env:GEMINI_KEY   = "AIza..."
#     $env:BOT_TOKEN    = "1234:ABC..."
#     $env:CHAT_ID      = "1180..."
#
#     Each user's real keys live ONLY in their own private GitHub repo Secrets
#     (Settings → Secrets and variables → Actions) — never in source code.
# ─────────────────────────────────────────────────────────────────────────────
GEMINI_KEY = os.environ.get("GEMINI_KEY", "")
BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
CHAT_ID    = os.environ.get("CHAT_ID", "")

if not GEMINI_KEY or not BOT_TOKEN or not CHAT_ID:
    print("ERROR: Missing credentials. Set GEMINI_KEY, BOT_TOKEN, and CHAT_ID as environment variables.")
    sys.exit(1)


# Test Data
cv_text = """
Youssef Wael
Cairo, Egypt
youssef@sparkgen.net | +20 100 000 0000 | https://github.com/youssef

PROFESSIONAL SUMMARY
Passionate Frontend Developer with 3+ years of experience building modern user interfaces using React, JavaScript, and TypeScript. Expert in responsive web design, state management, and modern styling libraries like TailwindCSS.

TECHNICAL SKILLS
- Frontend: React, JavaScript, TypeScript, HTML5, CSS3, Redux, Context API
- Styling: TailwindCSS, CSS Modules, Styled Components
- Tools: Git, GitHub, VS Code, Figma
"""

job = {
    "title": "React Frontend Engineer",
    "company": "SparkGen Innovate",
    "location": "Remote (Germany)",
    "source": "Remotive",
    "url": "https://remotive.com/remote-jobs/software-development/react-frontend-engineer-12345"
}

job_desc = """
We are looking for a React Frontend Engineer to join our team remote. 
Required:
- React (3+ years)
- TypeScript
- TailwindCSS
- Experience building responsive dashboards and styling
Nice to have: Redux or Context API.
"""

print("Running AI analysis with Gemini...")
analysis = analyze_job_match(cv_text, job["title"], job_desc, GEMINI_KEY)

print(f"AI Score: {analysis.get('match_score')}%")
print(f"Risk Assessment: {analysis.get('risk_level')} ({analysis.get('risk_reason')})")

print("Sending Telegram Alert...")
success = send_telegram_alert(BOT_TOKEN, CHAT_ID, job, analysis, "React Developer Profile")
if success:
    print("Test passed successfully!")
else:
    print("Failed to send Telegram alert.")
