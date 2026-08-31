"""
services/section_detector.py

Generic Resume Section Detector Engine.
Categorizes text lines/blocks into canonical sections (CONTACT, SUMMARY, EXPERIENCE, EDUCATION, SKILLS, PROJECTS, CERTIFICATIONS, NOTICE_PERIOD, COMPENSATION).
Supports arbitrary semantic heading variations without requiring exact section names.
"""

import re
from typing import Dict, List, Tuple

SECTION_PATTERNS = {
    "CONTACT": [
        r"\b(?:personal\s+details|personal\s+info|contact\s+details|contact\s+info|contact|location|address)\b"
    ],
    "SUMMARY": [
        r"\b(?:professional\s+summary|executive\s+summary|summary|profile|career\s+objective|objective|about\s+me)\b"
    ],
    "EXPERIENCE": [
        r"\b(?:work\s+experience|professional\s+experience|employment\s+history|career\s+history|professional\s+journey|employment|work\s+history|career\s+timeline|internships?|experience)\b"
    ],
    "EDUCATION": [
        r"\b(?:academic\s+background|education|academic\s+qualification|academic\s+history|qualifications|academics|education\s+&\s+training)\b"
    ],
    "SKILLS": [
        r"\b(?:technical\s+skills|core\s+skills|skills|technologies|tools\s+&\s+technologies|core\s+competencies|key\s+skills|area\s+of\s+expertise)\b"
    ],
    "PROJECTS": [
        r"\b(?:key\s+projects|projects|major\s+projects|project\s+details|significant\s+projects)\b"
    ],
    "CERTIFICATIONS": [
        r"\b(?:certifications|certified|courses|licenses\s+&\s+certifications|training)\b"
    ],
    "NOTICE_PERIOD": [
        r"\b(?:notice\s+period|joining\s+availability|availability|joining\s+time|earliest\s+joining|notice)\b"
    ],
    "COMPENSATION": [
        r"\b(?:current\s+ctc|expected\s+ctc|compensation|salary|package|remuneration|ctc\s+details)\b"
    ]
}


def detect_section_heading(line: str) -> Tuple[bool, str]:
    """
    Determines if a line acts as a section heading and returns the canonical section name.
    """
    line_clean = line.strip()
    if not line_clean or len(line_clean) > 60:
        return False, "UNKNOWN"

    line_lower = line_clean.lower()
    
    # Check if line looks like a header (short, ended with colon, uppercase, or standalone)
    is_header_format = len(line_clean) <= 40 or line_clean.isupper() or line_clean.endswith(":")

    if not is_header_format:
        return False, "UNKNOWN"

    for sec_name, patterns in SECTION_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, line_lower):
                return True, sec_name

    return False, "UNKNOWN"


def segment_resume_sections(resume_text: str) -> Dict[str, str]:
    """
    Segments a resume document into canonical section text blocks.
    Returns dict mapping section names to text content.
    """
    if not resume_text:
        return {}

    lines = resume_text.splitlines()
    sections = {}
    current_sec = "HEADER"
    current_lines = []

    for line in lines:
        line_strip = line.strip()
        if not line_strip:
            continue

        is_sec, sec_name = detect_section_heading(line_strip)
        if is_sec:
            if current_lines:
                sections[current_sec] = "\n".join(current_lines).strip()
            current_sec = sec_name
            current_lines = [line_strip]
        else:
            current_lines.append(line_strip)

    if current_lines:
        sections[current_sec] = "\n".join(current_lines).strip()

    return sections
