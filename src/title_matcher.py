import re

FILLERS = {
    "senior", "junior", "lead", "staff", "principal", "remote", "hybrid", "onsite", 
    "jobs", "job", "intern", "associate", "engineer", "developer", "software", "programmer",
    "middle", "mid", "expert", "specialist", "professional", "director", "vp", "head"
}

NEGATIVE_ROLE_BLOCKLIST = {
    "writer", "copywriter", "content writer", "sales", "inside sales", "telemarketing",
    "patient care", "nurse", "nursing", "medical", "accountant", "bookkeeper", "payroll",
    "real estate", "realtor", "legal assistant", "paralegal", "recruiter", "hr specialist",
    "customer service representative", "virtual assistant", "data entry clerk", "transcriptionist"
}

def get_role_core(title: str, fillers: set = FILLERS) -> str:
    """
    Extracts the defining domain core word from a job title by checking from the end.
    e.g., "Product Designer" -> "designer"
          "Frontend Engineer" -> "frontend"
          "Senior React Developer" -> "react"
    """
    words = re.findall(r'\b\w+\b', title.lower())
    for word in reversed(words):
        if word not in fillers and len(word) > 2:
            return word
    return words[-1] if words else ""

def is_title_relevant(job_title: str, target_titles: list) -> bool:
    """
    Performs case-insensitive semantic relevance checking.
    Ensures that the job title is relevant to at least one target title by verifying
    direct substring match or overlap of the target's core domain word, and checks
    against negative off-field role blocklists.
    M-03 Fix: Uses regex word boundaries for negative role blocklist checks.
    M-04 Fix: Skips generic filler words during domain core matching.
    """
    if not target_titles or not job_title:
        return True
    
    job_lower = job_title.lower()
    combined_targets = " ".join(target_titles).lower()

    # 0. Negative role blocklist check: discard off-field jobs unless explicitly targeted
    for neg_word in NEGATIVE_ROLE_BLOCKLIST:
        if re.search(rf'\b{re.escape(neg_word)}\b', job_lower) and neg_word not in combined_targets:
            return False
    
    for target in target_titles:
        target_lower = target.lower()
        
        # 1. Direct substring match (fast path)
        if target_lower in job_lower:
            return True
            
        # 2. Domain core word matching (stops cross-field contamination, e.g. Frontend vs DevOps)
        core = get_role_core(target_lower, FILLERS)
        if core and core not in FILLERS and core in job_lower:
            return True
            
    return False
