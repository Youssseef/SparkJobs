import re
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import requests

PREFERRED_ATS_DOMAINS = [
    "greenhouse.io", "lever.co", "smartrecruiters.com", "ashbyhq.com",
    "dover.io", "workday.com", "myworkdayjobs.com", "workable.com",
    "bamboohr.com", "breezy.hr", "recruitee.com", "jobvite.com",
    "applytojob.com", "taleo.net", "icims.com"
]

CLOSED_JOB_SIGNALS = [
    "this position has been filled",
    "this position is no longer available",
    "job not found",
    "position closed",
    "no longer accepting applications",
    "job posting has expired",
    "job is no longer available",
    "this job has been closed"
]

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def is_ats_url(url: str) -> bool:
    """Checks if a URL already points directly to a known Applicant Tracking System (ATS)."""
    if not url or not isinstance(url, str):
        return False
    u = url.lower()
    return any(domain in u for domain in PREFERRED_ATS_DOMAINS)

def normalize_linkedin_url(url: str) -> str:
    """
    Normalizes country-specific subdomains (ca., uk., eg., sa.) and tracking tokens
    to the universal canonical LinkedIn job URL: https://www.linkedin.com/jobs/view/{job_id}
    Eliminates cross-region 404s and expired guest token errors.
    """
    if not url or not isinstance(url, str) or 'linkedin.com' not in url.lower():
        return url
    match = re.search(r'/jobs/view/(?:[^\s/?#]*-)?([0-9]{8,})', url)
    if match:
        job_id = match.group(1)
        return f"https://www.linkedin.com/jobs/view/{job_id}"
    return url

def build_search_fallback_url(company: str, title: str) -> str:
    """Constructs a 1-tap browser search fallback query to open in mobile Safari/Chrome."""
    clean_comp = re.sub(r'[\"\']', '', str(company or '').strip())
    clean_title = re.sub(r'[\"\']', '', str(title or '').strip())
    if clean_comp and clean_title:
        query = f'"{clean_comp}" "{clean_title}" careers apply'
    elif clean_title:
        query = f'"{clean_title}" careers apply'
    else:
        query = 'careers job application'
    return f"https://www.google.com/search?q={quote_plus(query)}"

def extract_embedded_url(raw_url: str) -> str | None:
    """Extracts target URLs embedded inside aggregator query parameters (e.g. ?url=... or ?redirect=...)."""
    try:
        parsed = urlparse(raw_url)
        params = parse_qs(parsed.query)
        for key in ["url", "redirect", "dest", "target", "link", "job_url"]:
            if key in params and params[key]:
                candidate = unquote(params[key][0]).strip()
                if candidate.startswith("http://") or candidate.startswith("https://"):
                    return candidate
    except Exception:
        pass
    return None

def resolve_canonical_url(raw_url: str, timeout: int = 4) -> tuple[str, bool, str]:
    """
    Unmasks tracking and aggregator links into direct canonical ATS URLs.
    Returns: (canonical_url, is_live, reason)
    """
    if not raw_url or not isinstance(raw_url, str):
        return "", False, "empty_url"
    
    clean_url = raw_url.strip()
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        return clean_url, False, "invalid_protocol"

    # Fast path: LinkedIn URLs normalize to universal global job view
    if "linkedin.com" in clean_url.lower():
        return normalize_linkedin_url(clean_url), True, "canonical_linkedin"

    # Fast path: URL is already a verified ATS domain
    if is_ats_url(clean_url):
        return clean_url, True, "direct_ats"

    # Fast path: Embedded redirect query param is ATS
    embedded = extract_embedded_url(clean_url)
    if embedded and is_ats_url(embedded):
        return embedded, True, "embedded_ats"

    # Fast network unmasking via HEAD
    try:
        resp = requests.head(clean_url, headers=REQUEST_HEADERS, allow_redirects=True, timeout=timeout)
        final_url = resp.url if resp and resp.url else clean_url

        if resp.status_code in [404, 410]:
            return final_url, False, f"http_{resp.status_code}"

        if resp.status_code in [200, 201, 202, 203, 301, 302, 307, 308]:
            return final_url, True, "resolved"
    except requests.RequestException:
        pass

    # Fallback streamed GET to verify status code and closed job signals
    try:
        with requests.get(clean_url, headers=REQUEST_HEADERS, stream=True, allow_redirects=True, timeout=timeout) as resp:
            final_url = resp.url if resp and resp.url else clean_url
            if resp.status_code in [404, 410]:
                return final_url, False, f"http_{resp.status_code}"
            
            # Read first 8KB of content to check for closed-job signals
            first_chunk = resp.raw.read(8192).decode("utf-8", errors="ignore").lower()
            if any(sig in first_chunk for sig in CLOSED_JOB_SIGNALS):
                return final_url, False, "position_closed"

            return final_url, True, "resolved_get"
    except Exception:
        # On connection failure / timeout, return original URL as live fallback
        return clean_url, True, "unmasked_fallback"
