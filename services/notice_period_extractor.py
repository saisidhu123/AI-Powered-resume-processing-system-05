"""
services/notice_period_extractor.py

Production-grade, deterministic Notice Period Extraction Engine.
Extracts candidate notice period / joining availability independently before numeric extraction.
Standardizes output formats ("30 Days", "15 Days", "45 Days", "60 Days", "90 Days", "2 Months", "3 Months", "Immediate", "Negotiable", "Not Specified").
"""

import re
from typing import Optional

NOTICE_LABEL_PATTERNS = [
    r"\b(?:notice\s+period|notice|serving\s+notice\s+period|serving\s+notice|joining\s+availability|joining\s+time|earliest\s+joining|can\s+join|joining\s+in|available\s+to\s+join|availability)\b"
]

IMMEDIATE_PATTERNS = [
    r"\b(?:immediate\s+joiner|available\s+immediately|can\s+join\s+immediately|available\s+to\s+join\s+immediately|immediate|immediately|0\s*days?|zero\s*days?)\b"
]

INVALID_NOTICE_VALUES = [
    "notice", "notice period", "availability", "joining", "none", "null", "n/a", "na", "not specified", "header", "value"
]


def normalize_notice_period(val_str: str) -> str:
    """Format and normalize a notice period string."""
    if not val_str:
        return "Not Specified"

    val_clean = val_str.strip().strip("|:;-,=/ ")
    val_lower = val_clean.lower()

    if val_lower in INVALID_NOTICE_VALUES:
        return "Not Specified"

    if any(re.search(pat, val_lower) for pat in IMMEDIATE_PATTERNS):
        return "Immediate"

    if "negotiable" in val_lower:
        return "Negotiable"

    # Match numeric days e.g. "30 Days", "15-day notice", "60 days"
    m_days = re.search(r"\b(\d+)\s*\-?\s*days?\b", val_lower)
    if m_days:
        num = int(m_days.group(1))
        if num == 0:
            return "Immediate"
        return f"{num} Days"

    # Match numeric months e.g. "2 months", "1 month"
    m_months = re.search(r"\b(\d+)\s*\-?\s*months?\b", val_lower)
    if m_months:
        num = int(m_months.group(1))
        return f"{num} Month" if num == 1 else f"{num} Months"

    # Match numeric weeks e.g. "2 weeks"
    m_weeks = re.search(r"\b(\d+)\s*\-?\s*weeks?\b", val_lower)
    if m_weeks:
        num = int(m_weeks.group(1))
        return f"{num} Week" if num == 1 else f"{num} Weeks"

    # Standalone number matching when near notice label (e.g. "Notice Period: 30")
    m_num = re.search(r"\b(\d+)\b", val_clean)
    if m_num:
        num = int(m_num.group(1))
        if num in [15, 30, 45, 60, 90, 120, 180]:
            return f"{num} Days"
        elif num in [1, 2, 3, 4]:
            return f"{num} Month" if num == 1 else f"{num} Months"

    if "serving" in val_lower:
        return "Serving Notice"

    return "Not Specified"


def extract_notice_period(resume_text: str) -> str:
    """
    Context-first, deterministic Notice Period Extractor.
    Evaluated BEFORE CTC extraction to prevent notice period numbers from leaking into CTC fields.
    """
    if not resume_text or not resume_text.strip():
        return "Not Specified"

    lines = resume_text.splitlines()

    # Pass 0: Table Layout Match (e.g. Header row: "... | Notice | ...", Value row: "... | Immediate | ...")
    for i in range(len(lines) - 1):
        h_line = lines[i].strip()
        v_line = lines[i + 1].strip()

        if "|" in h_line and "|" in v_line:
            h_cols = [c.strip().lower() for c in h_line.split("|")]
            v_cols = [c.strip() for c in v_line.split("|")]

            for idx, col_hdr in enumerate(h_cols):
                if any(re.search(pat, col_hdr) for pat in NOTICE_LABEL_PATTERNS):
                    if idx < len(v_cols):
                        norm = normalize_notice_period(v_cols[idx])
                        if norm != "Not Specified":
                            return norm

    # Pass 1: Line & Multi-Line Segment-level search
    for i, line in enumerate(lines):
        line_strip = line.strip()
        if not line_strip:
            continue

        # Check if line matches Notice Period labels
        if any(re.search(pat, line_strip.lower()) for pat in NOTICE_LABEL_PATTERNS):
            # Try same line after colon/label
            m_val = re.search(r"(?:notice\s+period|notice|serving\s+notice|availability|joining\s+availability|joining\s+time|can\s+join|available\s+to\s+join)\s*[:\=\-]?\s*([^\n\,\|\;]+)", line_strip, re.IGNORECASE)
            if m_val:
                raw_val = m_val.group(1).strip()
                if raw_val.lower() not in INVALID_NOTICE_VALUES and not any(k in raw_val.lower() for k in ["ctc", "salary", "lpa", "lakh"]):
                    norm = normalize_notice_period(raw_val)
                    if norm != "Not Specified":
                        return norm

            # Multi-line lookahead: inspect next 2 lines if label has no value on same line
            for offset in range(1, 3):
                if i + offset < len(lines):
                    next_line = lines[i + offset].strip()
                    if next_line and not any(k in next_line.lower() for k in ["experience", "education", "skills", "projects", "ctc", "salary"]):
                        norm = normalize_notice_period(next_line)
                        if norm != "Not Specified":
                            return norm

    # Pass 2: Standalone immediate joiner phrase search across resume text
    if any(re.search(pat, resume_text.lower()) for pat in IMMEDIATE_PATTERNS):
        return "Immediate"

    # Pass 3: Standalone "Notice: X Days" search
    m_notice = re.search(r"\b(?:notice|availability)\s*[:\=\-]?\s*(\d+\s*(?:days?|months?|weeks?))\b", resume_text, re.IGNORECASE)
    if m_notice:
        return normalize_notice_period(m_notice.group(1))

    return "Not Specified"
