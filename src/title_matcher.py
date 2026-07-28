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
    Supports technical symbols like 'c++', 'c#', '.net'.
    """
    short_valid_cores = {"c++", "c#", "ui", "ux", "ai", "ml", "qa", "go", "c", "net"}
    words = re.findall(r'[\w+#.-]+', title.lower())
    for word in reversed(words):
        clean_word = word.strip(".-")
        if clean_word not in fillers and (len(clean_word) > 2 or clean_word in short_valid_cores):
            return clean_word
    return words[-1] if words else ""

def is_title_relevant(job_title: str, target_titles: list) -> bool:
    """
    Performs case-insensitive semantic relevance checking.
    Ensures that the job title is relevant to at least one target title by verifying
    direct substring match or overlap of the target's core domain word, and checks
    against negative off-field role blocklists.
    """
    if not target_titles or not job_title:
        return True
    
    job_lower = job_title.lower()
    combined_targets = " ".join(target_titles).lower()

    # 0. Negative role blocklist check: discard off-field jobs unless explicitly targeted
    for neg_word in NEGATIVE_ROLE_BLOCKLIST:
        kw_escaped = re.escape(neg_word)
        start_b = r'\b' if neg_word[0].isalnum() else ''
        end_b = r'\b' if neg_word[-1].isalnum() else ''
        pattern = rf'{start_b}{kw_escaped}{end_b}'
        if re.search(pattern, job_lower) and not re.search(pattern, combined_targets):
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
