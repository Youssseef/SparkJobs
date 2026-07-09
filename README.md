# SparkJobs 🚀
> Smart Automated Job Scan, Match Rating & Telegram Alerts Bot

SparkJobs is an automated personal assistant designed to query local and international developer job boards (Indeed, Google Jobs) concurrently, score job descriptions against your CV using **Google Gemini AI**, filter out duplicate or fake postings, and deliver clean, structured summaries directly to your Telegram channel.

It consists of two main parts:
1. **`web/`**: A Next.js (React + Tailwind CSS) client portal that runs locally. It features a bilingual setup wizard to easily initialize the bot, generate a repository on your behalf, write configurations, and manage active searches.
2. **`bot/`**: A Python-based scraping and AI classification bot designed to be hosted 100% free on **GitHub Actions** as a cron schedule (running every 20 minutes) with no server hosting costs.

---

## 📂 Project Structure

```text
sparkjobs/
├── bot/                # Python Scraper and AI Matcher Bot code
│   ├── .github/        # GitHub Actions workflows (cron runners)
│   ├── data/           # Config JSONs, locally loaded CV text
│   ├── src/            # Bot source scripts (scrapers, matchers, alerts)
│   └── requirements.txt
├── web/                # Next.js local web manager client
│   ├── components/     # Setup Wizard and Dashboard panels
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
* A private repository is initialized in your GitHub account.
* **Secrets** are securely written (`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SCRAPERAPI_KEY`).
* The **`scan.yml`** workflow is activated, triggering the Python compiler automatically every 20 minutes to fetch new jobs, matching them, and keeping track of duplicates inside `seen_jobs.json`.

---

## 🎨 Design System
SparkJobs follows the exact design language of the **SparkGen** ecosystem:
* **Background:** Deep dark slate/navy (`#030712`).
* **Accents:** Vibrant Blue (`#3b82f6` / `text-blue-400`) and Orange (`#f97316` / `text-orange-500`).
* **Typography:** Bold Outfit (English headers) and Cairo (Arabic headers) with robust line heights (`leading-relaxed`) to prevent character overlap.
* **Interactive Elements:** Cards with `border-white/[0.05]` outlines and custom searchable tags multi-select inputs.
