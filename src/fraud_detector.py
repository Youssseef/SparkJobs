import re
from datetime import datetime

FRAUD_RULES = {
    "max_age_days": 14,
    "spam_keywords": [
        r"whatsapp", r"telegram", r"urgent hiring", r"no experience needed",
        r"work from home \$?\d+,?\d*", r"deposit", r"pay fee", r"training fee",
        r"package envelope", r"secret shopper", r"mystery shopper",
        r"immediate start", r"no cv required", r"contact on whatsapp",
        # M-04 Fix: Arabic spam keywords for Gulf / MENA job board scams
        r"واتساب", r"تيليجرام", r"مطلوب فوراً", r"بدون خبرة",
        r"رسوم تدريب", r"عمولة فقط", r"ارسل cv على واتس",
        r"تواصل واتساب", r"لا يشترط خبرة", r"من المنزل"
    ],
    "suspicious_email_domains": [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "mail.ru", "yandex.ru"
    ],
    "min_description_words": 30
}

def analyze_job_for_fraud(job: dict) -> dict:
    """
    Checks job title, description, company, and email contact info against
    common fraud, scam, and ghost job indicators.
    Returns:
        dict: {
            "is_suspicious": bool,
            "risk_level": "Low" | "Medium" | "High",
            "reasons": list of strings
        }
    """
    reasons = []
    
    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()
    company = (job.get("company") or "").lower()
    url = (job.get("url") or "").lower()
    
    # 1. Check age of posting (handled in main scraper but reinforced here if date is present)
    # If the date is passed as a string and we can parse it, check it.
    
    # 2. Check Description Word Count (M-05 Fix: Language-aware threshold for concise Arabic text)
    words = description.split()
    is_arabic = bool(re.search(r'[\u0600-\u06FF]', description + " " + title))
    min_words = FRAUD_RULES["min_description_words"] // 2 if is_arabic else FRAUD_RULES["min_description_words"]
    if len(words) < min_words:
        reasons.append(f"Description is extremely short ({len(words)} words), which is typical of low-quality ghost jobs.")

    # 3. Check for Spam/Scam Keywords
    for pattern in FRAUD_RULES["spam_keywords"]:
        if re.search(pattern, description) or re.search(pattern, title):
            # Clean up print label
            clean_pattern = pattern.replace(r"\?", "").replace(r"\d+,?\d*", "").replace(r"\$", "$")
            reasons.append(f"Contains suspicious/scam phrase: '{clean_pattern}'")

    # 4. Check for Free Email Domains in description (e.g. 'apply at company@gmail.com')
    # Extracts emails from description
    email_regex = r'[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    found_emails = re.findall(email_regex, description)
    for domain in found_emails:
        if domain.lower() in FRAUD_RULES["suspicious_email_domains"]:
            reasons.append(f"Asks to apply or contact via a free email address (@{domain}) instead of a corporate domain.")

    # 5. Check for suspicious company names (English & Arabic placeholders)
    suspicious_companies = ["", "na", "n/a", "unknown", "confidential", "غير محدد", "سرية", "غير متاح", "بدون اسم"]
    if not company or company.strip() in suspicious_companies:
        reasons.append("Company name is confidential or not provided, commonly used for ghost jobs or data harvesting.")

    # 6. Check for WhatsApp/Telegram link patterns
    if "t.me/" in url or "wa.me/" in url or "api.whatsapp.com" in url or "t.me/" in description or "wa.me/" in description:
        reasons.append("Directs applicant to chat on Telegram or WhatsApp instead of using a standard ATS or company portal.")

    # Determine overall risk level
    high_risk_signals = [
        "free email address",
        "chat on Telegram or WhatsApp",
        "deposit", "pay fee", "training fee", "whatsapp", "telegram", "contact on whatsapp",
        "واتساب", "تيليجرام", "رسوم تدريب", "عمولة فقط"
    ]
    
    risk_level = "Low"
    is_suspicious = False
    
    if len(reasons) > 0:
        is_suspicious = True
        risk_level = "Medium"
        
        # Upgrade to High Risk if any high risk signals are found
        for reason in reasons:
            if any(signal in reason.lower() for signal in high_risk_signals):
                risk_level = "High"
                break
                
    return {
        "is_suspicious": is_suspicious,
        "risk_level": risk_level,
        "reasons": reasons
    }

if __name__ == "__main__":
    # Test cases
    test_job_1 = {
        "title": "React Developer needed immediately!",
        "description": "We are looking for a React developer. Urgent hiring! No experience needed. Work from home $5000 per week. Contact us on WhatsApp +123456789 or apply at techjobs@gmail.com.",
        "company": "SuperTech",
        "url": "https://indeed.com/job/123"
    }
    
    test_job_2 = {
        "title": "Senior Frontend Engineer",
        "description": "Requirements: 5+ years of experience in React, TypeScript, and state management. You will build highly scalable web interfaces and work in an agile team.",
        "company": "Acme Corp",
        "url": "https://indeed.com/job/456"
    }
    
    print("Job 1 Analysis:")
    print(analyze_job_for_fraud(test_job_1))
    print("\nJob 2 Analysis:")
    print(analyze_job_for_fraud(test_job_2))
