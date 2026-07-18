import os
import json
import re
from google import genai
from google.genai import types
from cv_processor import anonymize_cv_text

# Model cascade — verified working May 2026 (per SPARKGEN_DECISIONS.md Rule 14)
MODEL_CASCADE = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
]

def get_gemini_client(api_key: str):
    """
    Initializes and returns the new google.genai client.
    """
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def clean_json_response(text: str) -> dict:
    """
    Resilient JSON parser that extracts braces if the LLM wraps response
    in markdown or adds extra dialogue.
    """
    try:
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx + 1]
            return json.loads(json_str)
        return json.loads(text)
    except Exception as e:
        print(f"Error parsing Gemini JSON output: {e}. Raw response: {text}")
        return {}

def analyze_job_match(cv_text: str, job_title: str, job_desc: str, api_key: str, min_match_score: int = 65, cover_letter: str = "", years_exp: str = "3-5") -> dict:
    """
    Uses Gemini 2.5 Flash to analyze how well the candidate's CV matches the Job Description.
    Also generates a custom cold outreach message and scores safety/scam risk.
    Uses the new google.genai SDK (google-generativeai is deprecated).
    """
    # 1. Anonymize CV to protect user privacy
    safe_cv = anonymize_cv_text(cv_text)

    # Define fallback response
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

    # Add cover letter context to prompt if provided
    cover_letter_context = ""
    if cover_letter:
        cover_letter_context = f"""
    COVER LETTER TEMPLATE (Use this for tone, style, and highlight references):
    ---
    {cover_letter}
    ---
    """

    # 2. Structure the prompt
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
    6. Outreach Message: A short, professional, and personalized 3-sentence message to send to the recruiter or hiring manager on LinkedIn (mentioning specific alignments from their CV, but keeping contact details blank). If a COVER LETTER TEMPLATE is provided above, adapt its writing style, tone of voice, and highlights when composing this outreach message.
    7. Risk Level: Assess if this job posting is a scam, ghost job, or low-quality listing. Rate it: "Low", "Medium", or "High".
    8. Risk Reason: Explain why you rated the risk level.
    
    You MUST respond with a single, valid JSON object matching this schema. Do not write any preamble, dialogue, or markdown code blocks:
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
    Since the applicant's CV was not provided, you cannot calculate a personal match score (set it to 100).
    
    JOB TITLE: {job_title}
    APPLICANT TARGET YEARS OF EXPERIENCE: {years_exp} years
    JOB DESCRIPTION:
    ---
    {job_desc}
    ---
    
    Evaluate the following:
    1. Match Score: Always return 100.
    2. Estimated Salary: Estimate the average market salary range for this job title in the target location (or remote). Provide a short user-friendly string like "$90,000 - $120,000 / year (Est.)" or "Average: 15,000 - 20,000 AED / month". If the job posting already contains specific salary information, use the salary info from the job posting instead.
    3. Pros: Return ["CV not uploaded - Match analysis skipped"].
    4. Cons: Return ["To activate smart CV compatibility rating, upload your CV in the portal"].
    5. Missing Keywords: Return [].
    6. Outreach Message: A short, professional 3-sentence message to send to the recruiter or hiring manager on LinkedIn asking about the opening for this role (without personalized CV references).
    7. Risk Level: Assess if this job posting is a scam, ghost job, or low-quality listing. Rate it: "Low", "Medium", or "High".
    8. Risk Reason: Explain why you rated the risk level.
    
    You MUST respond with a single, valid JSON object matching this schema. Do not write any preamble, dialogue, or markdown code blocks:
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

    # 3. Try each model in the cascade
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
    # Test execution if API key is in env
    api_key = os.environ.get("GEMINI_API_KEY", "")
    test_cv = "Experienced frontend developer with 3 years of React, JavaScript, and HTML/CSS. Built multiple design systems."
    test_title = "Senior React Developer"
    test_desc = "Looking for a React Engineer with experience in TypeScript, TailwindCSS, and testing frameworks like Jest. Must build responsive interfaces."

    if api_key:
        print("Running test match with Gemini (new google.genai SDK):")
        print(analyze_job_match(test_cv, test_title, test_desc, api_key))
    else:
        print("No GEMINI_API_KEY env found. Returning mock response.")
        print(analyze_job_match(test_cv, test_title, test_desc, ""))
