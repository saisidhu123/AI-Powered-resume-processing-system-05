"""
services/number_classifier.py

Number Context Classifier & Multi-Line Context Windowing Engine.
Inspects context windows (previous 3-5 lines, current line, next 3-5 lines) for numeric tokens.
Classifies numbers into PHONE, GRADUATION_YEAR, SOFTWARE_VERSION, EXPERIENCE_YEARS, NOTICE_DAYS, or SALARY_CTC.
Prevents phone numbers, dates, version numbers, and notice days from being assigned as CTC or Experience.
"""

import re
from typing import Dict, List, Tuple, Any, Optional

NUMBER_CATEGORY_PATTERNS = {
    "PHONE": r"(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}|\b\d{10}\b|\b91-\d{10}\b",
    "GRADUATION_YEAR": r"\b(?:19\d\d|20\d\d)\b",
    "SOFTWARE_VERSION": r"\b(?:java|python|html|css|angular|react|spring|oracle|spark|hadoop)\s*v?(\d+(?:\.\d+)?)\b",
    "NOTICE_DAYS": r"\b(\d+)\s*\-?\s*(?:days?|months?|weeks?|day|month)\b",
    "EXPERIENCE_YEARS": r"\b(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?|months?|mos?)\s*(?:of\s+)?(?:experience|exp)?\b",
    "SALARY_CTC": r"(?:₹|Rs\.?|INR|\$|USD)\s*\d+(?:[\.,]\d+)?|\b\d+(?:[\.,]\d+)?\s*(?:LPA|Lakhs?|Lacs?|L|Crores?|Cr|Per\s+Annum|PA)\b"
}


def get_context_window(lines: List[str], target_index: int, window_size: int = 4) -> List[str]:
    """
    Retrieves surrounding N lines before and after target line index.
    """
    start_idx = max(0, target_index - window_size)
    end_idx = min(len(lines), target_index + window_size + 1)
    return lines[start_idx:end_idx]


def classify_number_context(num_str: str, context_text: str) -> str:
    """
    Determines the semantic category of a number string within its context window.
    """
    if not num_str:
        return "UNKNOWN"

    ctx_lower = context_text.lower()
    num_clean = num_str.strip()

    # 1. Phone number check (10+ digits)
    if re.search(NUMBER_CATEGORY_PATTERNS["PHONE"], num_clean) or len(re.sub(r"\D", "", num_clean)) >= 10:
        return "PHONE"

    # 2. Software version check e.g. "Java 8", "Python 3.10"
    if re.search(NUMBER_CATEGORY_PATTERNS["SOFTWARE_VERSION"], ctx_lower):
        return "SOFTWARE_VERSION"

    # 3. Graduation year / Employment year check (1990 - 2026)
    if re.fullmatch(r"(?:19\d\d|20\d\d)", num_clean):
        if any(k in ctx_lower for k in ["passed", "graduated", "batch", "class", "year", "education", "b.tech", "degree"]):
            return "GRADUATION_YEAR"

    # 4. Notice Period days check
    if any(k in ctx_lower for k in ["notice", "days", "joining", "availability"]):
        if num_clean in ["15", "30", "45", "60", "90", "120", "180"]:
            return "NOTICE_DAYS"

    # 5. Salary / CTC check
    if any(k in ctx_lower for k in ["ctc", "salary", "package", "lpa", "lakh", "lac", "inr", "₹", "$"]):
        return "SALARY_CTC"

    # 6. Experience years check
    if any(k in ctx_lower for k in ["experience", "exp", "years", "yrs"]):
        return "EXPERIENCE_YEARS"

    return "UNKNOWN"


def find_multi_line_value(lines: List[str], label_patterns: List[str], max_lookahead: int = 4) -> Tuple[bool, str, int]:
    """
    Searches for a field value that appears on lines following a header label (multi-line layout).
    e.g.
    Current CTC
    8 LPA
    or
    Notice Period:
    30 Days
    """
    for idx, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(re.search(pat, line_lower) for pat in label_patterns):
            # Check same line first
            colon_split = line.split(":", 1)
            if len(colon_split) > 1 and colon_split[1].strip():
                return True, colon_split[1].strip(), idx

            # Look ahead N lines
            for offset in range(1, max_lookahead + 1):
                if idx + offset < len(lines):
                    next_line = lines[idx + offset].strip()
                    if next_line and not any(k in next_line.lower() for k in ["experience", "education", "skills", "projects", "ctc", "salary"]):
                        return True, next_line, idx + offset

    return False, "", -1
