"""
services/ctc_extractor.py

Production-grade, deterministic CTC Extraction Engine.
Extracts Current CTC and Expected CTC independently with explicit non-disclosure protection.
Guarantees that Expected CTC is NEVER used as fallback for Current CTC, and Notice Period numbers NEVER leak into CTC.
"""

import re
from typing import Tuple, Dict, Any, List, Optional

SALARY_UNITS_PATTERN = r"(?:LPA|Lakhs?|Lacs?|L|[kK]|Crores?|Cr|Per\s+Annum|P\.?A\.?|Per\s+Month|Monthly|p\.?m\.?|Lakhs?\s+Per\s+Annum)"
CURRENCY_SYMBOLS_PATTERN = r"(?:₹|Rs\.?|INR|\$|USD)"

EXPLICIT_SALARY_VALUE_PATTERN = r"(?:" + CURRENCY_SYMBOLS_PATTERN + r"\s*\d+(?:[\.,]\d+)?(?:\s*" + SALARY_UNITS_PATTERN + r")?|\d+(?:[\.,]\d+)?\s*" + SALARY_UNITS_PATTERN + r")"
LABELLED_SALARY_VALUE_PATTERN = r"(?:" + CURRENCY_SYMBOLS_PATTERN + r"\s*)?\d+(?:[\.,]\d+)?(?:\s*" + SALARY_UNITS_PATTERN + r")?"

CURRENT_LABEL_PATTERNS = [
    r"\b(?:current|present|existing|fixed|presently\s+drawing|currently\s+drawing)\s*(?:ctc|c\.t\.c\.?|salary|compensation|package|remuneration|gross|pay|earnings|fixed)?\b",
    r"\b(?<!past\s)(?<!previous\s)(?<!prior\s)(?<!old\s)(?<!expected\s)(?<!desired\s)(?<!target\s)ctc\b(?!\s*(?:expected|desired|target|looking|expecting))"
]

EXPECTED_LABEL_PATTERNS = [
    r"\b(?:expected|desired|target|expecting|looking\s+for|salary\s+expectation|compensation\s+expectation)\s*(?:ctc|c\.t\.c\.?|salary|compensation|package|remuneration)?\b",
    r"\blooking\s+for\b",
    r"\bexpecting\b"
]

NOTICE_PERIOD_KEYWORDS = [
    "notice", "day", "days", "joining", "availability", "serving", "immediate", "month", "months", "week", "weeks"
]

NON_CTC_CONTEXT_KEYWORDS = [
    "notice", "day", "days", "joining", "availability", "serving", "immediate",
    "experience", "exp", "years", "yrs", "year", "age", "graduated", "passed",
    "mobile", "phone", "contact", "@", "linkedin", "version", "project",
    "past ctc", "previous ctc", "prior ctc", "old ctc", "past salary", "previous salary"
]

NON_DISCLOSURE_KEYWORDS = [
    "not specified", "not disclosed", "not mentioned", "not provided", "n/a", "na", "nil", "none", "undisclosed", "as per company norms"
]


def clean_and_validate_ctc(val_str: str, source_segment: str = "", is_explicit_label: bool = False) -> str:
    """
    Validates and cleans an extracted CTC string.
    Rejects notice period numbers, experience numbers, dates, phone numbers, and bare numbers without context.
    """
    if not val_str:
        return ""

    val_clean = val_str.strip().strip("|:;-,=/ ")
    # Repair font OCR artifacts e.g. "I8 LPA" -> "₹8 LPA"
    val_clean = re.sub(r"\bI(\d+(?:\.\d+)?\s*(?:LPA|Lakhs?|Lacs?|L|k|K|Crores?|Cr))\b", r"₹\1", val_clean, flags=re.IGNORECASE)
    val_lower = val_clean.lower()
    seg_lower = source_segment.lower() if source_segment else val_lower

    # Check for explicit non-disclosure
    if any(k in val_lower for k in NON_DISCLOSURE_KEYWORDS):
        return "Not specified"

    # 1. Hard Exclusion: Notice period, experience, dates, phone, age
    if any(k in val_lower for k in NOTICE_PERIOD_KEYWORDS) or any(k in seg_lower for k in ["notice period", "days notice", "day notice", "days to join"]):
        return ""

    if any(k in val_lower for k in ["year", "yrs", "month", "fresher", "@", "linkedin"]):
        return ""

    # Reject 4-digit year numbers (e.g. 2021, 2024, 2020)
    if re.fullmatch(r"(?:19\d\d|20\d\d)", val_clean):
        return ""

    # 2. Extract digits
    digits = re.findall(r"\d+(?:[\.,]\d+)?", val_clean)
    if not digits:
        return ""

    num_val = float(digits[0].replace(",", ""))

    # 3. Context Validation: Reject notice period numbers (15, 30, 45, 60, 90) if segment contains notice/day context
    if num_val in [15.0, 30.0, 45.0, 60.0, 90.0, 180.0] and any(k in seg_lower for k in NOTICE_PERIOD_KEYWORDS):
        return ""

    # 4. Strict Unit / Currency Validation
    has_unit = bool(re.search(SALARY_UNITS_PATTERN, val_clean, re.IGNORECASE))
    has_currency = bool(re.search(CURRENCY_SYMBOLS_PATTERN, val_clean, re.IGNORECASE))

    # If NOT directly preceded by an explicit CTC label, value MUST have a currency symbol or salary unit
    if not is_explicit_label and not (has_unit or has_currency):
        return ""

    return val_clean


def extract_ctc_from_segment(segment: str) -> Tuple[str, str]:
    """
    Parses a single segment/line for Current CTC and Expected CTC using context-first rules.
    """
    if not segment:
        return ("", "")

    seg_strip = segment.strip()
    seg_lower = seg_strip.lower()

    # Reject segment if it is strictly Notice Period or Experience
    if ("notice" in seg_lower or "availability" in seg_lower) and not ("ctc" in seg_lower or "salary" in seg_lower or "package" in seg_lower):
        return ("", "")

    curr_val = ""
    exp_val = ""

    has_curr = any(re.search(pat, seg_lower) for pat in CURRENT_LABEL_PATTERNS)
    has_exp = any(re.search(pat, seg_lower) for pat in EXPECTED_LABEL_PATTERNS)

    if has_curr and has_exp:
        exp_match = None
        for pat in EXPECTED_LABEL_PATTERNS:
            m = re.search(pat, seg_lower)
            if m:
                exp_match = m
                break

        if exp_match:
            split_idx = exp_match.start()
            curr_part = seg_strip[:split_idx]
            exp_part = seg_strip[split_idx:]

            # Check for non-disclosure in curr_part
            if any(k in curr_part.lower() for k in NON_DISCLOSURE_KEYWORDS):
                curr_val = "Not specified"
            else:
                curr_label_m = None
                for pat in CURRENT_LABEL_PATTERNS:
                    m_l = re.search(pat, curr_part, re.IGNORECASE)
                    if m_l:
                        curr_label_m = m_l
                        break
                curr_target = curr_part[curr_label_m.start():] if curr_label_m else curr_part
                m_curr = re.search(LABELLED_SALARY_VALUE_PATTERN, curr_target, re.IGNORECASE)
                if m_curr:
                    curr_val = clean_and_validate_ctc(m_curr.group(0), curr_target, is_explicit_label=True)

            # Check for non-disclosure in exp_part
            if any(k in exp_part.lower() for k in NON_DISCLOSURE_KEYWORDS):
                exp_val = "Not specified"
            else:
                exp_label_m = None
                for pat in EXPECTED_LABEL_PATTERNS:
                    m_l = re.search(pat, exp_part, re.IGNORECASE)
                    if m_l:
                        exp_label_m = m_l
                        break
                exp_target = exp_part[exp_label_m.start():] if exp_label_m else exp_part
                m_exp = re.search(LABELLED_SALARY_VALUE_PATTERN, exp_target, re.IGNORECASE)
                if m_exp:
                    exp_val = clean_and_validate_ctc(m_exp.group(0), exp_target, is_explicit_label=True)

            return (curr_val, exp_val)

    elif has_curr:
        if any(k in seg_lower for k in NON_DISCLOSURE_KEYWORDS):
            curr_val = "Not specified"
        else:
            curr_label_m = None
            for pat in CURRENT_LABEL_PATTERNS:
                m_l = re.search(pat, seg_strip, re.IGNORECASE)
                if m_l:
                    curr_label_m = m_l
                    break
            curr_target = seg_strip[curr_label_m.start():] if curr_label_m else seg_strip
            m = re.search(LABELLED_SALARY_VALUE_PATTERN, curr_target, re.IGNORECASE)
            if m:
                curr_val = clean_and_validate_ctc(m.group(0), curr_target, is_explicit_label=True)
        return (curr_val, "")

    elif has_exp:
        if any(k in seg_lower for k in NON_DISCLOSURE_KEYWORDS):
            exp_val = "Not specified"
        else:
            exp_label_m = None
            for pat in EXPECTED_LABEL_PATTERNS:
                m_l = re.search(pat, seg_strip, re.IGNORECASE)
                if m_l:
                    exp_label_m = m_l
                    break
            exp_target = seg_strip[exp_label_m.start():] if exp_label_m else seg_strip
            m = re.search(LABELLED_SALARY_VALUE_PATTERN, exp_target, re.IGNORECASE)
            if m:
                exp_val = clean_and_validate_ctc(m.group(0), exp_target, is_explicit_label=True)
        return ("", exp_val)

    # Standalone explicit salary value without direct label on line (only if line has no non-CTC context)
    if not any(k in seg_lower for k in NON_CTC_CONTEXT_KEYWORDS):
        m_exp_val = re.search(EXPLICIT_SALARY_VALUE_PATTERN, seg_strip, re.IGNORECASE)
        if m_exp_val:
            val = clean_and_validate_ctc(m_exp_val.group(0), seg_strip, is_explicit_label=False)
            return (val, "")

    return ("", "")


def extract_current_and_expected_ctc(resume_text: str) -> Tuple[str, str]:
    """
    Context-aware, production-grade extraction of Current CTC and Expected CTC from resume text.
    Returns ("Not specified", "Not specified") when no reliable CTC exists.
    """
    if not resume_text or not resume_text.strip():
        return ("Not specified", "Not specified")

    lines = resume_text.splitlines()
    final_curr = ""
    final_exp = ""

    # Pass 1: Line & Segment Parsing
    skip_indices = set()
    for i, line in enumerate(lines):
        if i in skip_indices:
            continue
        line_strip = line.strip()
        if not line_strip:
            continue

        target_line = line_strip
        # Multi-line lookahead when label is on line N and value is on line N+1
        if i + 1 < len(lines):
            next_l = lines[i + 1].strip()
            if (any(k in line_strip.lower() for k in ["current", "present", "expected", "desired", "target", "ctc", "salary"]) and
                not re.search(LABELLED_SALARY_VALUE_PATTERN, line_strip, re.IGNORECASE) and
                (re.search(EXPLICIT_SALARY_VALUE_PATTERN, next_l, re.IGNORECASE) or any(k in next_l.lower() for k in NON_DISCLOSURE_KEYWORDS))):
                target_line = line_strip + " " + next_l
                skip_indices.add(i + 1)

        # Split line by pipe '|', semicolon ';', or ' - ' to isolate segments
        segments = [s.strip() for s in re.split(r"[\|;\n]", target_line) if s.strip()]
        for seg in segments:
            c_val, e_val = extract_ctc_from_segment(seg)
            if c_val and c_val != "Not specified":
                if not final_curr or final_curr == "Not specified":
                    final_curr = c_val
                elif not final_exp or final_exp == "Not specified":
                    if c_val != final_curr:
                        final_exp = c_val
            elif c_val == "Not specified" and not final_curr:
                final_curr = c_val

            if e_val and e_val != "Not specified":
                if not final_exp or final_exp == "Not specified":
                    final_exp = e_val
            elif e_val == "Not specified" and not final_exp:
                final_exp = e_val

        if final_curr and final_exp and final_curr != "Not specified" and final_exp != "Not specified":
            break

    # Pass 2: Table Layout Inspection (e.g. Header row: "Current CTC | Expected CTC", Value row: "8 LPA | 11 LPA")
    if not (final_curr and final_exp and final_curr != "Not specified" and final_exp != "Not specified"):
        for i in range(len(lines) - 1):
            header_line = lines[i].lower()
            val_line = lines[i + 1].strip()

            if "|" in header_line and "|" in val_line:
                h_cols = [c.strip().lower() for c in lines[i].split("|")]
                v_cols = [c.strip() for c in lines[i + 1].split("|")]
                for col_idx, col_hdr in enumerate(h_cols):
                    if col_idx < len(v_cols):
                        cell_val = v_cols[col_idx]
                        if any(k in col_hdr for k in ["current ctc", "present ctc", "current salary", "present salary", "fixed ctc", "current package", "present package", "current"]):
                            if not final_curr or final_curr == "Not specified":
                                final_curr = clean_and_validate_ctc(cell_val, cell_val, is_explicit_label=True)
                        elif any(k in col_hdr for k in ["expected ctc", "exp ctc", "expected salary", "target ctc", "desired ctc", "desired salary", "expected package", "target package", "expected"]):
                            if not final_exp or final_exp == "Not specified":
                                final_exp = clean_and_validate_ctc(cell_val, cell_val, is_explicit_label=True)

            elif ("current" in header_line or "present" in header_line) and \
                 ("expected" in header_line or "desired" in header_line or "looking" in header_line):
                salaries = re.findall(EXPLICIT_SALARY_VALUE_PATTERN, val_line, re.IGNORECASE)
                if len(salaries) >= 2:
                    final_curr = clean_and_validate_ctc(salaries[0], val_line, is_explicit_label=True)
                    final_exp = clean_and_validate_ctc(salaries[1], val_line, is_explicit_label=True)

    # Pass 3: Strict Regex Label Fallback
    if not final_curr:
        m_curr = re.search(r"(?:current|present|existing)\s*(?:ctc|salary|package|compensation)\s*[:\=\-]?\s*([^\r\n\,\|\;]+)", resume_text, re.IGNORECASE)
        if m_curr:
            raw_curr = m_curr.group(1).strip()
            final_curr = clean_and_validate_ctc(raw_curr, m_curr.group(0), is_explicit_label=True)

    if not final_exp:
        m_exp = re.search(r"(?:expected|desired|target)\s*(?:ctc|salary|package|compensation)\s*[:\=\-]?\s*([^\r\n\,\|\;]+)", resume_text, re.IGNORECASE)
        if m_exp:
            raw_exp = m_exp.group(1).strip()
            final_exp = clean_and_validate_ctc(raw_exp, m_exp.group(0), is_explicit_label=True)

    # Final Output Formatting: Default to "Not specified" if blank
    out_curr = final_curr if final_curr else "Not specified"
    out_exp = final_exp if final_exp else "Not specified"

    return (out_curr, out_exp)


def sanitize_ctc_pair(current_ctc: str, expected_ctc: str, resume_text: str = "") -> Tuple[str, str]:
    """
    Final sanitization and cross-validation layer.
    Ensures Current CTC and Expected CTC are strictly independent.
    Strips out Expected CTC keywords/values from Current CTC and Notice Period contamination.
    """
    clean_curr = str(current_ctc or "").strip()
    clean_exp = str(expected_ctc or "").strip()

    # Normalize explicit non-disclosure strings
    if any(clean_curr.lower() == k for k in ["not specified", "not disclosed", "not mentioned", "not provided", "n/a", "na", "nil", "none", ""]):
        clean_curr = "Not specified"

    if any(clean_exp.lower() == k for k in ["not specified", "not disclosed", "not mentioned", "not provided", "n/a", "na", "nil", "none", ""]):
        clean_exp = "Not specified"

    # Reject Notice Period strings e.g. "30 Days", "15", "60"
    if clean_curr.lower() in ["30", "15", "45", "60", "90", "180"] or any(k in clean_curr.lower() for k in NOTICE_PERIOD_KEYWORDS):
        clean_curr = "Not specified"

    if clean_exp.lower() in ["30", "15", "45", "60", "90", "180"] or any(k in clean_exp.lower() for k in NOTICE_PERIOD_KEYWORDS):
        clean_exp = "Not specified"

    # Re-extract deterministically from resume_text if contamination detected
    exp_indicators = ["expected", "desired", "target", "expecting", "looking for", "salary expectation"]
    curr_indicators = ["current", "present", "existing"]

    curr_has_exp = any(k in clean_curr.lower() for k in exp_indicators)
    exp_has_curr = any(k in clean_exp.lower() for k in curr_indicators)

    if curr_has_exp or exp_has_curr or (clean_curr.lower() == clean_exp.lower() and clean_curr.lower() != "not specified"):
        if resume_text:
            det_curr, det_exp = extract_current_and_expected_ctc(resume_text)
            clean_curr = det_curr
            clean_exp = det_exp
        else:
            if curr_has_exp:
                clean_curr = "Not specified"
            if exp_has_curr:
                clean_exp = "Not specified"

    out_curr = clean_curr if clean_curr else "Not specified"
    out_exp = clean_exp if clean_exp else "Not specified"

    return (out_curr, out_exp)
