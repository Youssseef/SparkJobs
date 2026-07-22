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

def safe_str(value) -> str:
    """
    Guard against pandas NaN/None values, returning empty string or trimmed string.
    """
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()

def strip_html(text: str) -> str:
    """
    M-12 & M-15 Fix: Purges HTML tags from job descriptions to clean text for AI prompts and fraud word counts.
    """
    if not text or not isinstance(text, str):
        return ""
    if "<" not in text and ">" not in text:
        return text.strip()
    try:
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(separator=" ").strip()
    except Exception:
        return text.strip()

def is_url_reliable(url: str, site: str) -> bool:
    """
    Returns False for Google session-redirect URLs that decay within hours,
    Indeed click-tracking redirect URLs, unformatted URLs, or generic category/search index landing pages.
    """
    if not url or not isinstance(url, str):
        return False
    u = url.strip().lower()
    if not (u.startswith('http://') or u.startswith('https://')):
        return False
    if "indeed.com/rc/clk" in u:
        return False
    if "indeed.com" in u and "jk=" in u:
        jk_match = re.search(r'jk=([a-f0-9]{8,})', u)
        if not jk_match:
            return False
    if "google" in site.lower() or "google.com" in u:
        if "ibp=htl;jobs" in u or "htlcert" in u or "google.com/search" in u or "google.com/url?" in u:
            return False
    if "weworkremotely.com/categories/" in u and not "/remote-jobs/" in u:
        return False
    return True

def get_scraperapi_proxy(api_key: str) -> str:
    """
    Returns the ScraperAPI proxy URL string.
    """
    if not api_key:
        return ""
    return f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001"

def scrape_jobspy(site_name: list, search_term: str, location: str, proxy_url: str = "", results_wanted: int = 15) -> list:
    """
    Scrapes jobs using python-jobspy (Indeed, Glassdoor, ZipRecruiter, Google Jobs).
    """
    jobs_list = []
    try:
        # M-08 Note: Indeed has no country subdomain for Jordan — defaults to "usa"
        country_map = {
            "germany": "germany",
            "united kingdom": "uk",
            "uk": "uk",
            "united states": "usa",
            "us": "usa",
            "usa": "usa",
            "canada": "canada",
            "france": "france",
            "saudi arabia": "saudi arabia",
            "ksa": "saudi arabia",
            "united arab emirates": "united arab emirates",
            "uae": "united arab emirates",
            "egypt": "egypt",
            "qatar": "qatar",
            "kuwait": "kuwait",
            "oman": "oman",
            "bahrain": "bahrain",
            "jordan": "usa", # Indeed has no jo.indeed.com subdomain, fallback to global
            "netherlands": "netherlands",
            "sweden": "sweden",
            "switzerland": "switzerland",
            "australia": "australia",
            "worldwide": "usa",
            "remote": "usa",
        }

        country_indeed = "usa"
        loc_lower = location.lower()
        for k, v in country_map.items():
            if k in loc_lower:
                country_indeed = v
                break

        print(f"Scraping JobSpy sites {site_name} for '{search_term}' in '{location}'...")
        
        proxies = {}
        if proxy_url:
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

        df = scrape_jobs(
            site_name=site_name,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=24,
            country_indeed=country_indeed,
            proxies=proxies if proxy_url else None
        )

        if df is not None and not df.empty:
            for _, row in df.iterrows():
                desc = row.get("description", "")
                if pd.isna(desc):
                    desc = ""

                site = safe_str(row.get("site", "JobSpy")).lower()
                job_id = safe_str(row.get("id", ""))
                url_direct = safe_str(row.get("job_url_direct", ""))
                url_indirect = safe_str(row.get("job_url", ""))
                
                if site == "indeed":
                    # Track A Fix: Prefer canonical Indeed viewjob URL (job_url_indirect) over employer ATS link
                    url = url_indirect if (url_indirect and url_indirect.strip()) else url_direct
                    if url and "indeed.com" in url:
                        # Anchored regex to clean prefixed job keys safely without stripping internal substrings
                        url = re.sub(r'(?<=jk=)(indeed-|in-)(?=[a-f0-9])', '', url)
                    if not url or not url.strip():
                        clean_id = re.sub(r'^(indeed-|in-)(?=[a-f0-9])', '', job_id)
                        url = f"https://www.indeed.com/viewjob?jk={clean_id}"
                else:
                    url = url_direct if (url_direct and url_direct.strip()) else url_indirect

                if site == "google":
                    if not url_direct or not url_direct.strip():
                        continue
                    if "google.com/search" in url_direct:
                        continue
                elif not is_url_reliable(url, site):
                    continue

                jobs_list.append({
                    "id": job_id,
                    "title": safe_str(row.get("title", "")),
                    "company": safe_str(row.get("company", "")),
                    "location": safe_str(row.get("location", "")),
                    "url": url,
                    "description": strip_html(safe_str(desc)),
                    "source": safe_str(row.get("site", "JobSpy")),
                    "date": datetime.now().isoformat()
                })
        
        print(f"JobSpy found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping JobSpy: {e}")
        
    return jobs_list

def scrape_remoteok(search_term: str, proxy_url: str = "") -> list:
    """
    H-03 Fix: URL-encodes search_term query parameter to prevent broken requests.
    """
    jobs_list = []
    try:
        print(f"Scraping Remote OK for '{search_term}'...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        encoded_tag = quote(search_term.replace(' ', '-'))
        url = f"https://remoteok.com/api?tag={encoded_tag}"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            # M-05 Fix: Guard against Cloudflare HTML challenge pages returning 200 OK
            content_type = response.headers.get("Content-Type", "")
            if "json" not in content_type.lower():
                print(f"Remote OK returned non-JSON response ({content_type}). Skipping.")
                return jobs_list
            try:
                data = response.json()
            except Exception as json_err:
                print(f"Failed to parse Remote OK JSON response: {json_err}")
                return jobs_list
            if isinstance(data, list) and len(data) > 1:
                for item in data[1:]:
                    job_url = safe_str(item.get("url", ""))
                    if not is_url_reliable(job_url, "Remote OK"):
                        continue
                    jobs_list.append({
                        "id": f"remoteok-{item.get('id', '')}",
                        "title": safe_str(item.get("position", "")),
                        "company": safe_str(item.get("company", "")),
                        "location": "Remote",
                        "url": job_url,
                        "description": strip_html(safe_str(item.get("description", ""))),
                        "source": "Remote OK",
                        "date": datetime.now().isoformat()
                    })
        print(f"Remote OK found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping Remote OK: {e}")
    return jobs_list

def scrape_remotive(search_term: str, proxy_url: str = "") -> list:
    """
    H-03 Fix: Uses requests params dict for proper URL parameter encoding.
    H-04 Fix: Content-Type validation to skip non-JSON/Cloudflare challenge pages.
    """
    jobs_list = []
    try:
        print(f"Scraping Remotive for '{search_term}'...")
        url = "https://remotive.com/api/remote-jobs"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, params={"search": search_term}, proxies=proxies, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "json" not in content_type.lower():
                print(f"Remotive returned non-JSON response ({content_type}). Skipping.")
                return jobs_list
            data = response.json()
            jobs = data.get("jobs", [])
            for item in jobs:
                job_url = safe_str(item.get("url", ""))
                if not is_url_reliable(job_url, "Remotive"):
                    continue
                jobs_list.append({
                    "id": f"remotive-{item.get('id', '')}",
                    "title": safe_str(item.get("title", "")),
                    "company": safe_str(item.get("company_name", "")),
                    "location": "Remote",
                    "url": job_url,
                    "description": strip_html(safe_str(item.get("description", ""))),
                    "source": "Remotive",
                    "date": datetime.now().isoformat()
                })
        print(f"Remotive found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping Remotive: {e}")
    return jobs_list

def scrape_weworkremotely(search_term: str, proxy_url: str = "") -> list:
    """
    Scrapes jobs from We Work Remotely RSS Feed.
    H-05 Fix: Renamed inner loop url variable to job_url to prevent variable shadowing.
    H-09 Fix: Added explicit log for non-200 HTTP response codes.
    L-11 Fix: Stripped trailing slashes before splitting GUID to prevent ID collisions.
    """
    jobs_list = []
    try:
        print(f"Scraping We Work Remotely for '{search_term}'...")
        
        category = "remote-programming-jobs"
        search_words = set(re.findall(r'\b\w+\b', search_term.lower()))
        if any(kw in search_words for kw in ["design", "ux", "ui", "creative", "artist", "illustrator"]):
            category = "remote-design-jobs"
        elif any(kw in search_words for kw in ["product", "project", "owner", "scrum", "manager"]):
            category = "remote-product-jobs"
        elif any(kw in search_words for kw in ["support", "customer", "success", "help"]):
            category = "remote-customer-support-jobs"
        elif any(kw in search_words for kw in ["sales", "marketing", "growth", "seo", "ads"]):
            category = "remote-sales-and-marketing-jobs"
        elif any(kw in search_words for kw in ["writer", "copy", "content"]):
            category = "remote-copywriting-jobs"
        elif any(kw in search_words for kw in ["devops", "sysadmin", "sre", "cloud", "infrastructure"]):
            category = "remote-devops-sysadmin-jobs"
        elif any(kw in st_lower for kw in ["business", "exec", "ceo", "operations", "finance", "legal"]):
            category = "remote-business-exec-management-jobs"
            
        rss_url = f"https://weworkremotely.com/categories/{category}.rss"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(rss_url, proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
            for item in items:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                guid = item.find("guid").text if item.find("guid") is not None else ""
                
                # Prioritize direct job post link over generic category links
                job_url = ""
                if guid and (guid.startswith("http://") or guid.startswith("https://")) and "/remote-jobs/" in guid:
                    job_url = guid.strip()
                elif link and (link.startswith("http://") or link.startswith("https://")) and "/remote-jobs/" in link:
                    job_url = link.strip()
                else:
                    job_url = guid.strip() if (guid and guid.strip()) else link.strip()

                if not is_url_reliable(job_url, "We Work Remotely"):
                    continue

                # M-11 Fix: Word-level search so 'Product Designer' matches 'Designer, Product'
                search_words = [w.lower() for w in search_term.split() if len(w) > 2]
                title_lower = title.lower()
                desc_lower = desc.lower()
                is_match = (
                    search_term.lower() in title_lower or search_term.lower() in desc_lower or
                    (search_words and all(w in title_lower or w in desc_lower for w in search_words))
                )
                if is_match:
                    company = "WeWorkRemotely"
                    if ":" in title:
                        parts = title.split(":", 1)
                        company = parts[0].strip()
                        title = parts[1].strip()

                    # L-11 Fix: Strip trailing slashes before splitting GUID/link
                    if guid and '/' in guid:
                        raw_id = guid.strip().rstrip('/').split('/')[-1]
                    elif link and '/' in link:
                        raw_id = link.strip().rstrip('/').split('/')[-1]
                    else:
                        raw_id = hashlib.md5(f"{title}:{company}".encode()).hexdigest()[:12]

                    jobs_list.append({
                        "id": f"wwr-{raw_id}",
                        "title": safe_str(title),
                        "company": safe_str(company),
                        "location": "Remote",
                        "url": job_url,
                        "description": strip_html(safe_str(desc)),
                        "source": "We Work Remotely",
                        "date": datetime.now().isoformat()
                    })
        else:
            print(f"We Work Remotely returned HTTP {response.status_code}. Skipping.")
        print(f"We Work Remotely found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping We Work Remotely: {e}")
    return jobs_list

def run_all_scrapes(search_term: str, location: str, scraperapi_key: str = "") -> list:
    all_jobs = []
    proxy_url = get_scraperapi_proxy(scraperapi_key)
    
    all_jobs.extend(scrape_remoteok(search_term, proxy_url))
    time.sleep(random.uniform(1.5, 3.0))
    
    all_jobs.extend(scrape_remotive(search_term, proxy_url))
    time.sleep(random.uniform(1.5, 3.0))
    
    all_jobs.extend(scrape_weworkremotely(search_term, proxy_url))
    time.sleep(random.uniform(1.5, 3.0))
    
    jobspy_sites = ["google"]
    if scraperapi_key:
        jobspy_sites.extend(["indeed", "zip_recruiter"])
    else:
        print("Warning: No ScraperAPI key provided. Skipping Indeed and ZipRecruiter scrapes.")
        
    jobspy_jobs = scrape_jobspy(
        site_name=jobspy_sites,
        search_term=search_term,
        location=location,
        proxy_url=proxy_url
    )
    all_jobs.extend(jobspy_jobs)
    
    return all_jobs

if __name__ == "__main__":
    jobs = run_all_scrapes("React", "Remote")
    print(f"Total jobs scraped: {len(jobs)}")
