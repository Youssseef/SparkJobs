import re
import json
import urllib.parse
import urllib.request
try:
    from src.url_resolver import is_ats_url, detect_ats_platform
except ImportError:
    from url_resolver import is_ats_url, detect_ats_platform

PREFERRED_ATS_DOMAINS = [
    "greenhouse.io", "lever.co", "smartrecruiters.com", "ashbyhq.com",
    "workable.com", "bamboohr.com", "recruitee.com", "breezy.hr",
    "jobvite.com", "workday.com", "myworkdayjobs.com", "applytojob.com"
]

def search_scraperapi(query: str, api_key: str) -> list[str]:
    """Uses ScraperAPI Google Search endpoint if key provided."""
    if not api_key:
        return []
    try:
        url = f"http://api.scraperapi.com/structured/google/search?api_key={api_key}&query={urllib.parse.quote_plus(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "SparkJobs/2.4.2"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = data.get("organic_results", [])
            return [r.get("link", "") for r in results if r.get("link")]
    except Exception as e:
        print(f"[ATS Resolver] ScraperAPI error: {e}")
        return []

def search_duckduckgo(query: str) -> list[str]:
    """Fallback search using DuckDuckGo HTML endpoint."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            links = re.findall(r'href="([^"]*uddg=[^"]*)"', html)
            cleaned = []
            for l in links:
                m = re.search(r'uddg=([^&]+)', l)
                if m:
                    target = urllib.parse.unquote(m.group(1))
                    if not any(d in target for d in ['duckduckgo.com', 'google.com', 'bing.com', 'linkedin.com']):
                        cleaned.append(target)
            return cleaned
    except Exception as e:
        print(f"[ATS Resolver] DDG error: {e}")
        return []

def search_jobspy_google(company: str, title: str, location: str = "") -> list[str]:
    """Uses JobSpy Google search to look up direct ATS postings."""
    try:
        from jobspy import scrape_jobs
        dork_query = f'"{company}" "{title}" careers'
        df = scrape_jobs(
            site_name=["google"],
            search_term=dork_query,
            location=location,
            results_wanted=3,
            hours_old=72
        )
        if df is not None and not df.empty:
            urls = []
            for _, row in df.iterrows():
                u_dir = str(row.get("job_url_direct") or "").strip()
                u_ind = str(row.get("job_url") or "").strip()
                if u_dir and u_dir.startswith("http"):
                    urls.append(u_dir)
                elif u_ind and u_ind.startswith("http") and "google.com" not in u_ind:
                    urls.append(u_ind)
            return urls
    except Exception as e:
        print(f"[ATS Resolver] JobSpy Google fallback note: {e}")
    return []

def is_valid_direct_ats_url(url: str) -> bool:
    """Verifies that a resolved URL is a genuine job posting rather than a generic home page."""
    if not url or not isinstance(url, str):
        return False
    u = url.lower()
    if any(b in u for b in ["linkedin.com", "google.com", "bing.com", "duckduckgo.com"]):
        return False
    if is_ats_url(u):
        if any(p in u for p in ['/jobs/', '/job/', '/positions/', '/opening/', '/apply/', '/careers/']):
            return True
        if re.search(r'/[0-9a-f-]{6,}', u):
            return True
        return False
    if any(p in u for p in ['/careers/', '/jobs/', '/career/']) and re.search(r'/[a-z0-9_-]{4,}', u):
        return True
    return False

def resolve_direct_ats_link(company: str, title: str, location: str = "", scraperapi_key: str = "") -> str | None:
    """
    Resolves the direct employer ATS or career URL for an external job.
    Eliminates reliance on LinkedIn authwall / sign-in modals.
    """
    clean_company = re.sub(r'[^\w\s-]', '', str(company or '')).strip()
    clean_title = re.sub(r'[^\w\s-]', '', str(title or '')).strip()
    if not clean_company or not clean_title:
        return None

    # Strategy 1: Targeted ATS query via Google Jobs (JobSpy)
    google_candidates = search_jobspy_google(clean_company, clean_title, location)
    for u in google_candidates:
        if is_valid_direct_ats_url(u):
            return u

    # Strategy 2: ScraperAPI Google ATS search
    ats_domains_str = " OR ".join([f"site:{d}" for d in ["greenhouse.io", "lever.co", "smartrecruiters.com", "ashbyhq.com", "workable.com", "bamboohr.com"]])
    query = f'"{clean_company}" "{clean_title}" ({ats_domains_str})'
    candidates = search_scraperapi(query, scraperapi_key)
    for u in candidates:
        if is_valid_direct_ats_url(u):
            return u

    # Strategy 3: DuckDuckGo HTML search
    ddg_candidates = search_duckduckgo(query)
    for u in ddg_candidates:
        if is_valid_direct_ats_url(u):
            return u

    # Strategy 4: Direct company career portal search
    query_broad = f'"{clean_company}" "{clean_title}" careers apply'
    broad_candidates = search_scraperapi(query_broad, scraperapi_key) if scraperapi_key else search_duckduckgo(query_broad)
    for u in broad_candidates:
        if is_valid_direct_ats_url(u):
            return u

    return None
