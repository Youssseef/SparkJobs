import re

FILLERS = {
    "senior", "junior", "lead", "staff", "principal", "remote", "hybrid", "onsite", 
    "jobs", "job", "intern", "associate", "engineer", "developer", "software", "programmer",
    "middle", "mid", "expert", "specialist", "professional", "director", "vp", "head"
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
    direct substring match or overlap of the target's core domain word.
    """
    if not target_titles:
        return True
    
    for target in target_titles:
        target_lower = target.lower()
        job_lower = job_title.lower()
        
        # 1. Direct substring match (fast path)
        if target_lower in job_lower:
            return True
            
        # 2. Domain core word matching (stops cross-field contamination, e.g. Frontend vs DevOps)
        core = get_role_core(target_lower, FILLERS)
        if core and core in job_lower:
            return True
            
    return False
