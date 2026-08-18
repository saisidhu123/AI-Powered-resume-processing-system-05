import os
import glob
from services.resume_parser import parse_resume
from services.excel_service import read_excel_headers, populate_excel_template
from services.llm_service import extract_candidate_data

def test_all_resumes():
    headers = ['Candidate Name', 'Mobile Number', 'Email Address', 'Total Experience', 'Skills', 'Notice Period']

    resume_files = [f for f in glob.glob("uploads/*") if f.endswith((".pdf", ".docx"))]
    print(f"\n==================== BATCH TEST ({len(resume_files)} Files) ====================")

    for rfile in resume_files:
        filename = os.path.basename(rfile)
        print(f"\n--- Testing File: {filename} ---")
        ok, text, err = parse_resume(rfile)
        if not ok:
            print(f"[FAIL] Resume parsing failed: {err}")
            continue

        print(f"Text Extracted Successfully ({len(text)} chars)")
        ok_llm, cand_data, raw, err_llm = extract_candidate_data(text, headers)
        if not ok_llm:
            print(f"[FAIL] LLM extraction failed: {err_llm}")
            continue

        print("Extracted Candidate Fields:")
        for h in headers:
            val = cand_data.get(h, "(Blank)")
            print(f"   - {h}: {val}")

if __name__ == "__main__":
    test_all_resumes()
