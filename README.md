# SparkJobs 🚀
> Smart Automated Job Scan, Match Rating & Telegram Alerts Bot

## 🕌 صدقة جارية / Ongoing Charity
> **"هذا العمل صدقة جارية لي ولكل أمة المسلمين، نسأل الله أن يرزقنا وإياكم الرزق الحلال الطيب."**
> 
> *This project is dedicated as an ongoing charity (Sadaqah Jariyah) for the benefit of the Muslim Ummah. May Allah grant us and you lawful, blessed, and pure livelihood.*

---

SparkJobs is an automated personal assistant designed to query local and international developer job boards (Indeed, Google Jobs) concurrently, score job descriptions against your CV using **Google Gemini AI**, filter out duplicate or fake postings, and deliver clean, structured summaries directly to your Telegram channel.

It consists of two main parts:
1. **`web/`**: A React + Tailwind CSS client portal integrated into the SparkGen website. It features a bilingual setup wizard to easily initialize the bot, generate a repository on your behalf, write configurations, and manage active searches.
2. **`bot/`**: A Python-based scraping and AI classification bot designed to be hosted 100% free on **GitHub Actions** as a cron schedule with no server hosting costs.

---

## 🛠️ Recent Architectural Upgrades (Updates log)

*   **State Persistence & Ephemeral Storage Fix:** The GitHub Actions workflow (`scan.yml`) now commits and pushes both `seen_jobs.json` (deduplication database) and `status_tracker.json` (dashboard stats) back to the user's private repository after every scan. This ensures that dashboard metrics correctly accumulate over time instead of resetting on ephemeral runner shutdowns.
*   **Security Isolation & Dev Environment Protection:** Local testing files (like `bot/test_live_alert.py`) are configured to load keys securely from environment variables (`os.environ.get`) instead of hardcoded strings, and are permanently ignored via `.gitignore` to prevent accidental credential leaks.
*   **New Google GenAI SDK Migration:** Migrated the bot from the legacy `google-generativeai` package to the new `google.genai` SDK for future-proof API compatibility.
*   **Gemini Model Cascade Fallback:** Configured a resilient AI matching pipeline starting with `gemini-2.5-flash` as primary, and automatically cascading to `gemini-2.5-flash-lite` and `gemini-3.1-flash-lite` in case of rate limits or model downtime.
*   **Binary CV Parsing (.pdf & .docx):** Replaced manual plain text variables with support for binary file uploads. Features a pure-Python custom DOCX parser utilizing python's built-in `zipfile` and `xml.etree.ElementTree` namespaces to extract clean text without bloating the action runner's dependencies.


## 🌟 Premium Features & Capabilities

*   **AI-Estimated Salary Ranges:** If a job post lacks salary details, Gemini estimates the local market average (e.g. `$90,000 - $120,000 / yr` or `Average: 15,000 AED / mo`) based on job title and country.
*   **Bilingual Dashboard & Wizard:** Seamless English and Arabic toggle modes for both initial configuration and dashboard monitoring.
*   **Connection & Test Alert Button:** Interactive connection validation directly in the credentials setup, plus a live "Send Test Alert" button on the dashboard to verify Telegram integrations instantly.
*   **Real-time Activity Stats:** Displays dashboard metrics tracked directly from runs (Scans Run, Jobs Evaluated, and Alerts Sent this week).
*   **Exclusion Keywords Blocklist:** Block junior roles, unpaid listings, outsourcing agencies, or specific companies (e.g. `junior, intern, PHP`) by title, company, or description.
*   **Custom Scan Schedules:** Dynamically configures the GitHub Actions cron intervals (20m, 1h, 6h, or daily).
*   **Unified Search Profiles & Location-Specific Rules:** 
    *   Set global job titles, years of experience, blocklist keywords, and scan frequency once (no duplicate data entry or redundant CV uploads).
    *   Configure target countries as rule cards with inline switches (`Remote Only`, `Requires Visa Sponsorship`) and range sliders for the minimum AI Match Score.
    *   **Z-Index & Scrolling Improvements:** Smooth z-index overlays for country lists and maximum height viewport constraints (`max-h-[280px]`) with dark-mode scrollbars to prevent page stretching.
*   **Interactive Dashboard Settings Panel:** 
    *   **Settings Preview:** Read-only summary cards showing current search preferences.
    *   **Per-Country Pause/Resume:** Toggle scanning for individual countries directly from the web client.
    *   **In-place CV File Swapping:** Upload and commit a new resume (PDF or Word) directly to your GitHub repository with one click without re-running the setup wizard.
*   **Telegram WebApp Chat Menu Button:** 
    *   Programmatically registers a persistent "Dashboard 📊" (or "لوحة التحكم 📊") button on the bottom left of the chat window for configured and unconfigured users.
    *   Provides quick, native access to the web dashboard as an overlay sheet inside Telegram.
*   **Congratulations & Countdown Screen:** 
    *   Includes a post-deployment success step in the Setup Wizard.
    *   Automatically fetches the bot username from Telegram (`getMe` API) and triggers a 60-second countdown (boot process of the first GitHub scan workflow) with a direct link to open the bot.
*   **Expanded Target Country Mapping:** Advanced scraper routing for Indeed covering 18 countries (including GCC/Arab countries like UAE, Saudi Arabia, Egypt, Qatar, Kuwait, Oman, Bahrain, Jordan, alongside Europe and Australia).
*   **Bilingual Telegram Bot Commands & Bios:** Full support for `/start`, `/help`, `/status`, `/profiles`, `/pause`, `/resume`, and `/deleteaccount` commands, plus automatic localized bot descriptions and short biographies matching the user's active language preference.
*   **Weekly Activity Summary:** Dispatches a progress check-in to Telegram every 7 days (count of scans completed, listings evaluated) so you know the bot is alive even if job boards are dry.
*   **Interactive Telegram Buttons:** Attach inline `Applied ✅` / `Ignore ❌` buttons to alerts (dynamically localized as `تم التقديم ✅` / `تجاهل ❌` in Arabic mode). Clicking them updates the Telegram message in place and removes the buttons.
*   **Graceful No-CV & No-Gemini Fallbacks:** 
    *   If no Gemini key is provided, the bot sends all postings raw without filtering.
    *   If no CV is provided, the bot generates general safety ratings and recruiter outreach letters based on the job details alone.
*   **Data Deletion & Privacy:** `/deleteaccount` command automatically purges user KV storage settings securely.
*   **Bilingual Setup Welcome Greeting:** Automatically dispatches a welcome notification in the user's preferred language immediately upon setup completion.

---

## 📂 Project Structure

```text
sparkjobs/
├── bot/                # Python Scraper and AI Matcher Bot code
│   ├── data/           # Config JSONs, locally loaded CV text
│   ├── src/            # Bot source scripts (scrapers, matchers, alerts)
│   └── requirements.txt
├── web/                # Next.js local web manager client
│   ├── components/     # Setup Wizard, Upload Panel, and Dashboard
│   ├── pages/          # Landing pages and setup API routers
│   └── tailwind.config.js
└── README.md           # Master documentation (this file)
```

---

## ⚡ Getting Started (Local Development)

### 1. Web Portal Client (Next.js)
The local web manager allows you to enter your credentials, select search criteria (job titles, target countries, job styles, visa status), and compile the initial setup.

```bash
cd web
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to access the portal.

### 2. Scraper Bot (Python)
If you want to run a mock scrape locally instead of on GitHub Actions:

```bash
cd bot
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Configure data/config.json with keys, then execute
python src/main.py
```

---

## 🤖 GitHub Actions Workflow
The bot is designed to be self-sufficient. When the setup wizard completes:
*   A private repository is initialized in your GitHub account.
*   **Secrets** are securely written (`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SCRAPERAPI_KEY`).
*   The **`scan.yml`** workflow is activated, triggering the Python compiler automatically based on your custom frequency settings (default 20 minutes) to fetch new jobs, matching them, and keeping track of duplicates inside `seen_jobs.json`.

---

## 🎨 Design System
SparkJobs follows the exact design language of the **SparkGen** ecosystem:
*   **Background:** Deep dark slate/navy (`#030712`).
*   **Accents:** Vibrant Blue (`#3b82f6` / `text-blue-400`) and Orange (`#f97316` / `text-orange-500`).
*   **Typography:** Bold Outfit (English headers) and Cairo (Arabic headers) with robust line heights (`leading-relaxed`) to prevent character overlap.
*   **Interactive Elements:** Cards with `border-white/[0.05]` outlines and custom searchable tags multi-select inputs.
