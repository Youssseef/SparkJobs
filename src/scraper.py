import os
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

def is_url_reliable(url: str, site: str) -> bool:
    """
    Returns False for Google session-redirect URLs that decay within hours.
    """
    if not url or not url.strip():
        return False
    if "google" in site.lower() and "ibp=htl;jobs" in url:
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
                
                url = url_direct if (url_direct and url_direct.strip()) else url_indirect

                if site == "indeed":
                    if not url or not url.strip():
                        clean_id = job_id.replace("indeed-", "").replace("in-", "")
                        url = f"https://www.indeed.com/viewjob?jk={clean_id}"
                    elif "indeed.com" in url and "jk=" in url:
                        url = url.replace("jk=in-", "jk=").replace("jk=indeed-", "jk=")

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
                    "description": safe_str(desc),
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
            data = response.json()
            if isinstance(data, list) and len(data) > 1:
                for item in data[1:]:
                    jobs_list.append({
                        "id": f"remoteok-{item.get('id', '')}",
                        "title": item.get("position", ""),
                        "company": item.get("company", ""),
                        "location": "Remote",
                        "url": item.get("url", ""),
                        "description": item.get("description", ""),
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
    """
    jobs_list = []
    try:
        print(f"Scraping Remotive for '{search_term}'...")
        url = "https://remotive.com/api/remote-jobs"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, params={"search": search_term}, proxies=proxies, timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get("jobs", [])
            for item in jobs:
                jobs_list.append({
                    "id": f"remotive-{item.get('id', '')}",
                    "title": item.get("title", ""),
                    "company": item.get("company_name", ""),
                    "location": "Remote",
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
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
    """
    jobs_list = []
    try:
        print(f"Scraping We Work Remotely for '{search_term}'...")
        
        category = "remote-programming-jobs"
        st_lower = search_term.lower()
        if any(kw in st_lower for kw in ["design", "ux", "ui", "creative", "artist", "illustrator"]):
            category = "remote-design-jobs"
        elif any(kw in st_lower for kw in ["product", "project", "owner", "scrum", "manager"]):
            category = "remote-product-jobs"
        elif any(kw in st_lower for kw in ["support", "customer", "success", "help"]):
            category = "remote-customer-support-jobs"
        elif any(kw in st_lower for kw in ["sales", "marketing", "growth", "seo", "ads"]):
            category = "remote-sales-and-marketing-jobs"
        elif any(kw in st_lower for kw in ["writer", "copy", "content"]):
            category = "remote-copywriting-jobs"
        elif any(kw in st_lower for kw in ["devops", "sysadmin", "sre", "cloud", "infrastructure"]):
            category = "remote-devops-sysadmin-jobs"
        elif any(kw in st_lower for kw in ["business", "exec", "ceo", "operations", "finance", "legal"]):
            category = "remote-business-exec-management-jobs"
            
        url = f"https://weworkremotely.com/categories/{category}.rss"
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        response = requests.get(url, proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
            for item in items:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                guid = item.find("guid").text if item.find("guid") is not None else ""
                
                url = link if (link and link.strip()) else guid
                if not url or not url.strip():
                    url = guid

                if search_term.lower() in title.lower() or search_term.lower() in desc.lower():
                    company = "WeWorkRemotely"
                    if ":" in title:
                        parts = title.split(":", 1)
                        company = parts[0].strip()
                        title = parts[1].strip()

                    # L-07 Fix: Deterministic fallback hash instead of random integer
                    if guid and '/' in guid:
                        raw_id = guid.split('/')[-1]
                    elif link and '/' in link:
                        raw_id = link.split('/')[-1]
                    else:
                        raw_id = hashlib.md5(f"{title}:{company}".encode()).hexdigest()[:12]

                    jobs_list.append({
                        "id": f"wwr-{raw_id}",
                        "title": safe_str(title),
                        "company": safe_str(company),
                        "location": "Remote",
                        "url": url,
                        "description": safe_str(desc),
                        "source": "We Work Remotely",
                        "date": datetime.now().isoformat()
                    })
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
