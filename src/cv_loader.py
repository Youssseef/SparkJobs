import os
from cv_processor import extract_text_from_pdf, extract_text_from_docx
from config_loader import CVS_DIR

def get_cv_text(cv_version: str) -> str:
    """
    Loads text from CV file. Supports .pdf, .docx, and .txt.
    Tries fallback options if the configured version is missing.
    """
    versions_to_try = []
    if cv_version:
        versions_to_try.append(cv_version)
    if "default_cv" not in versions_to_try:
        versions_to_try.append("default_cv")

    for ver in versions_to_try:
        clean_ver = os.path.basename(ver)
        pdf_path = os.path.abspath(os.path.join(CVS_DIR, f"{clean_ver}.pdf"))
        if pdf_path.startswith(os.path.abspath(CVS_DIR) + os.sep) and os.path.exists(pdf_path):
            return extract_text_from_pdf(pdf_path)
            
        docx_path = os.path.abspath(os.path.join(CVS_DIR, f"{clean_ver}.docx"))
        if docx_path.startswith(os.path.abspath(CVS_DIR) + os.sep) and os.path.exists(docx_path):
            return extract_text_from_docx(docx_path)
            
        txt_path = os.path.abspath(os.path.join(CVS_DIR, f"{clean_ver}.txt"))
        if txt_path.startswith(os.path.abspath(CVS_DIR) + os.sep) and os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Error reading txt CV {txt_path}: {e}")
                
    print(f"Warning: CV file not found for versions {versions_to_try} in {CVS_DIR}")
    return ""
