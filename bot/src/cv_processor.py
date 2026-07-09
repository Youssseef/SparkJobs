import re
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all raw text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def anonymize_cv_text(text: str) -> str:
    """
    Strips personally identifiable information (PII) such as emails, phone numbers,
    links, and top header lines (which usually contain names and addresses).
    """
    if not text:
        return ""

    # 1. Strip Emails
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_regex, '[ANONYMIZED_EMAIL]', text)

    # 2. Strip Phone Numbers (captures international and local formats)
    phone_regex = r'(?:\+?\d{1,3}[-.\s\?]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    # Clean up phone number matching to avoid matching random years/dates
    # We look for standard phone lengths: at least 7 digits after cleaning
    def phone_replacer(match):
        val = match.group(0)
        digits = re.sub(r'\D', '', val)
        if len(digits) >= 7 and len(digits) <= 15:
            return '[ANONYMIZED_PHONE]'
        return val
    
    text = re.sub(phone_regex, phone_replacer, text)

    # 3. Strip URLs / Links (LinkedIn, GitHub, Portfolio)
    url_regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    text = re.sub(url_regex, '[ANONYMIZED_LINK]', text)

    # 4. Strip top headers (often contains Name, Location, Title)
    # Typically PII is in the first 5 lines of the resume. We will scan the first few lines
    # and replace any highly specific contact info patterns.
    lines = text.split('\n')
    anonymized_lines = []
    
    # We assume the first 5 non-empty lines might contain Name and Location.
    # We will search for keywords like "address", "street", "city", "zip", "location" and strip those lines.
    location_keywords = ['location', 'address', 'street', 'city', 'country', 'zip', 'road', 'state']
    
    non_empty_count = 0
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            anonymized_lines.append(line)
            continue
        
        non_empty_count += 1
        
        # Check if line contains location keywords
        contains_location = any(kw in cleaned_line.lower() for kw in location_keywords)
        
        # If it's in the very first 3 non-empty lines, it's highly likely to be the Name/Title/Header.
        # We replace them with placeholder if they don't look like standard sentences (e.g. short lines).
        if non_empty_count <= 3 and len(cleaned_line) < 50:
            anonymized_lines.append('[ANONYMIZED_HEADER_LINE]')
        elif contains_location:
            anonymized_lines.append('[ANONYMIZED_LOCATION_LINE]')
        else:
            anonymized_lines.append(line)

    return '\n'.join(anonymized_lines)

if __name__ == "__main__":
    # Quick local test
    dummy_cv = """
    Youssef Wael
    Senior Software Engineer | Cairo, Egypt
    Phone: +20 123 456 7890 | Email: youssef@sparkgen.net | LinkedIn: https://linkedin.com/in/youssef
    
    Professional Summary:
    Experienced developer specialized in React and Node.js.
    """
    print("Original CV:")
    print(dummy_cv)
    print("\nAnonymized CV:")
    print(anonymize_cv_text(dummy_cv))
