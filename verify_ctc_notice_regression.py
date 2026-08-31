"""
verify_ctc_notice_regression.py

Comprehensive 30+ Test Regression Suite for Notice Period & CTC Extraction Pipeline.
Verifies Notice Period extraction, strict CTC independence, explicit non-disclosure handling,
and invalid value protection.
"""

import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from services.notice_period_extractor import extract_notice_period
from services.ctc_extractor import extract_current_and_expected_ctc, sanitize_ctc_pair
from services.field_extractor import extract_all_fields_fallback

def run_30_ctc_notice_tests():
    print("\n========================================================================")
    print("   RUNNING 30+ NOTICE PERIOD & CTC PIPELINE REGRESSION TEST SUITE       ")
    print("========================================================================\n")

    passed_count = 0
    total_tests = 0

    def assert_case(test_id: int, title: str, text: str, exp_curr: str, exp_exp: str, exp_notice: str):
        nonlocal passed_count, total_tests
        total_tests += 1

        fields = extract_all_fields_fallback(text)
        got_curr = fields.get("Current CTC", "Not specified")
        got_exp = fields.get("Expected CTC", "Not specified")
        got_notice = fields.get("Notice Period", "Not Specified")

        ok_curr = (got_curr.lower() == exp_curr.lower()) or (exp_curr.lower() in got_curr.lower() and exp_curr.lower() != "not specified")
        ok_exp = (got_exp.lower() == exp_exp.lower()) or (exp_exp.lower() in got_exp.lower() and exp_exp.lower() != "not specified")
        ok_notice = (got_notice.lower() == exp_notice.lower()) or (exp_notice.lower() in got_notice.lower() and exp_notice.lower() != "not specified")

        # Hard Exclusion Assertions
        if got_curr.strip() in ["30", "15", "45", "60", "90"]:
            ok_curr = False
        if got_curr.lower() == got_exp.lower() and got_curr.lower() != "not specified":
            # If both are same, must be explicitly mentioned in text
            if "same" not in text.lower():
                ok_curr = False

        if ok_curr and ok_exp and ok_notice:
            passed_count += 1
            print(f"[PASS] Test {test_id:02d} ({title}): Current='{got_curr}', Expected='{got_exp}', Notice='{got_notice}'")
        else:
            print(f"[FAIL] Test {test_id:02d} ({title}):")
            print(f"       Got:      Current='{got_curr}', Expected='{got_exp}', Notice='{got_notice}'")
            print(f"       Expected: Current='{exp_curr}', Expected='{exp_exp}', Notice='{exp_notice}'")
            assert False, f"Test {test_id} Failed!"

    # 1. Current CTC + Expected CTC same line
    assert_case(1, "Current + Expected CTC same line", "Current CTC: 8 LPA | Expected CTC: 12 LPA", "8 LPA", "12 LPA", "Not Specified")

    # 2. Current CTC + Expected CTC separate lines
    assert_case(2, "Current + Expected CTC separate lines", "Current CTC: 8 LPA\nExpected CTC: 12 LPA", "8 LPA", "12 LPA", "Not Specified")

    # 3. Current CTC Not Specified + Expected CTC present
    assert_case(3, "Current CTC Not Specified + Expected CTC present", "Current CTC: Not Specified\nExpected CTC: 15 LPA", "Not specified", "15 LPA", "Not Specified")

    # 4. Current CTC N/A + Expected CTC present
    assert_case(4, "Current CTC N/A + Expected CTC present", "Current CTC: N/A\nExpected CTC: 15 LPA", "Not specified", "15 LPA", "Not Specified")

    # 5. Current CTC Not disclosed + Expected CTC present
    assert_case(5, "Current Salary Not disclosed + Expected Salary present", "Current Salary: Not disclosed\nExpected Salary: 18 LPA", "Not specified", "18 LPA", "Not Specified")

    # 6. Expected CTC only
    assert_case(6, "Expected CTC only", "Expected CTC: ₹15 LPA", "Not specified", "₹15 LPA", "Not Specified")

    # 7. Current CTC only
    assert_case(7, "Current CTC only", "Current CTC: ₹7.5 LPA", "₹7.5 LPA", "Not specified", "Not Specified")

    # 8. Notice Period 30 Days
    assert_case(8, "Notice Period 30 Days", "Notice Period: 30 Days", "Not specified", "Not specified", "30 Days")

    # 9. Notice Period 45 Days
    assert_case(9, "Notice Period 45 Days", "Notice Period: 45 Days", "Not specified", "Not specified", "45 Days")

    # 10. Notice Period 60 Days
    assert_case(10, "Notice Period 60 Days", "Notice Period: 60 Days", "Not specified", "Not specified", "60 Days")

    # 11. Notice Period Immediate
    assert_case(11, "Available to Join: Immediate", "Available to Join: Immediate", "Not specified", "Not specified", "Immediate")

    # 12. Notice Period 2 months
    assert_case(12, "Notice Period 2 months", "Notice Period: 2 months", "Not specified", "Not specified", "2 Months")

    # 13. Notice Period 3 months
    assert_case(13, "Serving Notice Period: 3 months", "Serving Notice Period: 3 months", "Not specified", "Not specified", "3 Months")

    # 14. Notice Period + Current CTC same line
    assert_case(14, "Notice Period + Current CTC same line", "Notice Period: 30 Days | Current CTC: 8 LPA", "8 LPA", "Not specified", "30 Days")

    # 15. Notice Period + Expected CTC same line
    assert_case(15, "Notice Period + Expected CTC same line", "Notice Period: 60 Days | Expected CTC: 15 LPA", "Not specified", "15 LPA", "60 Days")

    # 16. Current CTC + Expected CTC + Notice Period same line
    assert_case(16, "Current + Expected + Notice same line", "Notice Period: 15 Days | Current CTC: 6 LPA | Expected CTC: 8 LPA", "6 LPA", "8 LPA", "15 Days")

    # 17. Table-format CTC
    assert_case(17, "Table-format CTC", "Current CTC    Expected CTC\n8 LPA          12 LPA", "8 LPA", "12 LPA", "Not Specified")

    # 18. Pipe-separated CTC
    assert_case(18, "Pipe-separated CTC", "Current CTC: 13 LPA | Expected CTC: 17 LPA", "13 LPA", "17 LPA", "Not Specified")

    # 19. Comma-separated CTC
    assert_case(19, "Comma-separated CTC", "Current Salary: 8 LPA, Expected Salary: 12 LPA", "8 LPA", "12 LPA", "Not Specified")

    # 20. Colon-separated CTC
    assert_case(20, "Colon-separated CTC", "Present Package: 18 LPA", "18 LPA", "Not specified", "Not Specified")

    # 21. Currency ₹
    assert_case(21, "Currency ₹", "Current CTC: ₹18 LPA", "₹18 LPA", "Not specified", "Not Specified")

    # 22. INR
    assert_case(22, "Currency INR", "Current CTC: INR 10 LPA", "INR 10 LPA", "Not specified", "Not Specified")

    # 23. LPA
    assert_case(23, "Unit LPA", "Expected CTC: 12 LPA", "Not specified", "12 LPA", "Not Specified")

    # 24. Lakhs
    assert_case(24, "Unit Lakhs", "Current Salary: 8 Lakhs", "8 Lakhs", "Not specified", "Not Specified")

    # 25. Current CTC missing
    assert_case(25, "Current CTC missing", "Expected Salary: ₹20 LPA\nNotice Period: Immediate", "Not specified", "₹20 LPA", "Immediate")

    # 26. Expected CTC missing
    assert_case(26, "Expected CTC missing", "Current CTC: 8 LPA\nNotice Period: 30 Days", "8 LPA", "Not specified", "30 Days")

    # 27. Notice Period missing
    assert_case(27, "Notice Period missing", "Current CTC: 8 LPA\nExpected CTC: 12 LPA", "8 LPA", "12 LPA", "Not Specified")

    # 28. Phone number must not become CTC
    assert_case(28, "Phone number must not become CTC", "Mobile: 9876543210\nNotice Period: 30 Days", "Not specified", "Not specified", "30 Days")

    # 29. Notice period 30 days must not become CTC
    assert_case(29, "30 Days must not become CTC", "Notice Period: 30 Days\nNo CTC info", "Not specified", "Not specified", "30 Days")

    # 30. Expected CTC must never populate Current CTC
    assert_case(30, "Expected CTC must never populate Current CTC", "Current CTC: Not Provided\nExpected CTC: 15 LPA", "Not specified", "15 LPA", "Not Specified")

    # 31. Additional test: 15-day notice format
    assert_case(31, "15-day notice format", "Notice Period: 15-day notice", "Not specified", "Not specified", "15 Days")

    # 32. Additional test: Can Join Immediately
    assert_case(32, "Can Join Immediately", "Can Join: Immediately", "Not specified", "Not specified", "Immediate")

    print(f"\n[OK] ALL {passed_count}/{total_tests} REGRESSION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_30_ctc_notice_tests()
