# SparkJobs 🚀
> Smart Automated Job Scan, Match Rating & Telegram Alerts Bot

## 🕌 صدقة جارية / Ongoing Charity
> **"هذا العمل صدقة جارية لي ولكل أمة المسلمين، نسأل الله أن يرزقنا وإياكم الرزق الحلال الطيب."**
> 
> *This project is dedicated as an ongoing charity (Sadaqah Jariyah) for the benefit of the Muslim Ummah. May Allah grant us and you lawful, blessed, and pure livelihood.*

---

SparkJobs is an automated personal assistant designed to query local and international developer job boards (Indeed, Google Jobs) concurrently, score job descriptions against your CV using **Google Gemini AI**, filter out duplicate or fake postings, and deliver clean, structured summaries directly to your Telegram channel.

It is designed to run 100% free on **GitHub Actions** as a cron schedule with no server hosting compute costs. The bot is managed and configured directly from the **SparkGen Admin Dashboard** using a bilingual setup wizard and control panel.

---
## 🛠️ Recent Architectural Upgrades (Updates log)

*   **Security Hardening, 35-Issue Audit Remediation & Modular Architecture (July 2026):**
    *   **AES-256-GCM Token Encryption**: Implemented `cryptoHelper.js` to encrypt all GitHub Personal Access Tokens at rest in Supabase, preventing plain-text credential leaks on database compromise.
    *   **XXE Protection**: Replaced `xml.etree.ElementTree` in `cv_processor.py` with `defusedxml.ElementTree` to prevent XML External Entity and Billion Laughs vulnerabilities.
    *   **Telegram Webhook Authentication & Rate-Limiting**: Enforced `X-Telegram-Bot-Api-Secret-Token` validation and `jobsLimiter` rate-limiting on all webhook endpoints, securing against unauthorized command execution.
    *   **Anti-God-Component Modular Decomposition**: Decomposed backend routes (1,659 lines → 8 modules under `src/routes/jobs/`) and python runner (`main.py` → `config_loader.py`, `title_matcher.py`, `update_checker.py`, `main.py`), keeping 100% of files under the 400-line ceiling.
    *   **In-Memory Deduplication**: Refactored `deduplicator.py` from per-job disk reads to an in-memory dictionary pattern with single end-of-cycle file persistence, eliminating O(N²) I/O bottlenecks.
    *   **Telegram 64-Byte Payload Safety**: Implemented MD5 truncation on button callback_data to prevent Telegram silent payload drops on long job IDs.
    *   **URL HTML Escaping & Protocol Guards**: Enforced strict `html.escape()` and protocol checks on application links in Telegram alert templates.
    *   **GitHub Actions Concurrency Guard**: Added `concurrency` groups to `scan.yml` to prevent race conditions during concurrent git pushes.

*   **Proxy Resilience, BS4 RSS Parsing, Robust DOCX parsing & DB Security (July 2026):**
    *   **Proxy Resilience for Free APIs**: Added ScraperAPI proxy routing support to all scraper functions (`scrape_remoteok`, `scrape_remotive`, `scrape_weworkremotely`) to bypass Cloudflare rate-limit blocks inside GitHub Actions.
    *   **BS4 RSS XML Parsing**: Refactored the WeWorkRemotely scraper to parse XML using BeautifulSoup (`BeautifulSoup(..., "xml")`) instead of strict ElementTree, preventing parser crashes on unescaped HTML description elements.
    *   **Indeed Subdomain Fix**: Standardized Indeed country fallback to `"usa"` instead of `"worldwide"` (which Indeed does not support).
    *   **Robust XML DOCX Parser**: Replaced single-file main XML extraction with a recursive zip traversal that extracts text from all `.xml` documents (document, footnotes, headers, footers) regardless of namespaced tag variants.
    *   **Model Cascade Parity**: Added `gemini-3.1-flash-lite` to the bot's matching cascade to maintain alignment with backend validator features.
    *   **GitHub Token Update checks**: Configured template update queries in `main.py` to authenticate using `GITHUB_TOKEN`, resolving runner rate-limiting.
    *   **Seen Jobs Pull Rebase**: Added a `git pull --rebase` step to `scan.yml` before committing and pushing bot state, preventing non-fast-forward push rejections.
*   **Template Sync Fallbacks, Webhook Validation, Strict Google Jobs Filters & CV Cleanup (July 2026):**
    *   **Master Repository Sync Correction**: Aligned default fallback templates in `jobsRoutes.js` to point to `Youssseef/SparkJobs` as the master repository instead of legacy references, ensuring the "Sync Bot Code" feature fetches the correct codebase.
    *   **CV Extension Cleanups**: Implemented automatic directory scans on CV updates via `write-config` to check and delete older resume formats (e.g. removing old `.pdf` when uploading `.docx`). This prevents precedence collisions where the python runner preferred old ghost files.
    *   **Strict Google Jobs Redirect Filters**: Refactored Google Jobs scraper outputs in `scraper.py` to enforce that listings must have a direct employer ATS link (`job_url_direct`) and discard generic Google Jobs redirect URLs, which solved wrong job details and decaying URLs in Telegram.
    *   **Telegram Webhook Token Integration**: Appended bot token queries to the Telegram webhook registration URL. This allows the backend to capture token values dynamically and reply to messages even during early onboarding or guest states.
*   **Role-Core Filtering, URL Reliability & NaN Guards (July 2026):**
    *   **Role-Core-Word Title Filtering**: Refactored `is_title_relevant` to extract the core role word (e.g., `designer` from `Product Designer`) and enforce that it appears in the job title, stopping cross-field contamination (e.g. "Product Manager" matching a "Product Designer" search).
    *   **Google Jobs URL Ephemeral Filtering**: Discards Google Jobs session-redirect URLs (`ibp=htl;jobs`) that expire within hours and lead to mismatched/wrong jobs, ensuring only reliable direct employer links are alert targets.
    *   **NaN & String Guards**: Added `safe_str` helper to guard against pandas `NaN` values, preventing literal `"nan"` strings in company/location alerts.
    *   **CV Fallback Retrieval**: Enhanced `get_cv_text` to automatically fallback to `default_cv` files if the target version pointer is missing, keeping the CV parser robust.
*   **Indeed URL Resolving & Relevance Keywords (July 2026):**
    *   **Direct Indeed URLs**: Reconstructed clean Indeed URLs (`https://www.indeed.com/viewjob?jk={id}`) inside `scraper.py` using JobSpy's unique keys to prevent redirected or expired links.
    *   **Discipline Match Filters**: Removed generic domain nouns (`designer`, `developer`, `engineer`, `manager`) from title pre-filtering `fillers` list in `main.py` so that keyword overlap logic checks actual disciplines correctly.
    *   **Template Update Alarms**: Built a non-blocking update checking mechanism in `main.py` that hashes the local script and queries GitHub's API to detect if a template release is available, alerting the user once on Telegram to go sync their code.
*   **GitHub Action Dispatch, Security Hardening & CSP Proxying (July 2026):**
    *   **Credential Sanitization in config.json**: Strips `gemini_api_key`, `telegram_bot_token`, and `scraperapi_key` plain-text variables from committed config files to satisfy GitGuardian security scanners.
    *   **GitHub Action Secrets fallback**: Enabled `main.py` to securely read credentials from GitHub Actions secrets (injected as env variables in `scan.yml`) with fallback support.
    *   **Master/Main Branch Fallback**: Setup manual action dispatch logic with master fallback support to support repositories regardless of their default branch name.
    *   **Automatic Repository Reuse**: Configured repository creation route to automatically check and reuse existing user repositories on name collisions instead of failing.
    *   **Server-Side API Proxying**: Redirected external browser API calls (GitHub repository files and Telegram getMe bot lookups) through backend proxy endpoints to satisfy client-side browser CSP `connect-src` whitelist checks.
    *   **Logger Database Write Guard**: Configured client-side logging to skip database persistence for guest/unauthenticated sessions, preventing 403 DB forbidden errors.
*   **Active Telemetry Aggregator & Outcomes Reporter (July 2026):**
    *   **Aggregate Match Scores & Missing Skills:** Updated `main.py` bot execution cycle to log average matching scores per target job title and compile lists of missing technical keywords in user CVs.
    *   **Scraping Sources Tracking:** Records job posting providers (Indeed, Google Jobs, etc.) to evaluate source quality.
    *   **Telemetry Ping API Transmission:** Transmits telemetry aggregates automatically to the server at the end of every scan cycle via a secure POST ping protected by the `SPARKJOBS_PING_SECRET` token.
*   **Premium Layout Spacing & Responsive Grid Updates (July 2026):**
    *   **Unified Spacing & Padding:** Aligned page padding to `px-6 sm:px-8` (matching the nav bar's responsive widths) and increased vertical margins to `py-12 md:py-16` to clear the sticky header elegantly across all viewport widths.
    *   **Tightened Hierarchy:** Grouped breadcrumbs and title elements in a `.space-y-2` container to keep them visually unified rather than split apart by global column styles.
    *   **Language-Aware Typography Leading:** Replaced static `leading-relaxed` with dynamic `language === 'ar' ? 'leading-relaxed' : 'leading-tight'` logic, maintaining Cairo font readability while tightening English headers.
    *   **Active Grid Breakpoint Tuning (`lg` -> `md`):** Shifted 2-column layout activation to `md` (768px) to eliminate large empty spaces on the right side of tablet/medium screens and keep the Setup Wizard card properly aligned.
    *   **Vertical Alignment & SetupWizard Spacing:** Reverted grid vertical alignment to centered `items-center` mode. Compacted the SetupWizard card wrapper padding from `p-8` to `p-5 sm:p-6` and header margin to `mb-6` to make the form container more compact and prevent top overlaps.
    *   **Compact Standalone Spacing:** Reduced root vertical padding on the standalone client to `py-8 md:py-12` and horizontal padding to `px-4 sm:px-6` to make it more compact.
    *   **UX Writing Simplification & Icon-Only CTA:** Shortened labels, placeholders, and descriptions across all 5 wizard steps (e.g. `Target Years of Experience` -> `Experience Level`, `Automatic Scan Frequency` -> `Scan Frequency`, `Requires Visa Sponsorship` -> `Visa Sponsorship`). Replaced the text-heavy `+ Add Country` button with a clean `w-8 h-8 rounded-lg` square icon-only button to improve column alignment.
    *   **Country Card Grid Shift:** Shifted internal country card controls grid to stacked layout (`grid-cols-1`) for tablet and mobile sizes (under `lg:grid-cols-2` / 1024px) to prevent toggle-switch overlaps.
*   **State Persistence & Ephemeral Storage Fix:** The GitHub Actions workflow (`scan.yml`) now commits and pushes both `seen_jobs.json` (deduplication database) and `status_tracker.json` (dashboard stats) back to the user's private repository after every scan. This ensures that dashboard metrics correctly accumulate over time instead of resetting on ephemeral runner shutdowns.
*   **Security Isolation & Dev Environment Protection:** Local testing files (like `test_live_alert.py`) are configured to load keys securely from environment variables (`os.environ.get`) instead of hardcoded strings, and are permanently ignored via `.gitignore` to prevent accidental credential leaks.
*   **New Google GenAI SDK Migration:** Migrated the bot from the legacy `google-generativeai` package to the new `google.genai` SDK for future-proof API compatibility.
*   **Gemini Model Cascade Fallback:** Configured a resilient AI matching pipeline starting with `gemini-2.5-flash` as primary, and automatically cascading to `gemini-2.5-flash-lite` and `gemini-3.1-flash-lite` in case of rate limits or model downtime.
*   **Binary CV Parsing (.pdf & .docx):** Replaced manual plain text variables with support for binary file uploads. Features a pure-Python custom DOCX parser utilizing python's built-in `zipfile` and `xml.etree.ElementTree` namespaces to extract clean text without bloating the action runner's dependencies.
*   **Settings Save & Secrets Protection Guard (July 2026):**
    *   **Partial Secrets Update Safety**: Configured `/setup/write-secrets` API to only update secrets that have explicitly non-empty values in the request payload. Empty values are ignored, preventing settings updates from silently overwriting active GitHub Actions secrets with blank values.
    *   **Secret Status Verification**: Added `/setup/list-secrets` backend API to verify the presence of active keys in GitHub Secrets. The frontend Settings dashboard queries this on mount, displaying a secure placeholder and mask (`•••••••• (Saved in GitHub Secrets)`) to communicate key status while keeping the inputs editable without risks.
*   **Resilient Job Scraper & Field Filtering (July 2026):**
    *   **Dynamic RSS Category Routing**: Replaced hardcoded Programming category feeds on We Work Remotely with dynamic category lookup based on search term keywords (e.g. routing Design category for Product Designers).
    *   **Pre-AI Title Relevance Filter**: Added keyword overlap checks (`is_title_relevant`) to discard off-field scraped jobs instantly before running expensive AI matches, protecting Gemini key usage quotas and preventing off-field job alerts.
    *   **Job Scraper Exception Isolation**: Wrapped the job processing loop in a `try-except` block to ensure any individual job processing or API call failures do not crash the entire scheduled scan run.
    *   **Telegram Webhook Status Path Correction**: Fixed incorrect path reference (`bot/data/status_tracker.json` -> `data/status_tracker.json`) in the Telegram webhook receiver command handler for `/status`.


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
├── .github/workflows/
│   └── scan.yml        # GitHub Actions serverless cron runner configuration
├── data/               # Local folder containing active config/CV/seen logs
│   ├── config.json
│   └── status_tracker.json
├── src/                # Python scraper, matcher, and alert bot scripts
│   ├── ai_matcher.py
│   ├── main.py
│   ├── scraper.py
│   └── telegram_bot.py
├── requirements.txt    # Python dependencies manifest
└── README.md           # Master documentation (this file)
```

---

## ⚡ Getting Started (Local Development)

### 1. Web Portal Client (Admin Dashboard)
The SparkJobs web portal interface is embedded directly inside the **SparkGen Admin Dashboard** (`sparkgen-admin`). It allows you to enter your credentials, configure target job titles and countries, and trigger setup flows.

```bash
cd sparkgen-admin
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) (or configured dev port) to access the management portal.

### 2. Scraper Bot Worker (Python)
To run a manual or mock scan cycle locally instead of on GitHub Actions:

```bash
cd sparkjobs
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run scan cycle
python src/main.py
```
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
