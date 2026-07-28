import os
from cv_processor import extract_text_from_pdf, extract_text_from_docx
from config_loader import CVS_DIR

def get_cv_text(cv_version: str) -> str | None:
    """
    Loads text from CV file. Supports .pdf, .docx, and .txt.
    Tries fallback options if the configured version is missing.
    Returns None if no file exists, or string (can be empty for scanned images).
    """
    versions_to_try = []
    if cv_version:
        versions_to_try.append(cv_version)
    if "default_cv" not in versions_to_try and "default_cv.txt" not in versions_to_try:
        versions_to_try.append("default_cv")

    for ver in versions_to_try:
        clean_ver = os.path.basename(ver)
        base_name = os.path.splitext(clean_ver)[0]
        
        # Check direct full path if ver already includes an extension
        direct_path = os.path.abspath(os.path.join(CVS_DIR, clean_ver))
        if direct_path.startswith(os.path.abspath(CVS_DIR) + os.sep) and os.path.exists(direct_path):
            ext = os.path.splitext(clean_ver)[1].lower()
            if ext == ".pdf":
                return extract_text_from_pdf(direct_path)
            elif ext == ".docx":
                return extract_text_from_docx(direct_path)
            elif ext == ".txt":
                try:
                    with open(direct_path, "r", encoding="utf-8") as f:
                        return f.read().strip()
                except Exception as e:
                    print(f"Error reading txt CV {direct_path}: {e}")

        # Check by base_name + extension
        pdf_path = os.path.abspath(os.path.join(CVS_DIR, f"{base_name}.pdf"))
        if pdf_path.startswith(os.path.abspath(CVS_DIR) + os.sep) and os.path.exists(pdf_path):
            return extract_text_from_pdf(pdf_path)
            
        docx_path = os.path.abspath(os.path.join(CVS_DIR, f"{base_name}.docx"))
        if docx_path.startswith(os.path.abspath(CVS_DIR) + os.sep) and os.path.exists(docx_path):
            return extract_text_from_docx(docx_path)
            
        txt_path = os.path.abspath(os.path.join(CVS_DIR, f"{base_name}.txt"))
        if txt_path.startswith(os.path.abspath(CVS_DIR) + os.sep) and os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Error reading txt CV {txt_path}: {e}")
                
    print(f"Warning: CV file not found for versions {versions_to_try} in {CVS_DIR}")
    return None
