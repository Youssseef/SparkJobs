import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from title_matcher import is_title_relevant, get_role_core
from cv_processor import anonymize_cv_text
from deduplicator import is_job_seen, mark_job_as_seen, cleanup_old_jobs
from telegram_sender import safe_callback_id, escape_html
from ai_matcher import clean_json_response
from fraud_detector import analyze_job_for_fraud
from scraper import safe_str, is_url_reliable
from config_loader import load_config, load_status_tracker

class TestSparkJobsSuite(unittest.TestCase):

    def test_title_relevance(self):
        targets = ["React Developer", "Frontend Engineer"]
        self.assertTrue(is_title_relevant("Senior React Developer", targets))
        self.assertTrue(is_title_relevant("Lead Frontend Engineer", targets))
        self.assertFalse(is_title_relevant("Product Designer", targets))
        self.assertFalse(is_title_relevant("DevOps Engineer", targets))

    def test_role_core_extraction(self):
        self.assertEqual(get_role_core("Senior Product Designer"), "designer")
        self.assertEqual(get_role_core("Lead Frontend Engineer"), "frontend")

    def test_cv_anonymization(self):
        raw_cv = """
        John Doe
        Summary:
        Professional Frontend Developer.
        Email: john.doe@gmail.com
        Phone: +1 202 555 0123
        Portfolio: https://github.com/johndoe
        Experienced in building React applications and scalable UI components for enterprise products.
        """
        anonymized = anonymize_cv_text(raw_cv)
        self.assertNotIn("john.doe@gmail.com", anonymized)
        self.assertNotIn("+1 202 555 0123", anonymized)
        self.assertNotIn("https://github.com/johndoe", anonymized)
        self.assertIn("[ANONYMIZED_EMAIL]", anonymized)
        self.assertIn("[ANONYMIZED_PHONE]", anonymized)
        self.assertIn("[ANONYMIZED_LINK]", anonymized)

    def test_in_memory_deduplication(self):
        seen_db = {}
        self.assertFalse(is_job_seen(seen_db, "job-101"))
        mark_job_as_seen(seen_db, "job-101", "React Developer", "Acme Corp")
        self.assertTrue(is_job_seen(seen_db, "job-101"))

    def test_telegram_callback_length_guard(self):
        short_id = "job-123"
        cb_short = safe_callback_id(short_id, "applied")
        self.assertEqual(cb_short, "applied:job-123")
        self.assertLessEqual(len(cb_short.encode('utf-8')), 64)

        long_id = "indeed-super-long-job-id-that-exceeds-telegram-sixty-four-bytes-limit-12345678901234567890"
        cb_long = safe_callback_id(long_id, "applied")
        self.assertLessEqual(len(cb_long.encode('utf-8')), 64)
        self.assertTrue(cb_long.startswith("applied:"))

    def test_llm_json_cleaning(self):
        wrapped_json = "```json\n{\n  \"match_score\": 90,\n  \"risk_level\": \"Low\"\n}\n```"
        parsed = clean_json_response(wrapped_json)
        self.assertEqual(parsed.get("match_score"), 90)

    def test_fraud_detector(self):
        clean_job = {
            "title": "Senior React Engineer",
            "description": "We are seeking a highly skilled Senior React Engineer to join our growing engineering team. In this role, you will be responsible for building responsive web user interfaces, collaborating with product managers and UI designers, optimizing application performance, and maintaining clean code standards across all web platforms.",
            "company": "Acme Inc",
            "url": "https://acme.com/jobs/123"
        }
        res = analyze_job_for_fraud(clean_job)
        self.assertFalse(res["is_suspicious"])
        self.assertEqual(res["risk_level"], "Low")

    # L-03 Fix: Tests for scraper utilities, config loader, and Arabic fraud detection
    def test_scraper_safe_str(self):
        self.assertEqual(safe_str("Hello World"), "Hello World")
        self.assertEqual(safe_str(None), "")
        self.assertEqual(safe_str(float('nan')), "")

    def test_is_url_reliable(self):
        self.assertTrue(is_url_reliable("https://linkedin.com/jobs/view/123", "LinkedIn"))
        self.assertFalse(is_url_reliable("https://google.com/url?q=http://bad.com", "Google Jobs"))
        self.assertFalse(is_url_reliable("https://weworkremotely.com/categories/remote-dev-jobs", "We Work Remotely"))

    def test_arabic_fraud_keywords(self):
        arabic_scam_job = {
            "title": "مطلوب فوراً موظف إدخال بيانات",
            "description": "عمل من المنزل براتب مجزي جداً بدون خبرة. تواصل معنا فوراً على واتساب لإرسال الـ CV ورسوم التسجيل.",
            "company": "غير محدد",
            "url": "https://example.com"
        }
        res = analyze_job_for_fraud(arabic_scam_job)
        self.assertTrue(res["is_suspicious"])
        self.assertEqual(res["risk_level"], "High")

if __name__ == "__main__":
    unittest.main()
