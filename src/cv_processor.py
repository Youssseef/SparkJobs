import re
import zipfile
import defusedxml.ElementTree as ET
from pypdf import PdfReader

# M-02 Fix: Pre-compile regex at module level to prevent ReDoS on hot path
_EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_PHONE_REGEX = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}')
_URL_REGEX = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')

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

def extract_text_from_docx(docx_path: str) -> str:
    """
    C-02 Fix: Extracts raw text from DOCX using safe defusedxml parser
    protecting against XXE and entity expansion attacks.
    """
    try:
        texts = []
        with zipfile.ZipFile(docx_path) as docx:
            for file_name in docx.namelist():
                if file_name.startswith('word/') and file_name.endswith('.xml'):
                    try:
                        xml_content = docx.read(file_name)
                        root = ET.fromstring(xml_content)
                        for el in root.iter():
                            if el.tag.endswith('}t') or el.tag == 't':
                                if el.text:
                                    texts.append(el.text)
                    except Exception:
                        pass
        return " ".join(texts).strip()
    except Exception as e:
        print(f"Error reading DOCX {docx_path}: {e}")
        return ""

def anonymize_cv_text(text: str) -> str:
    """
    Strips personally identifiable information (PII) such as emails, phone numbers,
    links, and top header lines.
    """
    if not text:
        return ""

    # 1. Strip Emails
    text = _EMAIL_REGEX.sub('[ANONYMIZED_EMAIL]', text)

    # 2. Strip Phone Numbers
    def phone_replacer(match):
        val = match.group(0)
        digits = re.sub(r'\D', '', val)
        if 7 <= len(digits) <= 15:
            return '[ANONYMIZED_PHONE]'
        return val
    
    text = _PHONE_REGEX.sub(phone_replacer, text)

    # 3. Strip URLs / Links
    text = _URL_REGEX.sub('[ANONYMIZED_LINK]', text)

    # 4. Strip top headers
    lines = text.split('\n')
    anonymized_lines = []
    location_keywords = ['location', 'address', 'street', 'city', 'country', 'zip', 'road', 'state']
    
    non_empty_count = 0
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            anonymized_lines.append(line)
            continue
        
        non_empty_count += 1
        contains_location = any(kw in cleaned_line.lower() for kw in location_keywords)
        
        if non_empty_count <= 3 and len(cleaned_line) < 50:
            anonymized_lines.append('[ANONYMIZED_HEADER_LINE]')
        elif contains_location:
            anonymized_lines.append('[ANONYMIZED_LOCATION_LINE]')
        else:
            anonymized_lines.append(line)

    return '\n'.join(anonymized_lines)

if __name__ == "__main__":
    dummy_cv = """
    Youssef Wael
    Senior Software Engineer | Cairo, Egypt
    Phone: +20 123 456 7890 | Email: youssef@sparkgen.net | LinkedIn: https://linkedin.com/in/youssef
    """
    print("Anonymized CV check:")
    print(anonymize_cv_text(dummy_cv))
