import re

FILLERS = {
    "senior", "junior", "lead", "staff", "principal", "remote", "hybrid", "onsite", 
    "jobs", "job", "intern", "associate", "engineer", "developer", "software", "programmer",
    "middle", "mid", "expert", "specialist", "professional", "director", "vp", "head",
    "designer", "design", "manager", "management", "analyst", "analytics", "consultant",
    "coordinator", "administrator", "admin", "officer", "executive", "representative",
    "technician", "architect", "strategist", "master", "researcher", "specialists"
}

NEGATIVE_ROLE_BLOCKLIST = {
    "writer", "copywriter", "content writer", "sales", "inside sales", "telemarketing",
    "patient care", "nurse", "nursing", "medical", "accountant", "bookkeeper", "payroll",
    "real estate", "realtor", "legal assistant", "paralegal", "recruiter", "hr specialist",
    "customer service representative", "virtual assistant", "data entry clerk", "transcriptionist",
    # Engineering / physical / hardware roles when not targeted
    "mechanical", "solidworks", "catia", "autocad", "hvac", "piping", "civil engineer", 
    "interior designer", "fashion designer", "structural engineer",
    # Non-tech management when not targeted
    "property manager", "restaurant manager", "store manager", "hotel manager", "branch manager",
    "construction manager", "retail manager", "warehouse manager"
}

SHORT_VALID_CORES = {"c++", "c#", "ui", "ux", "ai", "ml", "qa", "go", "c", "net", "bi"}

def get_domain_tokens(title: str, fillers: set = FILLERS) -> list:
    """
    Extracts all domain-defining words from a job title by excluding generic roles and seniority.
    For 'UI/UX Designer', returns ['ui', 'ux'].
    For 'Senior Product Designer', returns ['product'].
    For 'Lead Frontend Engineer', returns ['frontend'].
    For 'Associate Product Manager', returns ['product'].
    """
    raw_words = re.findall(r'[\w+#.]+', title.lower())
    domain_tokens = []
    for word in raw_words:
        clean = word.strip(".-")
        if clean and clean not in fillers:
            if len(clean) >= 3 or clean in SHORT_VALID_CORES:
                domain_tokens.append(clean)
    return domain_tokens

def get_role_core(title: str, fillers: set = FILLERS) -> str:
    """
    Extracts the primary domain core word from a job title.
    Returns the first extracted domain token (or last word as fallback).
    """
    tokens = get_domain_tokens(title, fillers)
    if tokens:
        return tokens[0]
    words = re.findall(r'[\w+#.-]+', title.lower())
    return words[-1] if words else ""

def is_title_relevant(job_title: str, target_titles: list) -> bool:
    """
    Performs case-insensitive semantic relevance checking adhering to the Domain Qualifier Standard.
    Guarantees that a title never matches based solely on generic occupational nouns (designer, manager, analyst).
    Enforces cross-discipline blocklists and domain token overlap.
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
        
        # 1. Direct whole-target match (fast path)
        if target_lower in job_lower:
            return True
            
        # 2. Domain Qualifier Token Match
        target_tokens = get_domain_tokens(target_lower, FILLERS)
        if target_tokens:
            for token in target_tokens:
                kw_escaped = re.escape(token)
                start_b = r'\b' if token[0].isalnum() else ''
                end_b = r'\b' if token[-1].isalnum() else ''
                pattern = rf'{start_b}{kw_escaped}{end_b}'
                if re.search(pattern, job_lower):
                    return True
                    
    return False
