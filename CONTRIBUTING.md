# Contributing to SparkJobs 🚀

Thank you for your interest in contributing to SparkJobs! We welcome community contributions to make job hunting faster, safer, and completely free for everyone.

## How to Add a New Job Board/Source

To add a new job board or platform, follow these modular steps:

1. **Modify `src/scraper.py`**:
   - Create a new scraper function: `scrape_yourplatform(search_term: str) -> list`.
   - Ensure the function returns a list of dictionaries matching this exact unified schema:
     ```python
     {
         "id": "unique-id-string",
         "title": "Job Title",
         "company": "Company Name",
         "location": "Location or Remote",
         "url": "https://example.com/direct-apply-link",
         "description": "Full job description text",
         "source": "Your Platform Name",
         "date": "ISO-timestamp"
     }
     ```
   - Intercept and handle exceptions inside your scraper to prevent any single platform failure from crashing the entire scan run.

2. **Register in `run_all_scrapes`**:
   - Import your new function and append the returned jobs array to the `all_jobs` list.
   - Use `time.sleep(random.uniform(2.0, 4.0))` between platform calls to respect server rate-limits and mimic human browsing.

3. **Verify Locally**:
   - Run the testing suite to verify imports and API integrity:
     ```bash
     python src/main.py
     ```
   - Verify that alerts for your new platform are correctly delivered to your Telegram chat.
