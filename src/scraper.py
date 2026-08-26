import os
import re
import time
import random
import hashlib
import requests
from urllib.parse import quote
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from jobspy import scrape_jobs
import pandas as pd
from url_resolver import resolve_canonical_url, is_ats_url

INDEED_DOMAINS = {
    "saudi arabia": "sa.indeed.com",
    "ksa": "sa.indeed.com",
    "united arab emirates": "ae.indeed.com",
    "uae": "ae.indeed.com",
    "egypt": "eg.indeed.com",
    "qatar": "qa.indeed.com",
    "kuwait": "kw.indeed.com",
    "oman": "om.indeed.com",
    "bahrain": "bh.indeed.com",
    "uk": "uk.indeed.com",
    "united kingdom": "uk.indeed.com",
    "germany": "de.indeed.com",
    "france": "fr.indeed.com",
    "canada": "ca.indeed.com",
    "australia": "au.indeed.com",
    "netherlands": "nl.indeed.com",
    "sweden": "se.indeed.com",
    "switzerland": "ch.indeed.com",
    "usa": "indeed.com",
    "united states": "indeed.com",
    "us": "indeed.com",
}

def safe_str(value) -> str:
    """Guard against pandas NaN/None values, returning empty string or trimmed string."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()

def strip_html(text: str) -> str:
    """Purges HTML tags from job descriptions to clean text for AI prompts and fraud detection."""
    if not text or not isinstance(text, str):
        return ""
    if "<" not in text and ">" not in text:
        return text.strip()
    try:
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator=" ").strip()
    except Exception:
        return text.strip()

def is_url_reliable(url: str, site: str = "") -> bool:
    """Returns False for ephemeral Google session tokens, Indeed redirect tracking, or broken URLs."""
    if not url or not isinstance(url, str):
        return False
    u = url.strip().lower()
    if not (u.startswith('http://') or u.startswith('https://')):
        return False
    if "indeed.com/rc/clk" in u:
        return False
    if "indeed.com" in u and "jk=" in u:
        if not re.search(r'jk=([a-f0-9]{8,})', u):
            return False
    if "google" in site.lower() or "google.com" in u:
        if "ibp=htl;jobs" in u or "htlcert" in u or "google.com/search" in u or "google.com/url?" in u:
            return False
    if "weworkremotely.com/categories/" in u and not "/remote-jobs/" in u:
        return False
    return True

def get_scraperapi_proxy(api_key: str) -> str:
    """Returns the ScraperAPI proxy URL string."""
    if not api_key:
        return ""
    return f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001"

def get_indeed_subdomain(location: str) -> str:
    """Resolves native regional Indeed subdomain for given location."""
    loc_lower = str(location or "").lower()
    if re.search(r'\b(egypt|cairo|eg|alexandria|giza|القاهرة|مصر)\b', loc_lower):
        return "eg.indeed.com"
    elif re.search(r'\b(saudi|ksa|riyadh|jeddah|sa|السعودية|الرياض|جدة)\b', loc_lower):
        return "sa.indeed.com"
    elif re.search(r'\b(uae|emirates|dubai|abu dhabi|ae|الإمارات|دبي|أبوظبي)\b', loc_lower):
        return "ae.indeed.com"
    elif re.search(r'\b(qatar|doha|qa|قطر|الدوحة)\b', loc_lower):
        return "qa.indeed.com"
    elif re.search(r'\b(kuwait|kw|الكويت)\b', loc_lower):
        return "kw.indeed.com"
    elif re.search(r'\b(oman|muscat|om|عمان|مسقط)\b', loc_lower):
        return "om.indeed.com"
    elif re.search(r'\b(bahrain|bh|البحرين)\b', loc_lower):
        return "bh.indeed.com"
    elif re.search(r'\b(canada|ca)\b', loc_lower):
        return "ca.indeed.com"
    elif re.search(r'\b(uk|united kingdom|london|england|great britain|gb)\b', loc_lower):
        return "uk.indeed.com"
    elif re.search(r'\b(germany|berlin|munich|de|deutschland)\b', loc_lower):
        return "de.indeed.com"
    elif re.search(r'\b(france|paris|fr)\b', loc_lower):
        return "fr.indeed.com"
    elif re.search(r'\b(australia|sydney|melbourne|au)\b', loc_lower):
        return "au.indeed.com"
    elif re.search(r'\b(netherlands|amsterdam|nl)\b', loc_lower):
        return "nl.indeed.com"
    return "indeed.com"

def scrape_jobspy(site_name: list, search_term: str, location: str, proxy_url: str = "", results_wanted: int = 15, hours_old: int = 2) -> list:
    """
    Scrapes jobs across universal platforms using python-jobspy
    (LinkedIn, Indeed, Google Jobs, Glassdoor, ZipRecruiter).
    """
    jobs_list = []
    try:
        loc_lower = location.lower()
        country_indeed = "usa"
        for k, v in INDEED_DOMAINS.items():
            if k in loc_lower:
                country_indeed = k.replace(" ", "_")
                break

        print(f"Scraping JobSpy ({site_name}) for '{search_term}' in '{location}' (last {hours_old}h)...")
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

        df = scrape_jobs(
            site_name=site_name,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country_indeed,
            proxies=proxies
        )

        if df is not None and not df.empty:
            for _, row in df.iterrows():
                desc = safe_str(row.get("description", ""))
                site = safe_str(row.get("site", "JobSpy")).lower()
                job_id = safe_str(row.get("id", ""))
                url_direct = safe_str(row.get("job_url_direct", ""))
                url_indirect = safe_str(row.get("job_url", ""))
                job_loc = safe_str(row.get("location", "")) or location

                raw_url = ""
                if site == "indeed":
                    # Prefer direct employer career links over Indeed redirect links
                    if url_direct and url_direct.strip().startswith("http"):
                        raw_url = url_direct.strip()
                    else:
                        raw_url = url_indirect if (url_indirect and url_indirect.strip()) else url_direct
                    if raw_url and "indeed.com" in raw_url:
                        raw_url = re.sub(r'(?<=jk=)(indeed-|in-)(?=[a-f0-9])', '', raw_url)
                    if not raw_url or not raw_url.strip():
                        clean_id = re.sub(r'^(indeed-|in-)(?=[a-f0-9])', '', job_id)
                        dom = get_indeed_subdomain(job_loc)
                        raw_url = f"https://{dom}/viewjob?jk={clean_id}"
                else:
                    raw_url = url_direct if (url_direct and url_direct.strip() and url_direct.strip().startswith("http")) else url_indirect

                if site == "google":
                    if not url_direct or "google.com/search" in url_direct:
                        continue

                if not is_url_reliable(raw_url, site):
                    continue

                # Pre-flight canonical URL resolution with actual job location
                canonical_url, is_live, reason = resolve_canonical_url(raw_url, location=job_loc)
                if not is_live:
                    print(f"Discarding dead or closed job ({reason}): {raw_url}")
                    continue

                jobs_list.append({
                    "id": job_id or f"{site}-{hashlib.md5(canonical_url.encode()).hexdigest()[:10]}",
                    "title": safe_str(row.get("title", "")),
                    "company": safe_str(row.get("company", "")),
                    "location": safe_str(row.get("location", "")) or location,
                    "url": canonical_url,
                    "description": strip_html(desc),
                    "source": safe_str(row.get("site", "JobSpy")).title(),
                    "date": datetime.utcnow().isoformat() + "Z"
                })

        print(f"JobSpy found {len(jobs_list)} live jobs.")
    except Exception as e:
        print(f"Error scraping JobSpy: {e}")
    return jobs_list

def scrape_remoteok(search_term: str, proxy_url: str = "") -> list:
    """Scrapes jobs from RemoteOK public API with canonical unfurling."""
    jobs_list = []
    try:
        print(f"Scraping Remote OK for '{search_term}'...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        encoded_tag = quote(search_term.replace(' ', '-'))
        url = f"https://remoteok.com/api?tag={encoded_tag}"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            if "json" not in response.headers.get("Content-Type", "").lower():
                return jobs_list
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict) or not item.get("id"):
                        continue
                    job_url = safe_str(item.get("url", ""))
                    if not is_url_reliable(job_url, "Remote OK"):
                        continue
                    canonical_url, is_live, _ = resolve_canonical_url(job_url)
                    if not is_live:
                        continue
                    jobs_list.append({
                        "id": f"remoteok-{item.get('id', '')}",
                        "title": safe_str(item.get("position", "")),
                        "company": safe_str(item.get("company", "")),
                        "location": "Remote",
                        "url": canonical_url,
                        "description": strip_html(safe_str(item.get("description", ""))),
                        "source": "Remote OK",
                        "date": datetime.utcnow().isoformat() + "Z"
                    })
        print(f"Remote OK found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping Remote OK: {e}")
    return jobs_list

def scrape_remotive(search_term: str, proxy_url: str = "") -> list:
    """Scrapes jobs from Remotive public API with canonical unfurling."""
    jobs_list = []
    try:
        print(f"Scraping Remotive for '{search_term}'...")
        url = "https://remotive.com/api/remote-jobs"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, params={"search": search_term}, proxies=proxies, timeout=10)
        if response.status_code == 200:
            if "json" not in response.headers.get("Content-Type", "").lower():
                return jobs_list
            data = response.json()
            for item in data.get("jobs", []):
                job_url = safe_str(item.get("url", ""))
                if not is_url_reliable(job_url, "Remotive"):
                    continue
                canonical_url, is_live, _ = resolve_canonical_url(job_url)
                if not is_live:
                    continue
                jobs_list.append({
                    "id": f"remotive-{item.get('id', '')}",
                    "title": safe_str(item.get("title", "")),
                    "company": safe_str(item.get("company_name", "")),
                    "location": "Remote",
                    "url": canonical_url,
                    "description": strip_html(safe_str(item.get("description", ""))),
                    "source": "Remotive",
                    "date": datetime.utcnow().isoformat() + "Z"
                })
        print(f"Remotive found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping Remotive: {e}")
    return jobs_list

def scrape_weworkremotely(search_term: str, proxy_url: str = "") -> list:
    """Scrapes jobs from We Work Remotely with category safety."""
    jobs_list = []
    try:
        category = None
        search_words = set(re.findall(r'\b\w+\b', search_term.lower()))
        if any(kw in search_words for kw in ["design", "ux", "ui", "creative", "artist"]):
            category = "remote-design-jobs"
        elif any(kw in search_words for kw in ["programming", "developer", "engineer", "software", "frontend", "backend", "fullstack", "react", "python"]):
            category = "remote-programming-jobs"
        elif any(kw in search_words for kw in ["product", "project", "scrum", "manager", "owner"]):
            category = "remote-product-jobs"
        elif any(kw in search_words for kw in ["support", "customer", "success", "help"]):
            category = "remote-customer-support-jobs"
        elif any(kw in search_words for kw in ["sales", "marketing", "growth", "seo", "ads"]):
            category = "remote-sales-and-marketing-jobs"
        elif any(kw in search_words for kw in ["writer", "copy", "content"]):
            category = "remote-copywriting-jobs"
        elif any(kw in search_words for kw in ["devops", "sysadmin", "sre", "cloud", "infrastructure"]):
            category = "remote-devops-sysadmin-jobs"
        elif any(kw in search_words for kw in ["business", "exec", "ceo", "operations", "finance", "legal"]):
            category = "remote-business-exec-management-jobs"

        if not category:
            return jobs_list

        rss_url = f"https://weworkremotely.com/categories/{category}.rss"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(rss_url, proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            for item in soup.find_all("item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                guid = item.find("guid").text if item.find("guid") is not None else ""
                
                job_url = guid.strip() if (guid and "/remote-jobs/" in guid) else link.strip()
                if not is_url_reliable(job_url, "We Work Remotely"):
                    continue

                match_words = [w.lower() for w in search_term.split() if len(w) > 2]
                title_lower, desc_lower = title.lower(), desc.lower()
                is_match = (search_term.lower() in title_lower or (match_words and all(w in title_lower for w in match_words)))
                
                if is_match:
                    company = "WeWorkRemotely"
                    if ":" in title:
                        parts = title.split(":", 1)
                        if len(parts[0].strip().split()) <= 4:
                            company = parts[0].strip()
                            title = parts[1].strip()

                    raw_id = guid.strip().rstrip('/').split('/')[-1] if guid else hashlib.md5(f"{title}:{company}".encode()).hexdigest()[:12]
                    canonical_url, is_live, _ = resolve_canonical_url(job_url)
                    if not is_live:
                        continue

                    jobs_list.append({
                        "id": f"wwr-{raw_id}",
                        "title": safe_str(title),
                        "company": safe_str(company),
                        "location": "Remote",
                        "url": canonical_url,
                        "description": strip_html(safe_str(desc)),
                        "source": "We Work Remotely",
                        "date": datetime.utcnow().isoformat() + "Z"
                    })
        print(f"We Work Remotely found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping We Work Remotely: {e}")
    return jobs_list

def scrape_direct_ats_dorks(search_term: str, location: str, proxy_url: str = "", results_wanted: int = 15, hours_old: int = 24) -> list:
    """
    Directly targets open ATS domains (Lever, Greenhouse, Ashby, Workable) via Google Jobs
    to guarantee massive pools of 100% direct, open auto-applyable forms.
    """
    ats_jobs = []
    ats_domains = [
        ("lever", "site:jobs.lever.co"),
        ("greenhouse", "site:boards.greenhouse.io"),
        ("ashby", "site:jobs.ashbyhq.com"),
        ("workable", "site:apply.workable.com")
    ]
    
    for platform_name, dork in ats_domains:
        try:
            dork_query = f'{dork} "{search_term}"'
            print(f"Scraping Direct ATS ({platform_name.upper()} via {dork_query})...")
            proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
            df = scrape_jobs(
                site_name=["google"],
                search_term=dork_query,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                proxies=proxies
            )
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    raw_url = safe_str(row.get("job_url_direct", "")) or safe_str(row.get("job_url", ""))
                    if not raw_url or not is_url_reliable(raw_url, platform_name):
                        continue
                    canonical_url, is_live, reason = resolve_canonical_url(raw_url, location=location)
                    if not is_live:
                        continue
                    job_id = safe_str(row.get("id", "")) or f"{platform_name}-{hashlib.md5(canonical_url.encode()).hexdigest()[:10]}"
                    ats_jobs.append({
                        "id": job_id,
                        "title": safe_str(row.get("title", "")),
                        "company": safe_str(row.get("company", "")),
                        "location": safe_str(row.get("location", "")) or location,
                        "url": canonical_url,
                        "description": strip_html(safe_str(row.get("description", ""))),
                        "source": f"Direct ATS ({platform_name.title()})",
                        "ats_platform": platform_name,
                        "date": datetime.utcnow().isoformat() + "Z"
                    })
        except Exception as e:
            print(f"Error scraping ATS dork for {platform_name}: {e}")
            
    print(f"Direct ATS Google Dorks found {len(ats_jobs)} direct live jobs.")
    return ats_jobs

def scrape_himalayas(search_term: str, proxy_url: str = "") -> list:
    """Scrapes direct remote jobs from Himalayas API with direct apply URLs."""
    jobs_list = []
    try:
        print(f"Scraping Himalayas API for '{search_term}'...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        encoded_q = quote(search_term)
        url = f"https://himalayas.app/jobs/api?search={encoded_q}&limit=20"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("jobs", []):
                raw_url = safe_str(item.get("application_url", "")) or safe_str(item.get("url", ""))
                if not raw_url or not is_url_reliable(raw_url, "Himalayas"):
                    continue
                canonical_url, is_live, _ = resolve_canonical_url(raw_url)
                if not is_live:
                    continue
                jobs_list.append({
                    "id": f"himalayas-{item.get('id', hashlib.md5(canonical_url.encode()).hexdigest()[:10])}",
                    "title": safe_str(item.get("title", "")),
                    "company": safe_str(item.get("companyName", "")),
                    "location": "Remote",
                    "url": canonical_url,
                    "description": strip_html(safe_str(item.get("description", ""))),
                    "source": "Himalayas",
                    "date": datetime.utcnow().isoformat() + "Z"
                })
        print(f"Himalayas API found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping Himalayas: {e}")
    return jobs_list

def run_all_scrapes(search_term: str, location: str, scraperapi_key: str = "", hours_old: int = 24) -> list:
    """Aggregates jobs across universal platforms, direct ATS dorks, and remote hubs."""
    all_jobs = []
    seen_urls = set()
    proxy_url = get_scraperapi_proxy(scraperapi_key)
    
    # 1. Direct ATS Google Dorks (Guaranteed open ATS links: Lever, Greenhouse, Ashby, Workable)
    direct_ats = scrape_direct_ats_dorks(search_term, location, proxy_url, results_wanted=15, hours_old=hours_old)
    for j in direct_ats:
        if j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            all_jobs.append(j)

    # 2. Universal Enterprise Job Boards (LinkedIn, Indeed, Google, Glassdoor, ZipRecruiter)
    universal_sites = ["linkedin", "indeed", "google", "glassdoor", "zip_recruiter"]
    universal_jobs = scrape_jobspy(
        site_name=universal_sites,
        search_term=search_term,
        location=location,
        proxy_url=proxy_url,
        hours_old=hours_old
    )
    for j in universal_jobs:
        if j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            all_jobs.append(j)
    
    # 3. Direct Remote Job APIs (Himalayas, RemoteOK, Remotive, WWR)
    is_remote_search = "remote" in location.lower() or "worldwide" in location.lower()
    if is_remote_search:
        for r_job in (scrape_himalayas(search_term, proxy_url) + 
                      scrape_remoteok(search_term, proxy_url) + 
                      scrape_remotive(search_term, proxy_url) + 
                      scrape_weworkremotely(search_term, proxy_url)):
            if r_job["url"] not in seen_urls:
                seen_urls.add(r_job["url"])
                all_jobs.append(r_job)
        
    return all_jobs

if __name__ == "__main__":
    jobs = run_all_scrapes("Product Designer", "Remote", hours_old=24)
    print(f"Total jobs scraped: {len(jobs)}")
