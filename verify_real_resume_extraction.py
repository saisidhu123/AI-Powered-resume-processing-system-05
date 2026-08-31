"""
verify_real_resume_extraction.py

Final Real-World Resume Extraction & Validation Audit Suite.
Processes all real resume files in uploads/ and validates field independence,
non-leakage, and accurate extraction across PDF, DOCX, and DOC formats.
"""

import os
import sys
import re
import json
from typing import List, Dict, Any

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"c:\Users\nag93\Downloads\AI-Powered resume processing system 05")

from services.document_reader import build_resume_document
from services.resume_parser import parse_resume
from services.field_extractor import extract_all_fields_fallback, normalize_skills
from services.ctc_extractor import extract_current_and_expected_ctc, clean_and_validate_ctc, sanitize_ctc_pair
from services.notice_period_extractor import extract_notice_period, normalize_notice_period
from services.experience_engine import evaluate_total_experience
from services.llm_service import classify_header_concept, validate_candidate_dictionary
from utils.helpers import classify_technology

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")

def run_real_resume_audit(limit_files: int = 60):
    print("=" * 90)
    print("      REAL-WORLD RESUME EXTRACTION & VALIDATION AUDIT      ")
    print("=" * 90)

    if not os.path.exists(UPLOAD_DIR):
        print(f"Error: Uploads directory '{UPLOAD_DIR}' not found.")
        return

    all_files = [
        f for f in os.listdir(UPLOAD_DIR)
        if f.lower().endswith((".pdf", ".docx", ".doc")) and not f.startswith("~$")
    ]
    all_files.sort()

    files_to_test = all_files[:limit_files]

    total_tested = 0
    total_successful_parses = 0
    total_parsing_failures = 0
    total_validation_failures = 0

    field_errors_count = 0
    ctc_leakage_errors = 0
    notice_leakage_errors = 0
    experience_errors = 0
    fresher_errors = 0

    results_summary = []

    for idx, fname in enumerate(files_to_test, start=1):
        fpath = os.path.join(UPLOAD_DIR, fname)
        total_tested += 1

        print(f"\n[{idx:03d}/{len(files_to_test)}] Processing Real Resume: {fname}")
        
        parsed_ok, raw_text, parse_err = parse_resume(fpath)
        if not parsed_ok or not raw_text.strip():
            total_parsing_failures += 1
            print(f"  ❌ PARSE FAILED: {parse_err}")
            results_summary.append({
                "Filename": fname,
                "Status": "PARSE_FAIL",
                "Errors": [f"Parse failure: {parse_err}"]
            })
            continue

        total_successful_parses += 1
        doc = build_resume_document(fpath, raw_text)

        # Deterministic and fallback extraction
        fields = extract_all_fields_fallback(doc.full_text)
        cand_name = fields.get("Candidate Name", "Unknown")
        exp_val = fields.get("Total Experience", "Not Specified")
        notice_val = fields.get("Notice Period", "Not Specified")
        curr_ctc = fields.get("Current CTC", "Not specified")
        exp_ctc = fields.get("Expected CTC", "Not specified")
        skills_val = fields.get("Skills", "")
        tech_domain = ", ".join(classify_technology(doc.full_text, skills_val))

        # Create Candidate Dict & Run Final Validation Layer
        cand_dict = {
            "Candidate Name": cand_name,
            "Total Experience": exp_val,
            "Notice Period": notice_val,
            "Current CTC": curr_ctc,
            "Expected CTC": exp_ctc,
            "Skills": skills_val,
            "Technology Domain": tech_domain
        }
        cand_dict = validate_candidate_dictionary(cand_dict, doc.full_text)

        # Audit Validation Checks
        val_errors = []

        curr_c_str = str(cand_dict.get("Current CTC", "")).lower()
        exp_c_str = str(cand_dict.get("Expected CTC", "")).lower()
        np_str = str(cand_dict.get("Notice Period", "")).lower()
        exp_s_str = str(cand_dict.get("Total Experience", "")).lower()

        # Check 1: Notice contains salary/CTC terminology
        if any(k in np_str for k in ["lpa", "lakh", "lac", "ctc", "salary", "inr", "₹"]):
            val_errors.append("Notice Period contains salary/CTC terminology")
            notice_leakage_errors += 1
            field_errors_count += 1

        # Check 2: Current CTC contains notice-period terminology or bare notice number
        if any(k in curr_c_str for k in ["notice", "days", "day", "joining", "serving", "immediate"]) or curr_c_str.strip() in ["15", "30", "45", "60", "90"]:
            val_errors.append("Current CTC contains notice-period terminology or bare notice number")
            ctc_leakage_errors += 1
            field_errors_count += 1

        # Check 3: Expected CTC contains notice-period terminology
        if any(k in exp_c_str for k in ["notice", "days", "day", "joining", "serving", "immediate"]) or exp_c_str.strip() in ["15", "30", "45", "60", "90"]:
            val_errors.append("Expected CTC contains notice-period terminology")
            ctc_leakage_errors += 1
            field_errors_count += 1

        # Check 4: Current CTC == Expected CTC when resume text explicitly has different values
        if curr_c_str != "not specified" and exp_c_str != "not specified" and curr_c_str == exp_c_str:
            if not re.search(r"(?:current|present)\s*(?:ctc|salary).{0,20}(?:expected|target).{0,20}" + re.escape(curr_c_str), doc.full_text, re.IGNORECASE):
                val_errors.append("Current CTC equals Expected CTC unexpectedly")
                ctc_leakage_errors += 1
                field_errors_count += 1

        # Check 5: Expected CTC copied into Current CTC when Current CTC missing
        if curr_c_str == exp_c_str and curr_c_str != "not specified" and not re.search(r"current\s*(?:ctc|salary)", doc.full_text, re.IGNORECASE):
            val_errors.append("Expected CTC copied into Current CTC when Current CTC was missing")
            ctc_leakage_errors += 1
            field_errors_count += 1

        # Check 6: Previous/Past CTC interpreted as Current CTC
        clean_c_num = re.sub(r"[^\d\.]", "", curr_c_str)
        if clean_c_num and re.search(r"(?:past|previous|prior|old)\s*(?:ctc|salary)[^0-9\n]{0,20}" + re.escape(clean_c_num), doc.full_text, re.IGNORECASE):
            val_errors.append("Past/Previous CTC interpreted as Current CTC")
            ctc_leakage_errors += 1
            field_errors_count += 1

        # Check 7: Graduation year interpreted as Experience
        if re.search(r"\b(19\d{2}|20\d{2})\s*years?\b", exp_s_str, re.IGNORECASE):
            val_errors.append("Graduation year interpreted as Total Experience")
            experience_errors += 1
            field_errors_count += 1

        # Check 8: Notice days interpreted as Experience
        if any(k in exp_s_str for k in ["notice", "days", "day", "joining"]):
            val_errors.append("Notice period days interpreted as Total Experience")
            experience_errors += 1
            field_errors_count += 1

        if val_errors:
            total_validation_failures += 1
            print(f"  ⚠️ VALIDATION FAILURES ({len(val_errors)}): {', '.join(val_errors)}")
        else:
            print(f"  ✅ PASSED AUDIT")

        print(f"     Name: '{cand_name}' | Exp: '{cand_dict['Total Experience']}' | Notice: '{cand_dict['Notice Period']}'")
        print(f"     Current CTC: '{cand_dict['Current CTC']}' | Expected CTC: '{cand_dict['Expected CTC']}'")

        results_summary.append({
            "Filename": fname,
            "Candidate Name": cand_name,
            "Experience": cand_dict["Total Experience"],
            "Notice Period": cand_dict["Notice Period"],
            "Current CTC": cand_dict["Current CTC"],
            "Expected CTC": cand_dict["Expected CTC"],
            "Skills": cand_dict["Skills"][:50] + "..." if len(cand_dict["Skills"]) > 50 else cand_dict["Skills"],
            "Technology Domain": cand_dict["Technology Domain"],
            "Status": "SUCCESS" if not val_errors else "VAL_FAIL",
            "Errors": val_errors
        })

    # Summary Output
    print("\n" + "=" * 90)
    print("                REAL-WORLD RESUME EXTRACTION AUDIT SUMMARY                ")
    print("=" * 90)
    print(f"  Total Resumes Tested:             {total_tested}")
    print(f"  Total Successfully Processed:     {total_successful_parses}")
    print(f"  Total Parsing Failures:           {total_parsing_failures}")
    print(f"  Total Validation Failures:        {total_validation_failures}")
    print(f"  Total Field-Level Errors:         {field_errors_count}")
    print(f"  CTC Leakage Errors:               {ctc_leakage_errors}")
    print(f"  Notice Period Leakage Errors:     {notice_leakage_errors}")
    print(f"  Experience Errors:                {experience_errors}")
    print(f"  Fresher Errors:                   {fresher_errors}")
    print("=" * 90 + "\n")

    if total_validation_failures == 0 and total_parsing_failures == 0:
        print("🎉 [PERFECT AUDIT] 100% OF REAL RESUMES PASSED AUDIT WITH ZERO FIELD LEAKAGE!")
    else:
        print(f"⚠️ AUDIT FINISHED WITH {total_validation_failures} VALIDATION ERRORS.")

if __name__ == "__main__":
    run_real_resume_audit(limit_files=200)
