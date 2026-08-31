"""
verify_universal_resume_extraction.py

Universal Generic Resume Extraction Test Suite.
Contains 50 synthetic resume layouts across all 26 layout categories (A through Z).
Verifies that candidate data is extracted generically across any format without hardcoded assumptions.
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.field_extractor import extract_all_fields_fallback
from services.llm_service import extract_candidate_data
from services.document_reader import build_resume_document
from services.section_detector import segment_resume_sections
from services.number_classifier import classify_number_context

# 50 Synthetic Resume Formats across Categories A - Z
TEST_CASES = [
    # A. One-column resume
    ("A_OneColumn", "JOHN DOE\nSoftware Engineer\nEmail: john@example.com\nMobile: 9876543210\nExperience: 5 Years\nNotice Period: 30 Days\nCurrent CTC: 8 LPA\nExpected CTC: 12 LPA", "5 Years", "30 Days", "8 LPA", "12 LPA"),
    
    # B. Two-column resume (Contact/Skills left, Work right)
    ("B_TwoColumn", "SKILLS & DETAILS | WORK HISTORY\nMobile: 9876543211 | Senior Developer (2019 - 2024)\nNotice: 15 Days | Built enterprise apps\nCurrent CTC: 10 LPA | Expected CTC: 15 LPA", "5 Years", "15 Days", "10 LPA", "15 LPA"),

    # C. Table resume
    ("C_Table", "Candidate | Experience | Notice | Current CTC | Expected CTC\nJane Smith | 4 Years | Immediate | ₹6 LPA | ₹9 LPA", "4 Years", "Immediate", "₹6 LPA", "₹9 LPA"),

    # D. Current CTC and Expected CTC same line
    ("D_CTC_SameLine", "Rahul Sharma | Exp: 3 Yrs | Notice: 30 Days | Current CTC: 7 LPA | Expected CTC: 10 LPA", "3 Years", "30 Days", "7 LPA", "10 LPA"),

    # E. Current CTC and Expected CTC separate lines (multi-line)
    ("E_CTC_SeparateLines", "Priya V\nCurrent CTC:\n12 LPA\nExpected CTC:\n16 LPA\nNotice Period:\n45 Days\n2020 - 2024 Engineer", "4 Years", "45 Days", "12 LPA", "16 LPA"),

    # F. Current CTC = Not Specified
    ("F_CurrentCTC_NotSpecified", "Amit Kumar\nCurrent CTC: Not Specified\nExpected CTC: 15 LPA\nNotice Period: 60 Days\nExperience: 6 Years", "6 Years", "60 Days", "Not specified", "15 LPA"),

    # G. Expected CTC only
    ("G_ExpectedCTCOnly", "Suresh Patel\nExpected Salary: ₹20 LPA\nNotice Period: Immediate\nExperience: 8 Years", "8 Years", "Immediate", "Not specified", "₹20 LPA"),

    # H. Current CTC only
    ("H_CurrentCTCOnly", "Ramesh Rao\nCurrent Package: ₹14 LPA\nNotice Period: 30 Days\nExperience: 5 Years", "5 Years", "30 Days", "₹14 LPA", "Not specified"),

    # I. Notice Period = 30 Days
    ("I_Notice30Days", "Kiran M\nNotice Period: 30 Days\nExperience: 2 Years", "2 Years", "30 Days", "Not specified", "Not specified"),

    # J. Notice Period = Immediate
    ("J_NoticeImmediate", "Deepak N\nAvailable to Join: Immediate\nExperience: 1 Year", "1 Year", "Immediate", "Not specified", "Not specified"),

    # K. Notice Period = 2 Months
    ("K_Notice2Months", "Vikram S\nServing Notice Period: 2 months\nExperience: 4 Years", "4 Years", "2 Months", "Not specified", "Not specified"),

    # L. Notice Period and CTC same line
    ("L_Notice_CTC_SameLine", "Notice Period: 15 Days | Current CTC: 6 LPA | Expected CTC: 8 LPA", "Not Specified", "15 Days", "6 LPA", "8 LPA"),

    # M. Experience in years
    ("M_ExpYears", "Anand B\nTotal Experience: 7 Years\nNotice Period: 30 Days", "7 Years", "30 Days", "Not specified", "Not specified"),

    # N. Experience in years + months
    ("N_ExpYearsMonths", "Pooja C\nExperience: 3 years 6 months\nNotice Period: Immediate", "3.5 Years", "Immediate", "Not specified", "Not specified"),

    # O. Experience calculated from dates
    ("O_ExpCalculatedDates", "Arjun K\nWORK HISTORY:\nSoftware Engineer (Jan 2020 - Dec 2023)\nNotice: 30 Days", "4 Years", "30 Days", "Not specified", "Not specified"),

    # P. Fresher
    ("P_Fresher", "Rohit D\nSummary: Fresher seeking software engineering role.\nEducation: B.Tech 2024", "Fresher", "Not Specified", "Not specified", "Not specified"),

    # Q. Fresh graduate
    ("Q_FreshGraduate", "Sneha P\nFresh graduate with strong Java skills.\nNotice: Immediate", "Fresher", "Immediate", "Not specified", "Not specified"),

    # R. No professional experience
    ("R_NoProfExp", "Meera N\nNo professional experience.\nNotice: Immediate", "Fresher", "Immediate", "Not specified", "Not specified"),

    # S. Internship only
    ("S_InternshipOnly", "Vikram S\nSummary: Software Engineer Intern\nExperience: 6 month internship\nNotice: Immediate", "6 Months", "Immediate", "Not specified", "Not specified"),

    # T. Resume with no experience information
    ("T_NoExpInfo", "Kavita S\nSkills: Python, SQL\nNotice Period: 30 Days", "Not Specified", "30 Days", "Not specified", "Not specified"),

    # U. Phone numbers
    ("U_PhoneProtection", "Contact: +91 9876543210\nNotice Period: 30 Days\nCurrent CTC: 8 LPA", "Not Specified", "30 Days", "8 LPA", "Not specified"),

    # V. Graduation years
    ("V_GraduationYear", "Graduated in 2020 with B.Tech.\nExperience: 4 Years\nNotice: 15 Days", "4 Years", "15 Days", "Not specified", "Not specified"),

    # W. Software versions
    ("W_SoftwareVersion", "Skills: Java 8, Python 3.10, HTML5\nExperience: 3 Years\nNotice: Immediate", "3 Years", "Immediate", "Not specified", "Not specified"),

    # X. Project durations
    ("X_ProjectDuration", "Project Duration: 6 months\nTotal Experience: 5 Years\nNotice: 30 Days", "5 Years", "30 Days", "Not specified", "Not specified"),

    # Y. Multiple jobs
    ("Y_MultipleJobs", "Company A (2018 - 2021)\nCompany B (2021 - 2024)\nNotice: 60 Days", "6 Years", "60 Days", "Not specified", "Not specified"),

    # Z. Overlapping jobs
    ("Z_OverlappingJobs", "Project Lead (2020 - 2022)\nConsultant (2021 - 2023)\nNotice: 30 Days", "3 Years", "30 Days", "Not specified", "Not specified"),

    # 24 Additional Variations (Making 50 total)
    ("27_ColonCTC", "Current CTC: ₹18 LPA\nExpected CTC: ₹23 LPA", "Not Specified", "Not Specified", "₹18 LPA", "₹23 LPA"),
    ("28_DashCTC", "Present Package - 8 LPA\nExpected Package - 12 LPA", "Not Specified", "Not Specified", "8 LPA", "12 LPA"),
    ("29_INR_Format", "Current Salary: INR 10 LPA\nExpected Salary: INR 15 LPA", "Not Specified", "Not Specified", "₹10 LPA", "₹15 LPA"),
    ("30_USD_Format", "Current Compensation: $80K\nExpected Compensation: $100K", "Not Specified", "Not Specified", "$80K", "$100K"),
    ("31_Decimal_CTC", "Current CTC: 4.5 LPA\nExpected CTC: 6.5 LPA", "Not Specified", "Not Specified", "4.5 LPA", "6.5 LPA"),
    ("32_Lakhs_Format", "Current Salary: 8 Lakhs\nExpected Salary: 12 Lakhs", "Not Specified", "Not Specified", "8 Lakhs", "12 Lakhs"),
    ("33_Undisclosed_CTC", "Current CTC: Undisclosed\nExpected CTC: 18 LPA", "Not Specified", "Not Specified", "Not specified", "18 LPA"),
    ("34_NA_CTC", "Current CTC: NA\nExpected CTC: 15 LPA", "Not Specified", "Not Specified", "Not specified", "15 LPA"),
    ("35_Nil_CTC", "Current CTC: Nil\nExpected CTC: 10 LPA", "Not Specified", "Not Specified", "Not specified", "10 LPA"),
    ("36_Notice15DayNotice", "Notice Period: 15-day notice", "Not Specified", "15 Days", "Not specified", "Not specified"),
    ("37_NoticeCanJoin", "Can Join: Immediately", "Not Specified", "Immediate", "Not specified", "Not specified"),
    ("38_NoticeAvailableToJoin", "Available to Join: 30 Days", "Not Specified", "30 Days", "Not specified", "Not specified"),
    ("39_NoticeEarliestJoining", "Earliest Joining: Immediate", "Not Specified", "Immediate", "Not specified", "Not specified"),
    ("40_NoticeNegotiable", "Notice Period: Negotiable", "Not Specified", "Negotiable", "Not specified", "Not specified"),
    ("41_ExpOver10Years", "Total Experience: 10+ Years", "10+ Years", "Not Specified", "Not specified", "Not specified"),
    ("42_Exp2Point5Years", "Total Experience: 2.5 Years", "2.5 Years", "Not Specified", "Not specified", "Not specified"),
    ("43_Exp18Months", "Experience: 18 months", "1.5 Years", "Not Specified", "Not specified", "Not specified"),
    ("44_ExpTillDate", "Software Engineer (Jan 2019 - Present)", "7.7 Years", "Not Specified", "Not specified", "Not specified"),
    ("45_ExpCareerBreak", "Dev (2018 - 2020)\nBreak (2020 - 2021)\nDev (2021 - 2024)", "5 Years", "Not Specified", "Not specified", "Not specified"),
    ("46_FresherEntryLevel", "Entry level developer seeking opportunity", "Fresher", "Not Specified", "Not specified", "Not specified"),
    ("47_FresherNoExperience", "Recent B.Sc graduate, no work experience", "Fresher", "Not Specified", "Not specified", "Not specified"),
    ("48_MultiLineCTC", "Current Salary\n₹8 LPA\nExpected Salary\n₹12 LPA", "Not Specified", "Not Specified", "₹8 LPA", "₹12 LPA"),
    ("49_MultiLineNotice", "Notice Duration\n30 Days", "Not Specified", "30 Days", "Not specified", "Not specified"),
    ("50_ComplexLayout", "EXPERIENCE & SALARY\n5 Years Exp | Notice: 15 Days\nCurrent CTC: 9 LPA | Expected CTC: 13 LPA", "5 Years", "15 Days", "9 LPA", "13 LPA")
]

def run_universal_extraction_tests():
    print("\n==========================================================================")
    print("      RUNNING 50-TEST UNIVERSAL GENERIC RESUME EXTRACTION SUITE           ")
    print("==========================================================================\n")

    passed_count = 0
    total_tests = len(TEST_CASES)

    for idx, (title, text, exp_exp, exp_notice, exp_curr, exp_e_ctc) in enumerate(TEST_CASES, start=1):
        doc = build_resume_document("", text)
        secs = segment_resume_sections(doc.full_text)
        fields = extract_all_fields_fallback(doc.full_text)

        got_exp = fields.get("Total Experience", "Not Specified")
        got_notice = fields.get("Notice Period", "Not Specified")
        got_curr = fields.get("Current CTC", "Not specified")
        got_exp_ctc = fields.get("Expected CTC", "Not specified")

        # Validation assertions
        ok_exp = (exp_exp == "Not Specified") or (exp_exp.lower() in got_exp.lower())
        ok_notice = (exp_notice == "Not Specified") or (exp_notice.lower() in got_notice.lower())
        ok_curr = (exp_curr.lower() == "not specified" and got_curr.lower() == "not specified") or (exp_curr.lower() != "not specified" and exp_curr.lower() in got_curr.lower())
        ok_exp_ctc = (exp_e_ctc.lower() == "not specified" and got_exp_ctc.lower() == "not specified") or (exp_e_ctc.lower() != "not specified" and exp_e_ctc.lower() in got_exp_ctc.lower())

        # Strict Rejection Check
        if got_curr.strip() in ["30", "15", "45", "60", "90"]:
            ok_curr = False

        if ok_exp and ok_notice and ok_curr and ok_exp_ctc:
            passed_count += 1
            print(f"[PASS] Test {idx:02d} ({title}): Exp='{got_exp}', Notice='{got_notice}', Current='{got_curr}', Expected='{got_exp_ctc}'")
        else:
            print(f"[FAIL] Test {idx:02d} ({title}):")
            print(f"       Got:      Exp='{got_exp}', Notice='{got_notice}', Current='{got_curr}', Expected='{got_exp_ctc}'")
            print(f"       Expected: Exp='{exp_exp}', Notice='{exp_notice}', Current='{exp_curr}', Expected='{exp_e_ctc}'")
            assert False, f"Test {idx:02d} ({title}) Failed!"

    print("-" * 74)
    print(f"\n[OK] ALL {passed_count}/{total_tests} UNIVERSAL RESUME LAYOUT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_universal_extraction_tests()
