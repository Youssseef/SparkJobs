import os
import time
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from jobspy import scrape_jobs
import pandas as pd

def get_scraperapi_proxy(api_key: str) -> str:
    """
    Returns the ScraperAPI proxy URL string.
    """
    if not api_key:
        return ""
    # ScraperAPI standard proxy endpoint
    return f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001"

def scrape_jobspy(site_name: list, search_term: str, location: str, proxy_url: str = "", results_wanted: int = 15) -> list:
    """
    Scrapes jobs using the python-jobspy library.
    Handles Indeed, Glassdoor, ZipRecruiter, and Google Jobs.
    """
    jobs_list = []
    try:
        # Determine country parameter for Indeed based on location
        # Covers all 18 countries available in the setup wizard
        country_map = {
            "germany": "germany",
            "united kingdom": "uk",
            "uk": "uk",
            "united states": "usa",
            "us": "usa",
            "usa": "usa",
            "canada": "canada",
            "france": "france",
            "saudi arabia": "saudiarabia",
            "ksa": "saudiarabia",
            "united arab emirates": "uae",
            "uae": "uae",
            "egypt": "egypt",
            "qatar": "qatar",
            "kuwait": "kuwait",
            "oman": "oman",
            "bahrain": "bahrain",
            "jordan": "jordan",
            "netherlands": "netherlands",
            "sweden": "sweden",
            "switzerland": "switzerland",
            "australia": "australia",
            "worldwide": "worldwide",
            "remote": "worldwide",
        }

        country_indeed = "worldwide"  # default — safer than "usa" for unknown entries
        loc_lower = location.lower()
        for k, v in country_map.items():
            if k in loc_lower:
                country_indeed = v
                break

        print(f"Scraping JobSpy sites {site_name} for '{search_term}' in '{location}'...")
        
        # Configure proxies if provided
        proxies = {}
        if proxy_url:
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

        # Run JobSpy scraper
        # JobSpy returns a pandas DataFrame
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
                # Extract description securely
                desc = row.get("description", "")
                if pd.isna(desc):
                    desc = ""

                jobs_list.append({
                    "id": str(row.get("id", "")),
                    "title": str(row.get("title", "")),
                    "company": str(row.get("company", "")),
                    "location": str(row.get("location", "")),
                    "url": str(row.get("job_url", "")),
                    "description": str(desc),
                    "source": str(row.get("site", "JobSpy")),
                    "date": datetime.now().isoformat()
                })
        
        print(f"JobSpy found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping JobSpy: {e}")
        
    return jobs_list

def scrape_remoteok(search_term: str) -> list:
    """
    Scrapes jobs from Remote OK API (Free JSON).
    """
    jobs_list = []
    try:
        print(f"Scraping Remote OK for '{search_term}'...")
        # Remote OK requires a proper User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://remoteok.com/api?tag={search_term.replace(' ', '-')}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Remote OK API returns a list where the first element is legal info/stats
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

def scrape_remotive(search_term: str) -> list:
    """
    Scrapes jobs from Remotive API (Free JSON).
    """
    jobs_list = []
    try:
        print(f"Scraping Remotive for '{search_term}'...")
        url = f"https://remotive.com/api/remote-jobs?search={search_term}"
        response = requests.get(url, timeout=10)
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

def scrape_weworkremotely(search_term: str) -> list:
    """
    Scrapes jobs from We Work Remotely RSS Feed (Free XML).
    """
    jobs_list = []
    try:
        print(f"Scraping We Work Remotely for '{search_term}'...")
        # WWR feeds are grouped by category, but we can search using their public search feed
        url = f"https://weworkremotely.com/categories/remote-programming-jobs.rss"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    guid = item.find("guid").text if item.find("guid") is not None else link
                    
                    # Manual keyword filter for search term
                    if search_term.lower() in title.lower() or search_term.lower() in desc.lower():
                        # Parse company name from title "Company: Position"
                        company = "WeWorkRemotely"
                        if ":" in title:
                            parts = title.split(":", 1)
                            company = parts[0].strip()
                            title = parts[1].strip()

                        jobs_list.append({
                            "id": f"wwr-{guid.split('/')[-1] if '/' in guid else guid}",
                            "title": title,
                            "company": company,
                            "location": "Remote",
                            "url": link,
                            "description": desc,
                            "source": "We Work Remotely",
                            "date": datetime.now().isoformat()
                        })
        print(f"We Work Remotely found {len(jobs_list)} jobs.")
    except Exception as e:
        print(f"Error scraping We Work Remotely: {e}")
    return jobs_list

def run_all_scrapes(search_term: str, location: str, scraperapi_key: str = "") -> list:
    """
    Runs scraping across all available free APIs and JobSpy sources sequentially.
    """
    all_jobs = []
    
    # 1. Scrape free remote APIs
    all_jobs.extend(scrape_remoteok(search_term))
    time.sleep(random.uniform(1.5, 3.0)) # Politeness delay
    
    all_jobs.extend(scrape_remotive(search_term))
    time.sleep(random.uniform(1.5, 3.0))
    
    all_jobs.extend(scrape_weworkremotely(search_term))
    time.sleep(random.uniform(1.5, 3.0))
    
    # 2. Scrape JobSpy (Indeed, Google Jobs, ZipRecruiter)
    # We use ScraperAPI proxy if provided to prevent blocking
    proxy_url = get_scraperapi_proxy(scraperapi_key)
    
    # Google Jobs / Indeed / ZipRecruiter
    jobspy_sites = ["google"]
    if scraperapi_key: # Only scrape Indeed/ZipRecruiter if proxy is available to prevent immediate Action bans
        jobspy_sites.extend(["indeed", "zip_recruiter"])
    else:
        print("Warning: No ScraperAPI key provided. Skipping Indeed and ZipRecruiter scrapes to prevent IP blocking, and running Google Jobs without a proxy.")
        
    jobspy_jobs = scrape_jobspy(
        site_name=jobspy_sites,
        search_term=search_term,
        location=location,
        proxy_url=proxy_url
    )
    all_jobs.extend(jobspy_jobs)
    
    return all_jobs

if __name__ == "__main__":
    # Test execution
    jobs = run_all_scrapes("React", "Remote")
    print(f"Total jobs scraped: {len(jobs)}")
