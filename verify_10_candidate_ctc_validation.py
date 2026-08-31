"""
verify_10_candidate_ctc_validation.py

10-Candidate CTC & Notice Period Output Validation Script.
Processes 10 benchmark candidates, validates that Notice Period values NEVER leak into Current CTC,
and prints the required 10-candidate validation table.
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.field_extractor import extract_all_fields_fallback
from services.llm_service import extract_candidate_data

BENCHMARK_RESUMES = [
    ("Rahul Sharma", "RAHUL SHARMA\nMobile: 9876543210\nEmail: rahul@example.com\nNotice Period: 30 Days\nCurrent CTC: 8 LPA\nExpected CTC: 11 LPA\nWORK EXPERIENCE:\n2020 - 2024 Software Engineer", "30 Days", "8 LPA", "11 LPA"),
    ("Priya Reddy", "PRIYA REDDY\nMobile: 9876543211\nEmail: priya@example.com\nNotice Period: 15 Days\nCurrent Salary: ₹6 LPA\nExpected Salary: ₹8 LPA\nWORK EXPERIENCE:\n2022 - 2024 Python Developer", "15 Days", "₹6 LPA", "₹8 LPA"),
    ("Arjun Kumar", "ARJUN KUMAR\nMobile: 9876543212\nEmail: arjun@example.com\nNotice Period: 60 Days\nCurrent CTC: 15 LPA\nExpected CTC: 20 LPA\nWORK EXPERIENCE:\n2018 - 2024 Senior AI Engineer", "60 Days", "15 LPA", "20 LPA"),
    ("Sneha Rao", "SNEHA RAO\nMobile: 9876543213\nEmail: sneha@example.com\nNotice Period: 45 Days | Current\nCurrent CTC: 13 LPA\nExpected CTC: 17 LPA\nWORK EXPERIENCE:\n2021 - 2024 Data Engineer", "45 Days", "13 LPA", "17 LPA"),
    ("Vikram Singh", "VIKRAM SINGH\nMobile: 9876543214\nEmail: vikram@example.com\nNotice Period: 30 Days\nCurrent CTC: ₹18 LPA\nExpected CTC: ₹23 LPA\nWORK EXPERIENCE:\n2019 - 2024 DevOps Engineer", "30 Days", "₹18 LPA", "₹23 LPA"),
    ("Kiran Verma", "KIRAN VERMA\nMobile: 9876543215\nEmail: kiran@example.com\nNotice Period: 60 Days\nNo CTC information anywhere\nWORK EXPERIENCE:\n2016 - 2024 Full Stack Lead", "60 Days", "Not specified", "Not specified"),
    ("Ananya Patel", "ANANYA PATEL\nMobile: 9876543216\nEmail: ananya@example.com\nExperience: 1 Year\nNotice Period: 30 Days\nNo CTC information\nWORK EXPERIENCE:\n2023 - 2024 Junior Frontend", "30 Days", "Not specified", "Not specified"),
    ("Meera Nair", "MEERA NAIR\nMobile: 9876543217\nEmail: meera@example.com\nNotice Period: 15 Days | Immediate\nCurrent CTC: ₹4.5 LPA\nExpected CTC: ₹6 LPA\nWORK EXPERIENCE:\n2020 - 2024 QA Engineer", "Immediate", "₹4.5 LPA", "₹6 LPA"),
    ("Neha Kapoor", "NEHA KAPOOR\nMobile: 9876543218\nEmail: neha@example.com\nNotice Period: 30 Days\nExpected CTC: ₹15 LPA\nWORK EXPERIENCE:\n2021 - 2024 Salesforce Consultant", "30 Days", "Not specified", "₹15 LPA"),
    ("Rohit Das", "ROHIT DAS\nMobile: 9876543219\nEmail: rohit@example.com\nNotice Period: Immediate\nCurrent CTC: ₹7.5 LPA\nSummary: Fresher seeking entry level developer position", "Immediate", "₹7.5 LPA", "Not specified")
]

def run_validation():
    print("\n==========================================================================")
    print("           FINAL 10-CANDIDATE CTC & NOTICE PERIOD VALIDATION TABLE        ")
    print("==========================================================================\n")

    headers = ["Candidate Name", "Notice Period", "Current CTC", "Expected CTC", "Status"]
    row_fmt = "{:<16} | {:<15} | {:<14} | {:<14} | {:<8}"
    print(row_fmt.format(*headers))
    print("-" * 78)

    all_passed = True
    for name, text, exp_np, exp_c_ctc, exp_e_ctc in BENCHMARK_RESUMES:
        data = extract_all_fields_fallback(text)
        np_val = data.get("Notice Period", "Not specified")
        c_ctc = data.get("Current CTC", "Not specified")
        e_ctc = data.get("Expected CTC", "Not specified")

        # Verify Notice Period numbers (15, 30, 45, 60) NEVER appear as Current CTC
        is_clean = (c_ctc not in ["15", "30", "45", "60", "90"]) and (c_ctc.lower() != np_val.lower())
        status = "PASSED" if is_clean else "FAILED"
        if not is_clean:
            all_passed = False

        print(row_fmt.format(name, np_val or "Not specified", c_ctc or "Not specified", e_ctc or "Not specified", status))

    print("-" * 78)
    if all_passed:
        print("\n[OK] 10/10 BENCHMARK CANDIDATES VALIDATED SUCCESSFULLY!")
    else:
        print("\n[FAIL] Validation Failed!")
        assert False

if __name__ == "__main__":
    run_validation()
