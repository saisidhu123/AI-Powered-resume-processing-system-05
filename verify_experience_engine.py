import os
import sys
from services.experience_engine import (
    extract_explicit_experience,
    calculate_experience_from_dates,
    detect_fresher,
    evaluate_total_experience
)

def run_experience_engine_tests():
    print("\n========================================================================")
    print("      RUNNING 40+ GENERIC TOTAL EXPERIENCE EXTRACTION ENGINE TESTS      ")
    print("========================================================================\n")

    passed_count = 0
    total_tests = 0

    def assert_exp(test_id: int, test_name: str, input_text: str, expected_contains: list, forbidden_contains: list = None):
        nonlocal passed_count, total_tests
        total_tests += 1
        res = evaluate_total_experience(input_text)
        disp = res.display_str
        src = res.source

        ok = True
        for req in expected_contains:
            if req.lower() not in disp.lower():
                ok = False
                break
        if forbidden_contains:
            for forb in forbidden_contains:
                if forb.lower() in disp.lower():
                    ok = False
                    break

        if ok:
            passed_count += 1
            print(f"[PASS] Test {test_id:02d} ({test_name}): '{disp}' (Source: {src})")
        else:
            print(f"[FAIL] Test {test_id:02d} ({test_name}): Got '{disp}' (Source: {src}), Expected: {expected_contains}")
            assert ok, f"Test {test_id} Failed!"

    # 1. Explicit statements
    assert_exp(1, "Explicit 5 years", "Summary: Senior engineer with 5 years of experience.", ["5 Years"])
    assert_exp(2, "Explicit 5+ years", "Professional Summary: Lead Developer with 5+ years experience in Python.", ["5+ Years"])
    assert_exp(3, "Explicit decimal 2.5 years", "Summary: Developer with 2.5 years of experience.", ["2.5 Years"])
    assert_exp(4, "Explicit 18 months", "Summary: Software Analyst with 18 months of experience.", ["1.5 Years"])
    assert_exp(5, "Explicit 3 years 6 months", "Summary: Backend engineer with 3 years 6 months experience.", ["3.5 Years"])
    assert_exp(6, "Explicit Over 10 years", "Summary: Executive with Over 10 years of experience.", ["10+ Years"])

    # 2. Freshers & Students
    assert_exp(7, "Explicit Fresher", "Fresher looking for entry level software role.", ["Fresher"])
    assert_exp(8, "Explicit Fresh Graduate", "Fresh graduate with no professional experience.", ["Fresher"])
    assert_exp(9, "No Work Experience", "Recent CS graduate. No professional experience.", ["Fresher"])

    # 3. Employment Date Ranges
    assert_exp(10, "Jan 2020 - Present", "WORK EXPERIENCE:\nSoftware Engineer (Jan 2020 - Present)", ["Years"])
    assert_exp(11, "2018 - 2022", "WORK EXPERIENCE:\nSoftware Engineer (2018 - 2022)", ["4 Years"])
    assert_exp(12, "March 2019 to July 2023", "WORK EXPERIENCE:\nDeveloper (March 2019 to July 2023)", ["4.4 Years"])

    # 4. Multiple Jobs
    assert_exp(13, "Multiple Sequential Jobs", "WORK EXPERIENCE:\nCompany A: Jan 2018 - Dec 2020\nCompany B: Jan 2021 - Dec 2023", ["6 Years"])
    
    # 5. Overlapping Jobs (Merging)
    assert_exp(14, "Overlapping Jobs", "WORK EXPERIENCE:\nJob A: 2018 - 2022\nJob B: 2020 - 2024", ["6 Years"])

    # 6. Career Break (Gap Exclusion)
    assert_exp(15, "Career Break", "WORK EXPERIENCE:\nJob A: 2015 - 2018\nCareer Break: 2018 - 2021\nJob B: 2021 - 2024", ["6 Years"])

    # 7. Short Experience
    assert_exp(16, "Candidate with 6 months", "Summary: Developer with 6 months experience.", ["6 Months"])
    assert_exp(17, "Candidate with 1 year", "Summary: Software Engineer with 1 year experience.", ["1 Year"])

    # 8. Non-experience Number Rejection
    assert_exp(18, "Phone Number Rejection", "Rahul Sharma\nPhone: +91 90000 10003\nEmail: rahul@example.com\nWORK EXPERIENCE:\nJan 2020 - Jan 2024", ["4 Years"], ["91", "90000", "10003"])
    assert_exp(19, "CTC / Salary Rejection", "Summary: Python Engineer\nCurrent CTC: 15 LPA\nExpected CTC: 20 LPA\nWORK EXPERIENCE:\n2019 - 2024", ["5 Years"], ["15", "20"])
    assert_exp(20, "Notice Period Rejection", "Notice Period: 60 Days\nWORK EXPERIENCE:\n2021 - 2024", ["3 Years"], ["60"])
    assert_exp(21, "Graduation Year Rejection", "EDUCATION:\nB.Tech CSE (Graduated in 2018)\nWORK EXPERIENCE:\n2020 - 2024", ["4 Years"], ["2018"])
    assert_exp(22, "Software Version Rejection", "SKILLS:\nJava 8, Python 3.10, HTML5, SQL 2019\nWORK EXPERIENCE:\n2021 - 2024", ["3 Years"], ["8", "3.10"])

    # 9. Senior Executive
    assert_exp(23, "Senior Executive 20+ Years", "Professional Summary: Executive Director with 22 years of experience.", ["22+ Years"])

    # 10. Date format variations
    assert_exp(24, "MM/YYYY format", "WORK EXPERIENCE:\n06/2019 - 06/2023", ["4 Years"])
    assert_exp(25, "Till date / Current", "WORK EXPERIENCE:\n01/2021 to Till date", ["Years"])

    # 11. Additional Advanced Generic Tests
    assert_exp(26, "YYYY-MM format", "WORK EXPERIENCE:\n2020-01 - 2024-05", ["4.4 Years"])
    assert_exp(27, "Age Rejection", "Rahul Sharma (28 years old)\nWORK EXPERIENCE:\n2020 - 2024", ["4 Years"], ["28"])
    assert_exp(28, "Project Duration Rejection", "Project Duration: 6 months college project.\nWORK EXPERIENCE:\n2019 - 2024", ["5 Years"])
    assert_exp(29, "OCR space decimal", "Summary: Software Developer with 5 . 5 years experience.", ["5.5 Years"])
    assert_exp(30, "OCR space modifier", "Summary: Lead Architect with 5 + yrs experience.", ["5+ Years"])
    assert_exp(31, "Having 4 years of", "Summary: Having 4 years of hands-on experience in Java.", ["4 Years"])
    assert_exp(32, "Experienced with 7 years", "Experienced professional with 7 years in cloud engineering.", ["7 Years"])
    assert_exp(33, "Overall experience: 8 years", "Overall experience: 8 years", ["8 Years"])
    assert_exp(34, "Total experience - 6 years", "Total experience - 6 years", ["6 Years"])
    assert_exp(35, "Professional experience = 9 years", "Professional experience = 9 years", ["9 Years"])
    assert_exp(36, "Around 5 years", "Summary: Around 5 years of software experience.", ["5 Years"])
    assert_exp(37, "Nearly 6 years", "Summary: Nearly 6 years in backend development.", ["6 Years"])
    assert_exp(38, "More than 10 years", "Summary: More than 10 years of experience.", ["10+ Years"])
    assert_exp(39, "7 years 4 months", "Summary: Senior QA with 7 years 4 months experience.", ["7.3 Years"])
    assert_exp(40, "Unparseable History Fallback", "John Doe\nSummary: Software Engineer\nWORK EXPERIENCE:\nRole at Acme Corp", ["Not Specified"])

    print(f"\n[OK] {passed_count}/{total_tests} GENERIC EXPERIENCE ENGINE UNIT TESTS PASSED!")


def run_regression_tests():
    print("\n========================================================================")
    print("      RUNNING REGRESSION TESTS FOR BENCHMARK CANDIDATE SAMPLES          ")
    print("========================================================================\n")

    benchmark_samples = [
        ("Rahul Sharma (4 Years)", "RAHUL SHARMA\nSummary: Software Engineer with 4 years of experience.\nWORK EXPERIENCE:\n2020 - 2024", "4 Years"),
        ("Priya Reddy (2 Years)", "PRIYA REDDY\nSummary: Python Developer with 2 years experience.\nWORK EXPERIENCE:\n2022 - 2024", "2 Years"),
        ("Arjun Kumar (6 Years)", "ARJUN KUMAR\nSummary: Senior AI Engineer with 6+ years experience.\nWORK EXPERIENCE:\n2018 - 2024", "6+ Years"),
        ("Sneha Rao (3 Years)", "SNEHA RAO\nSummary: Data Engineer with 3 years of experience.\nWORK EXPERIENCE:\n2021 - 2024", "3 Years"),
        ("Vikram Singh (5 Years)", "VIKRAM SINGH\nSummary: DevOps Engineer with 5 years experience.\nWORK EXPERIENCE:\n2019 - 2024", "5 Years"),
        ("Kiran Verma (8 Years)", "KIRAN VERMA\nSummary: Full Stack Lead with 8 years of experience.\nWORK EXPERIENCE:\n2016 - 2024", "8 Years"),
        ("Ananya Patel (1 Year)", "ANANYA PATEL\nSummary: Junior Frontend Developer with 1 year experience.\nWORK EXPERIENCE:\n2023 - 2024", "1 Year"),
        ("Meera Nair (4 Years)", "MEERA NAIR\nSummary: QA Automation Engineer with 4 years experience.\nWORK EXPERIENCE:\n2020 - 2024", "4 Years"),
        ("Neha Kapoor (3 Years)", "NEHA KAPOOR\nSummary: Salesforce Consultant with 3 years experience.\nWORK EXPERIENCE:\n2021 - 2024", "3 Years"),
        ("Rohit Das (Fresher)", "ROHIT DAS\nSummary: Fresher seeking entry level developer position.\nEDUCATION:\nB.Tech 2024", "Fresher")
    ]

    reg_passed = 0
    for title, text, expected in benchmark_samples:
        res = evaluate_total_experience(text)
        if expected.lower() in res.display_str.lower():
            reg_passed += 1
            print(f"[PASS] {title}: Extracted '{res.display_str}'")
        else:
            print(f"[FAIL] {title}: Extracted '{res.display_str}', Expected '{expected}'")
            assert False, f"Regression test failed for {title}"

    print(f"\n[OK] ALL {reg_passed}/{len(benchmark_samples)} REGRESSION BENCHMARK TESTS PASSED!")


if __name__ == "__main__":
    run_experience_engine_tests()
    run_regression_tests()
