import os
import json
import re
from google import generativeai as genai
from cv_processor import anonymize_cv_text

def get_gemini_client(api_key: str):
    """
    Initializes and configures the Gemini API client.
    """
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai

def clean_json_response(text: str) -> dict:
    """
    Resilient JSON parser that extracts braces if the LLM wraps response
    in markdown or adds extra dialogue.
    """
    try:
        # Search for first { and last }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx:end_idx + 1]
            return json.loads(json_str)
        return json.loads(text)
    except Exception as e:
        print(f"Error parsing Gemini JSON output: {e}. Raw response: {text}")
        return {}

def analyze_job_match(cv_text: str, job_title: str, job_desc: str, api_key: str, min_match_score: int = 65) -> dict:
    """
    Uses Gemini 2.5 Flash to analyze how well the candidate's CV matches the Job Description.
    Also generates a custom cold outreach message and scores safety/scam risk.
    """
    # 1. Anonymize CV to protect user privacy
    safe_cv = anonymize_cv_text(cv_text)
    
    # Define fallback response
    fallback = {
        "match_score": 0,
        "risk_level": "Low",
        "risk_reason": "No AI analysis performed (Fallback)",
        "pros": ["No automated assessment available"],
        "cons": ["Review manually"],
        "missing_keywords": [],
        "outreach_message": f"Hi, I noticed your opening for the {job_title} role..."
    }

    # If no API key is provided, return fallback
    if not api_key:
        print("No Gemini API key provided. Skipping AI analysis.")
        return fallback

    client = get_gemini_client(api_key)
    if not client:
        return fallback

    # 2. Structure the prompt
    prompt = f"""
    You are an expert technical recruiter. Analyze the applicant's CV against the Job Description.
    
    APPLICANT CV (Anonymized):
    ---
    {safe_cv}
    ---
    
    JOB TITLE: {job_title}
    JOB DESCRIPTION:
    ---
    {job_desc}
    ---
    
    Evaluate the following:
    1. Match Score: An integer from 0 to 100 representing how well the CV fits the Job Description.
    2. Pros: 2-3 specific reasons why the CV matches this job.
    3. Cons: 1-2 weaknesses or areas of misalignment.
    4. Missing Keywords: Crucial technical keywords or skills mentioned in the job post but missing from the CV.
    5. Outreach Message: A short, professional, and personalized 3-sentence message to send to the recruiter or hiring manager on LinkedIn (mentioning specific alignments from their CV, but keeping contact details blank).
    6. Risk Level: Assess if this job posting is a scam, ghost job, or low-quality listing. Rate it: "Low", "Medium", or "High".
    7. Risk Reason: Explain why you rated the risk level (e.g., generic description, unrealistically high salary, standard corporate profile).
    
    You MUST respond with a single, valid JSON object matching this schema. Do not write any preamble, dialogue, or markdown code blocks:
    {{
      "match_score": int,
      "risk_level": "Low" | "Medium" | "High",
      "risk_reason": "reason why",
      "pros": ["pro1", "pro2"],
      "cons": ["con1"],
      "missing_keywords": ["keyword1", "keyword2"],
      "outreach_message": "string"
    }}
    """

    try:
        # Use gemini-2.5-flash as it is the standard, fast, and free tier model in 2026
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        if response and response.text:
            result = clean_json_response(response.text)
            if result:
                return result
    except Exception as e:
        print(f"Gemini API invocation error: {e}")
        
    return fallback

if __name__ == "__main__":
    # Test execution if API key is in env
    api_key = os.environ.get("GEMINI_API_KEY", "")
    test_cv = "Experienced frontend developer with 3 years of React, JavaScript, and HTML/CSS. Built multiple design systems."
    test_title = "Senior React Developer"
    test_desc = "Looking for a React Engineer with experience in TypeScript, TailwindCSS, and testing frameworks like Jest. Must build responsive interfaces."
    
    if api_key:
        print("Running test match with Gemini:")
        print(analyze_job_match(test_cv, test_title, test_desc, api_key))
    else:
        print("No GEMINI_API_KEY env found. Returning mock response.")
        print(analyze_job_match(test_cv, test_title, test_desc, ""))
