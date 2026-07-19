import os
import json
import re
from google import genai
from google.genai import types
from cv_processor import anonymize_cv_text

MODEL_CASCADE = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
]

def get_gemini_client(api_key: str):
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def clean_json_response(text: str) -> dict:
    """
    M-01 Fix: Strips markdown code blocks and extracts JSON object resiliently.
    """
    if not text:
        return {}
    try:
        # Strip markdown fences first
        cleaned = re.sub(r'```(?:json)?\s*', '', text).strip()
        cleaned = cleaned.rstrip('`').strip()
        
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = cleaned[start_idx:end_idx + 1]
            return json.loads(json_str)
        return json.loads(cleaned)
    except Exception as e:
        print(f"Error parsing Gemini JSON output: {e}. Raw response: {text}")
        return {}

def analyze_job_match(cv_text: str, job_title: str, job_desc: str, api_key: str, min_match_score: int = 65, cover_letter: str = "", years_exp: str = "3-5") -> dict:
    safe_cv = anonymize_cv_text(cv_text)

    fallback = {
        "match_score": 100,
        "estimated_salary": "Not specified (Market average: Unknown)",
        "risk_level": "Low",
        "risk_reason": "Skipped (No Gemini API Key provided)",
        "pros": ["Unfiltered job alert (AI Matcher disabled)"],
        "cons": ["To unlock smart compatibility scores, pros/cons, and personalized outreach drafts, please add a Gemini API Key in your setup dashboard."],
        "missing_keywords": [],
        "outreach_message": "(Recruiter outreach templates require adding a Gemini API Key in your setup)"
    }

    if not api_key:
        print("No Gemini API key provided. Bypassing AI match filters to deliver all parsed jobs.")
        return fallback

    client = get_gemini_client(api_key)
    if not client:
        return fallback

    cover_letter_context = ""
    if cover_letter:
        cover_letter_context = f"""
    COVER LETTER TEMPLATE (Use this for tone, style, and highlight references):
    ---
    {cover_letter}
    ---
    """

    if cv_text:
        prompt = f"""
    You are an expert technical recruiter. Analyze the applicant's CV against the Job Description.
    
    APPLICANT CV (Anonymized):
    ---
    {safe_cv}
    ---
    {cover_letter_context}
    
    JOB TITLE: {job_title}
    APPLICANT TARGET YEARS OF EXPERIENCE: {years_exp} years
    JOB DESCRIPTION:
    ---
    {job_desc}
    ---
    
    Evaluate the following:
    1. Match Score: An integer from 0 to 100 representing how well the CV fits the Job Description.
    2. Estimated Salary: Estimate the average market salary range for this job title in the target location (or remote). Provide a short user-friendly string like "$90,000 - $120,000 / year (Est.)" or "Average: 15,000 - 20,000 AED / month". If the job posting already contains specific salary information, use the salary info from the job posting instead.
    3. Pros: 2-3 specific reasons why the CV matches this job.
    4. Cons: 1-2 weaknesses or areas of misalignment.
    5. Missing Keywords: Crucial technical keywords or skills mentioned in the job post but missing from the CV.
    6. Outreach Message: A short, professional, and personalized 3-sentence message to send to the recruiter or hiring manager on LinkedIn.
    7. Risk Level: Assess if this job posting is a scam, ghost job, or low-quality listing. Rate it: "Low", "Medium", or "High".
    8. Risk Reason: Explain why you rated the risk level.
    
    You MUST respond with a single, valid JSON object matching this schema:
    {{
      "match_score": int,
      "estimated_salary": "string",
      "risk_level": "Low" | "Medium" | "High",
      "risk_reason": "reason why",
      "pros": ["pro1", "pro2"],
      "cons": ["con1"],
      "missing_keywords": ["keyword1", "keyword2"],
      "outreach_message": "string"
    }}
    """
    else:
        prompt = f"""
    You are an expert recruiter. Analyze this job description.
    Since the applicant's CV was not provided, set match score to 100.
    
    JOB TITLE: {job_title}
    APPLICANT TARGET YEARS OF EXPERIENCE: {years_exp} years
    JOB DESCRIPTION:
    ---
    {job_desc}
    ---
    
    Evaluate the following:
    1. Match Score: Always return 100.
    2. Estimated Salary: Estimate the average market salary range for this job title in the target location (or remote).
    3. Pros: Return ["CV not uploaded - Match analysis skipped"].
    4. Cons: Return ["To activate smart CV compatibility rating, upload your CV in the portal"].
    5. Missing Keywords: Return [].
    6. Outreach Message: A short, professional 3-sentence message to send to recruiter.
    7. Risk Level: Rate "Low", "Medium", or "High".
    8. Risk Reason: Explain why you rated the risk level.
    
    You MUST respond with a single, valid JSON object matching this schema:
    {{
      "match_score": 100,
      "estimated_salary": "string",
      "risk_level": "Low" | "Medium" | "High",
      "risk_reason": "reason why",
      "pros": ["CV not uploaded - Match analysis skipped"],
      "cons": ["To activate smart CV compatibility rating, upload your CV in the portal"],
      "missing_keywords": [],
      "outreach_message": "string"
    }}
    """

    for model_name in MODEL_CASCADE:
        try:
            print(f"Trying model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            if response and response.text:
                result = clean_json_response(response.text)
                if result:
                    print(f"Success with model: {model_name}")
                    return result
        except Exception as e:
            print(f"Model {model_name} failed: {e}. Trying next...")
            continue

    print("All models in cascade failed. Returning fallback.")
    return fallback

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY", "")
    test_cv = "Experienced frontend developer with 3 years of React."
    test_title = "Senior React Developer"
    test_desc = "Looking for a React Engineer with experience in TypeScript."

    if api_key:
        print(analyze_job_match(test_cv, test_title, test_desc, api_key))
    else:
        print(analyze_job_match(test_cv, test_title, test_desc, ""))
