"""
verify_ctc_experience_regression.py

Regression Test Suite for CTC Extraction & Notice Period Hard Exclusion Layer.
Proves that Notice Period numbers (15, 30, 45, 60) can NEVER populate Current CTC or Expected CTC,
and verifies strict context-first salary extraction across all required formats.
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.ctc_extractor import extract_current_and_expected_ctc, sanitize_ctc_pair
from services.experience_engine import evaluate_total_experience
from services.field_extractor import extract_ctc, extract_notice_period

def run_ctc_and_experience_regression_tests():
    print("\n========================================================================")
    print("   RUNNING CTC SEPARATION & NOTICE PERIOD HARD EXCLUSION REGRESSION SUITE   ")
    print("========================================================================\n")

    passed_count = 0
    total_tests = 0

    def assert_ctc(test_id: int, name: str, text: str, exp_curr: str, exp_exp: str):
        nonlocal passed_count, total_tests
        total_tests += 1
        
        c_val, e_val = extract_current_and_expected_ctc(text)
        c_san, e_san = sanitize_ctc_pair(c_val, e_val, text)

        ok_curr = (exp_curr.lower() in c_san.lower()) if exp_curr and exp_curr.lower() != "not specified" else (c_san.lower() == "not specified" or c_san == "")
        ok_exp = (exp_exp.lower() in e_san.lower()) if exp_exp and exp_exp.lower() != "not specified" else (e_san.lower() == "not specified" or e_san == "")

        # Strict Rejection Check: 30, 15, 45, 60 must NEVER be Current CTC
        if c_san.strip() in ["30", "15", "45", "60", "90"]:
            ok_curr = False

        if ok_curr and ok_exp:
            passed_count += 1
            print(f"[PASS] Test {test_id:02d} ({name}): Current='{c_san}', Expected='{e_san}'")
        else:
            print(f"[FAIL] Test {test_id:02d} ({name}): Got Current='{c_san}', Expected='{e_san}' | Expected: Current='{exp_curr}', Expected='{exp_exp}'")
            assert False, f"Test {test_id} Failed!"

    def assert_exp(test_id: int, name: str, text: str, expected_exp: str):
        nonlocal passed_count, total_tests
        total_tests += 1

        res = evaluate_total_experience(text)
        disp = res.display_str

        ok = expected_exp.lower() in disp.lower()
        if ok:
            passed_count += 1
            print(f"[PASS] Test {test_id:02d} ({name}): Experience='{disp}' (Source: {res.source})")
        else:
            print(f"[FAIL] Test {test_id:02d} ({name}): Got Experience='{disp}', Expected='{expected_exp}'")
            assert False, f"Test {test_id} Failed!"

    # ------------------ REQUIRED USER TEST CASES 1 - 11 ------------------
    # Test 1
    t1 = "Notice Period: 30 Days\nCurrent CTC: 8 LPA\nExpected CTC: 11 LPA"
    assert_ctc(1, "Notice + Pipe CTC (8 / 11 LPA)", t1, "8 LPA", "11 LPA")

    # Test 2
    t2 = "Notice Period: 15 Days\nCurrent Salary: 6 LPA\nExpected Salary: 8 LPA"
    assert_ctc(2, "Notice 15 Days + CTC (6 / 8 LPA)", t2, "6 LPA", "8 LPA")

    # Test 3
    t3 = "Notice Period: 60 Days\nCurrent CTC: 15 LPA\nExpected CTC: 20 LPA"
    assert_ctc(3, "Notice 60 Days + CTC (15 / 20 LPA)", t3, "15 LPA", "20 LPA")

    # Test 4
    t4 = "Notice Period: 45 Days\nCurrent CTC: 13 LPA\nExpected CTC: 17 LPA"
    assert_ctc(4, "Notice 45 Days + CTC (13 / 17 LPA)", t4, "13 LPA", "17 LPA")

    # Test 5
    t5 = "Notice Period: 30 Days\nCurrent CTC: ₹8 LPA\nExpected CTC: ₹12 LPA"
    assert_ctc(5, "Currency ₹8 LPA / ₹12 LPA", t5, "₹8 LPA", "₹12 LPA")

    # Test 6 (NO CTC -> Must be "Not specified", NEVER 60)
    t6 = "Notice Period: 60 Days\nNo CTC information anywhere"
    assert_ctc(6, "No CTC (Notice 60 Days only)", t6, "Not specified", "Not specified")

    # Test 7 (Experience + Notice Period, NO CTC -> Must be "Not specified", NEVER 5 or 30)
    t7 = "Experience: 5 Years\nNotice Period: 30 Days\nNo CTC information"
    assert_ctc(7, "No CTC (Exp 5 Yrs + Notice 30 Days)", t7, "Not specified", "Not specified")
    assert_exp(8, "Exp 5 Yrs Check", t7, "5 Years")

    # Test 8
    t8 = "Current CTC: ₹18 LPA\nExpected CTC: ₹23 LPA"
    assert_ctc(9, "Currency ₹18 LPA / ₹23 LPA", t8, "₹18 LPA", "₹23 LPA")

    # Test 9
    t9 = "Current CTC: ₹4.5 LPA\nExpected CTC: ₹6 LPA"
    assert_ctc(10, "Decimal ₹4.5 LPA / ₹6 LPA", t9, "₹4.5 LPA", "₹6 LPA")

    # Test 10
    t10 = "Expected CTC: ₹15 LPA\nNo Current CTC"
    assert_ctc(11, "Standalone Expected CTC ₹15 LPA", t10, "Not specified", "₹15 LPA")

    # Test 11
    t11 = "Current CTC: ₹7.5 LPA\nNo Expected CTC"
    assert_ctc(12, "Standalone Current CTC ₹7.5 LPA", t11, "₹7.5 LPA", "Not specified")

    # ------------------ SPECIFIC URGENT BUG EXCLUSION TESTS ------------------
    assert_ctc(13, "Notice Period: 30 Days", "Notice Period: 30 Days", "Not specified", "Not specified")
    assert_ctc(14, "Notice Period: 15 Days | Current", "Notice Period: 15 Days | Current", "Not specified", "Not specified")
    assert_ctc(15, "Notice Period: 60", "Notice Period: 60", "Not specified", "Not specified")
    assert_ctc(16, "Notice Period: 45 Days | Current", "Notice Period: 45 Days | Current", "Not specified", "Not specified")

    # ------------------ FRESHER & FORMATTING TESTS ------------------
    assert_exp(17, "Explicit Fresher", "Fresher", "Fresher")
    assert_exp(18, "Fresh Graduate Statement", "Fresh graduate with no professional experience", "Fresher")
    assert_exp(19, "Software Engineer | 2020 - 2024", "Software Engineer | 2020 - 2024", "4 Years")

    print(f"\n[OK] ALL {passed_count}/{total_tests} REGRESSION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_ctc_and_experience_regression_tests()
