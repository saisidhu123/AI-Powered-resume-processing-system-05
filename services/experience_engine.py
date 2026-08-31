import re
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

# Supported date months mapping
MONTHS_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9, "sept": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}

def get_current_year_month() -> Tuple[int, int]:
    """Dynamically get system year and month at runtime."""
    now = datetime.now()
    return now.year, now.month


class NormalizedExperience:
    def __init__(
        self,
        display_str: str,
        numeric_years: float,
        numeric_months: int,
        source: str,
        confidence: float,
        notes: str,
        explicit_val: Optional[str] = None,
        calculated_val: Optional[str] = None,
        discrepancy_flag: bool = False
    ):
        self.display_str = display_str
        self.numeric_years = numeric_years
        self.numeric_months = numeric_months
        self.source = source  # explicit_resume_statement | employment_dates | ai_resolved | fresher_statement | insufficient_information
        self.confidence = confidence
        self.notes = notes
        self.explicit_val = explicit_val
        self.calculated_val = calculated_val
        self.discrepancy_flag = discrepancy_flag

    def to_dict(self) -> Dict[str, Any]:
        return {
            "display_str": self.display_str,
            "numeric_years": self.numeric_years,
            "numeric_months": self.numeric_months,
            "source": self.source,
            "confidence": self.confidence,
            "notes": self.notes,
            "explicit_val": self.explicit_val,
            "calculated_val": self.calculated_val,
            "discrepancy_flag": self.discrepancy_flag
        }


def format_experience_display(numeric_years: float, modifier: str = "", raw_explicit_match: str = "") -> str:
    """Format experience into clean HR display string."""
    if numeric_years <= 0.0:
        return "Fresher"

    val_str = str(int(numeric_years)) if numeric_years.is_integer() else str(numeric_years)

    if raw_explicit_match:
        cleaned_match = raw_explicit_match.strip()
        if "+" in cleaned_match or "plus" in cleaned_match.lower() or "over" in cleaned_match.lower() or "more than" in cleaned_match.lower() or modifier == "+":
            return f"{val_str}+ Years"

    if modifier == "+" or numeric_years >= 10.0:
        return f"{val_str}+ Years"
    elif numeric_years < 1.0:
        months = int(round(numeric_years * 12))
        if months <= 1:
            return "1 Month"
        return f"{months} Months"
    elif numeric_years.is_integer():
        return f"{int(numeric_years)} Years" if numeric_years > 1 else "1 Year"
    else:
        return f"{numeric_years} Years"


def clean_experience_text_prepass(text: str) -> str:
    """
    Text cleanup pre-pass for experience extraction:
    - Normalizes OCR spaces in decimal numbers e.g. '5 . 5' -> '5.5'
    - Normalizes space-separated modifiers e.g. '5 +' -> '5+'
    - Standardizes date range dashes (em-dash, en-dash, 'to', 'through', 'until')
    """
    if not text:
        return ""

    # Fix space-separated decimals e.g. '5 . 5' -> '5.5'
    cleaned = re.sub(r"(\b\d+)\s*\.\s*(\d+\b)", r"\1.\2", text)
    
    # Fix space-separated modifiers e.g. '5 +' -> '5+'
    cleaned = re.sub(r"(\b\d+(?:\.\d+)?)\s+\+", r"\1+", cleaned)

    return cleaned


def segment_resume_sections(resume_text: str) -> Dict[str, str]:
    """
    Segment resume text into logical sections:
    work_experience, summary, education, skills, personal_info
    """
    if not resume_text:
        return {"work_experience": "", "summary": "", "education": "", "skills": "", "personal_info": ""}

    lines = resume_text.splitlines()
    sections = {
        "work_experience": [],
        "summary": [],
        "education": [],
        "skills": [],
        "personal_info": []
    }

    current_section = "summary"

    work_headers = ["work experience", "professional experience", "employment history", "career history", "work history", "employment", "experience", "work summary", "career summary"]
    edu_headers = ["education", "academic background", "academics", "qualifications", "educational qualification", "academic profile"]
    skill_headers = ["technical skills", "skills", "key skills", "core competencies", "competencies", "technologies"]
    personal_headers = ["personal details", "personal information", "contact", "contact details"]

    for line in lines:
        ll = line.lower().strip().rstrip(":")
        
        # Section headers should be standalone headings without numeric values
        if not re.search(r"\d", line):
            if any(ll == h or ll == h + ":" for h in work_headers):
                current_section = "work_experience"
                continue
            elif any(ll == h or ll == h + ":" for h in edu_headers):
                current_section = "education"
                continue
            elif any(ll == h or ll == h + ":" for h in skill_headers):
                current_section = "skills"
                continue
            elif any(ll == h or ll == h + ":" for h in personal_headers):
                current_section = "personal_info"
                continue

        sections[current_section].append(line)

    return {k: "\n".join(v) for k, v in sections.items()}


def extract_explicit_experience(resume_text: str) -> Optional[NormalizedExperience]:
    """
    LEVEL 1: Contextual extraction of explicit professional experience statements.
    Supports formats:
    - "5 years of experience", "5+ years", "5 yrs", "5.5 years"
    - "3 years 6 months", "18 months", "7 years 4 months"
    - "Experienced professional with 7 years...", "Having 4 years of..."
    - "Overall experience: 8 years", "Total experience - 6 years", "Professional experience = 9 years"
    - "Around 5 years", "More than 10 years", "Over 8 years", "Nearly 6 years"
    """
    if not resume_text:
        return None

    cleaned_text = clean_experience_text_prepass(resume_text)
    lines = cleaned_text.splitlines()

    explicit_patterns = [
        # Explicit labeled statements (e.g. "Total Experience: 5 Years", "Overall Experience - 3.5 yrs", "Work Experience = 6 yrs")
        r"(?:total|overall|professional|work|career)?\s*(?:experience|exp\.?)\s*[:\=\-]\s*(\d+(?:\.\d+)?\s*(?:\+)?\s*(?:years?|yrs?|months?|mos?)(?:\s*(?:and|&)?\s*\d+\s*(?:months?|mos?))?)",
        # Years + Months combinations e.g. "3 years 6 months", "7 years 4 months", "3 yrs 6 mos", "2 years and 4 months"
        r"\b(\d+)\s*(?:years?|yrs?)\s*(?:and|&)?\s*(\d+)\s*(?:months?|mos?)\b(?:\s*(?:of|in)?\s*(?:professional|work|industry|domain|software|tech|engineering)?\s*(?:experience|exp\.?))?",
        # Decimal or Integer Years with Exp/Experience e.g. "5 Years Exp", "5+ years of experience", "5 yrs exp", "around 5 years"
        r"\b(?:over|more\s+than|approx\.?|approximately|around|nearly|with|having)?\s*(\d+(?:\.\d+)?\s*(?:\+)?)\s*(?:years?|yrs?)\s*(?:of|in)?\s*(?:professional|work|industry|domain|software|tech|engineering|relevant|hands\-on)?\s*(?:experience|exp\.?)\b",
        # Explicit years in domain/field e.g. "Nearly 6 years in backend development", "5 years in Python"
        r"\b(?:over|more\s+than|approx\.?|approximately|around|nearly|with|having)?\s*(\d+(?:\.\d+)?\s*(?:\+)?)\s*(?:years?|yrs?)\s+(?:of|in)\s+[a-zA-Z0-9\s\-\/]{2,30}\b",
        # Stated months e.g. "18 months of experience", "10 months experience", "6 months experience"
        r"\b(\d+)\s*(?:months?|mos?)\s*(?:of|in)?\s*(?:professional|work|industry|domain|software|tech|engineering)?\s*(?:experience|exp\.?)\b",
        # Role with experience e.g. "Experienced professional with 8 years", "Developer with 4.5 yrs"
        r"\b(?:engineer|developer|architect|consultant|manager|lead|analyst|professional)\s+(?:with|having)\s+(\d+(?:\.\d+)?\s*(?:\+)?)\s*(?:years?|yrs?)\b"
    ]

    # Pass 0: Table Layout Inspection (Header row: "... | Experience | ...", Value row: "... | 4 Years | ...")
    for i in range(min(len(lines) - 1, 10)):
        h_line = lines[i].strip()
        v_line = lines[i + 1].strip()
        if "|" in h_line and "|" in v_line:
            h_cols = [c.strip().lower() for c in h_line.split("|")]
            v_cols = [c.strip() for c in v_line.split("|")]
            for idx, col_hdr in enumerate(h_cols):
                if "exp" in col_hdr or "experience" in col_hdr:
                    if idx < len(v_cols):
                        val_cell = v_cols[idx]
                        m_digits = re.search(r"\b(\d+(?:\.\d+)?\s*(?:\+)?)\s*(?:years?|yrs?|months?|mos?)\b", val_cell, re.IGNORECASE)
                        if m_digits:
                            num_str = m_digits.group(1)
                            yrs = float(num_str.replace("+", ""))
                            display = format_experience_display(yrs, modifier="+" if "+" in num_str else "")
                            return NormalizedExperience(
                                display_str=display,
                                numeric_years=yrs,
                                numeric_months=int(round(yrs * 12)),
                                source="explicit_resume_statement",
                                confidence=95.0,
                                notes=f"Table experience column extracted: '{val_cell}'",
                                explicit_val=display
                            )

    for i, line in enumerate(lines[:40]):  # Inspect top 40 header/summary lines
        line_clean = line.strip()
        if not line_clean:
            continue

        target_line = line_clean
        if i + 1 < len(lines):
            next_l = lines[i + 1].strip()
            if (any(k in line_clean.lower() for k in ["experience", "exp", "work experience", "total experience"]) and
                not re.search(r"\d", line_clean) and re.search(r"\d", next_l)):
                target_line = line_clean + " " + next_l

        # Split table rows / multi-field lines into independent cell segments
        segments = [s.strip() for s in re.split(r"[\|;\n]", target_line) if s.strip()]

        for seg in segments:
            seg_lower = seg.lower()
            for pat in explicit_patterns:
                m = re.search(pat, seg, re.IGNORECASE)
                if m:
                    match_str = m.group(0).lower()

                    # Context Rejection Checks on match window:
                    # Ignore if match window contains Age ("28 years old"), CTC/LPA, Phone, Email, Education graduation, Project duration
                    if any(k in match_str for k in ["years old", "yrs old", "age:", "ctc", "lpa", "salary", "lakh", "lac", "inr", "$", "phone", "mobile", "contact", "@", "graduated", "gpa", "marks"]):
                        continue

                    # Reject software version context e.g. "Java 8", "HTML 5", "Python 3.10", "Windows 11", ".NET 6", "Angular 14"
                    if re.search(r"\b(?:java|python|html|css|windows|sql|angular|react|node|\.net|version)\s*\d", seg.lower()):
                        if "experience" not in seg.lower():
                            continue

            for pat in explicit_patterns:
                m = re.search(pat, seg, re.IGNORECASE)
                if m:
                    groups = m.groups()
                    
                    # Case 1: Years + Months combination e.g. ("3", "6")
                    if len(groups) == 2 and groups[0] and groups[1] and groups[0].isdigit() and groups[1].isdigit():
                        yrs = float(groups[0])
                        mos = float(groups[1])
                        total_yrs = round(yrs + (mos / 12.0), 1)
                        tot_mos = int(yrs * 12 + mos)
                        display = format_experience_display(total_yrs, raw_explicit_match=f"{groups[0]} Years {groups[1]} Months")
                        return NormalizedExperience(
                            display_str=display,
                            numeric_years=total_yrs,
                            numeric_months=tot_mos,
                            source="explicit_resume_statement",
                            confidence=95.0,
                            notes=f"Explicit years + months statement extracted: '{m.group(0)}'",
                            explicit_val=display
                        )

                    # Check for explicit Years + Months combination e.g. "3 years 6 months", "7 years 4 months"
                    m_ym = re.search(r"\b(\d+)\s*(?:years?|yrs?)\s*(?:and|&)?\s*(\d+)\s*(?:months?|mos?)\b", seg, re.IGNORECASE)
                    if m_ym:
                        yrs = float(m_ym.group(1))
                        mos = float(m_ym.group(2))
                        total_yrs = round(yrs + (mos / 12.0), 1)
                        tot_mos = int(yrs * 12 + mos)
                        display = format_experience_display(total_yrs, raw_explicit_match=m_ym.group(0))
                        return NormalizedExperience(
                            display_str=display,
                            numeric_years=total_yrs,
                            numeric_months=tot_mos,
                            source="explicit_resume_statement",
                            confidence=95.0,
                            notes=f"Explicit years + months statement extracted: '{m_ym.group(0)}'",
                            explicit_val=display
                        )

                    val_str = groups[0].strip() if groups else m.group(0).strip()

                    # Check if it's months only e.g. "18 months", "6 months"
                    if re.search(r"\b(?:months?|mos?)\b", seg, re.IGNORECASE) and not re.search(r"\b(?:years?|yrs?)\b", seg, re.IGNORECASE):
                        digits = re.findall(r"\d+(?:\.\d+)?", val_str)
                        if digits:
                            mos = float(digits[0])
                            if 1 <= mos <= 600:
                                total_yrs = round(mos / 12.0, 1)
                                tot_mos = int(mos)
                                display = format_experience_display(total_yrs)
                                return NormalizedExperience(
                                    display_str=display,
                                    numeric_years=total_yrs,
                                    numeric_months=tot_mos,
                                    source="explicit_resume_statement",
                                    confidence=95.0,
                                    notes=f"Explicit months statement extracted: '{m.group(0)}'",
                                    explicit_val=display
                                )

                    # Case 3: Years e.g. "5+", "5.5", "8"
                    digits = re.findall(r"\d+(?:\.\d+)?", val_str)
                    if digits:
                        yrs = float(digits[0])
                        if 0.1 <= yrs <= 60.0:
                            has_over_modifier = bool(re.search(r"\b(?:over|more\s+than|plus)\b", seg_lower))
                            modifier = "+" if "+" in val_str or "+" in m.group(0) or has_over_modifier else ""
                            display = format_experience_display(yrs, modifier=modifier, raw_explicit_match=val_str)
                            tot_mos = int(round(yrs * 12))
                            return NormalizedExperience(
                                display_str=display,
                                numeric_years=yrs,
                                numeric_months=tot_mos,
                                source="explicit_resume_statement",
                                confidence=95.0,
                                notes=f"Explicit professional experience statement extracted: '{m.group(0)}'",
                                explicit_val=display
                            )

    return None


def parse_single_date(date_str: str, is_end_date: bool = False) -> Optional[Tuple[int, int, bool]]:
    """
    Parse a single date snippet into (year, month, has_explicit_month).
    Supports:
    - Month YYYY e.g. 'Jan 2020', 'January 2020', 'Nov, 2022'
    - MM/YYYY or MM-YYYY e.g. '06/2019', '01-2021'
    - YYYY-MM or YYYY/MM e.g. '2020-01', '2024-05'
    - Standalone YYYY e.g. '2018', '2022'
    - Present/Current keywords
    """
    if not date_str:
        return None

    clean = date_str.lower().strip()
    curr_yr, curr_mo = get_current_year_month()

    # 1. Check for present/current keywords dynamically
    if any(k in clean for k in ["present", "current", "till date", "till now", "ongoing", "currently working", "now"]):
        return curr_yr, curr_mo, True

    # 2. Check YYYY-MM or YYYY/MM format e.g. '2020-01', '2024-05'
    ym_match = re.search(r"\b(19\d{2}|20\d{2})[\/\-](0[1-9]|1[0-2])\b", clean)
    if ym_match:
        yr = int(ym_match.group(1))
        mo = int(ym_match.group(2))
        if yr <= curr_yr + 1:
            return yr, mo, True

    # 3. Check year 19xx or 20xx
    y_match = re.search(r"\b(19\d{2}|20\d{2})\b", clean)
    if not y_match:
        return None
    year = int(y_match.group(1))

    if year > curr_yr + 1:
        return None

    has_explicit_month = False
    month = 1

    # Check month name e.g. "jan", "february"
    for m_name, m_num in MONTHS_MAP.items():
        if re.search(r"\b" + re.escape(m_name) + r"\b", clean):
            month = m_num
            has_explicit_month = True
            break

    # Check MM/YYYY, MM-YYYY, DD/MM/YYYY
    if not has_explicit_month:
        digits = re.findall(r"\b\d{1,2}\b", clean)
        if digits:
            for d_str in digits:
                d_val = int(d_str)
                if 1 <= d_val <= 12 and d_val != year:
                    month = d_val
                    has_explicit_month = True
                    break

    return year, month, has_explicit_month


def merge_overlapping_intervals(intervals: List[Tuple[int, int, int, int, bool]]) -> List[Tuple[int, int]]:
    """
    Merge overlapping employment date intervals.
    Each input item: (start_year, start_month, end_year, end_month, is_pure_year).
    Converts into continuous absolute month bounds, merges overlapping ranges,
    and returns non-overlapping (start_abs_month, end_abs_month) ranges.
    """
    if not intervals:
        return []

    abs_ranges = []
    for sy, sm, ey, em, is_pure_year in intervals:
        if is_pure_year or sm == em:
            start_abs = sy * 12 + sm
            end_abs = ey * 12 + em
        else:
            start_abs = sy * 12 + sm
            end_abs = ey * 12 + em + 1
        if end_abs >= start_abs:
            abs_ranges.append((start_abs, end_abs))

    if not abs_ranges:
        return []

    # Sort ranges by start_abs
    abs_ranges.sort(key=lambda r: r[0])

    merged = []
    curr_start, curr_end = abs_ranges[0]

    for next_start, next_end in abs_ranges[1:]:
        if next_start <= curr_end:  # Overlapping or contiguous
            curr_end = max(curr_end, next_end)
        else:
            merged.append((curr_start, curr_end))
            curr_start, curr_end = next_start, next_end

    merged.append((curr_start, curr_end))
    return merged


def calculate_experience_from_dates(resume_text: str) -> Optional[NormalizedExperience]:
    """
    LEVEL 2: Generic employment history date range calculator.
    - Multi-format date range parser.
    - Merges overlapping jobs to prevent double-counting.
    - Excludes Education, Certifications, Career Breaks, Sabbaticals, and Academic Internships.
    """
    if not resume_text:
        return None

    cleaned_text = clean_experience_text_prepass(resume_text)
    sections = segment_resume_sections(cleaned_text)
    work_text = sections.get("work_experience") or cleaned_text

    # Regex for date ranges: e.g. "Jan 2020 - Mar 2024", "01/2020 to 05/2024", "2020-01 - 2024-05", "2018 - Present", "2020 to 2024"
    date_part_pat = r"(?:(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|september|sept|oct|october|nov|november|dec|december|\d{1,2}[\/\-])?\s*\b(?:19|20)\d{2}\b(?:\s*[\/\-]\s*\d{1,2})?|present|current|till\s+date|till\s+now|ongoing|currently\s+working|now)"
    
    date_range_pat = r"(\b" + date_part_pat + r")\s*(?:--|–|—|-|to|through|until)\s*(\b" + date_part_pat + r")"

    lines = work_text.splitlines()
    raw_intervals = []
    log_details = []

    for line in lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()

        # Exclude lines that are clearly career breaks, gaps, sabbaticals, education, certifications, or project titles
        if any(k in line_lower for k in ["career break", "career gap", "break", "gap", "sabbatical", "maternity leave", "paternity leave", "study break", "unemployed", "job search", "b.tech", "b.e", "m.tech", "bca", "mca", "b.sc", "m.sc", "bba", "mba", "phd", "university", "college", "school", "high school", "degree", "diploma", "gpa", "marks"]):
            continue

        # Ignore academic internships or college projects if line explicitly specifies non-professional
        if any(k in line_lower for k in ["academic internship", "college project", "academic project", "workshop"]):
            continue

        matches = re.findall(date_range_pat, line_clean, re.IGNORECASE)
        for s_raw, e_raw in matches:
            s_parsed = parse_single_date(s_raw, is_end_date=False)
            e_parsed = parse_single_date(e_raw, is_end_date=True)

            if s_parsed and e_parsed:
                sy, sm, s_has_m = s_parsed
                ey, em, e_has_m = e_parsed

                if ey < sy or (ey == sy and em < sm):
                    continue

                # Filter out education ranges e.g. 2018-2022 if line contains degree keywords
                if (ey - sy == 4 or ey - sy == 3) and any(k in line_lower for k in ["btech", "be", "bsc", "bba", "bca", "passout", "graduated"]):
                    continue

                is_pure_year = (not s_has_m and not e_has_m and "present" not in e_raw.lower() and "current" not in e_raw.lower())
                raw_intervals.append((sy, sm, ey, em, is_pure_year))
                log_details.append(f"{s_raw.strip()} to {e_raw.strip()}")

    if not raw_intervals:
        return None

    # Merge overlapping intervals
    merged_intervals = merge_overlapping_intervals(raw_intervals)

    total_net_months = 0
    for start_m, end_m in merged_intervals:
        dur = end_m - start_m
        if dur > 0:
            total_net_months += dur

    if total_net_months <= 0:
        return None

    numeric_years = round(total_net_months / 12.0, 1)
    display_str = format_experience_display(numeric_years)

    log_msg = f"Calculated {numeric_years} years from {len(merged_intervals)} merged employment period(s): {'; '.join(log_details)}"
    return NormalizedExperience(
        display_str=display_str,
        numeric_years=numeric_years,
        numeric_months=total_net_months,
        source="employment_dates",
        confidence=90.0,
        notes=log_msg,
        calculated_val=display_str
    )


def detect_fresher(resume_text: str) -> Optional[NormalizedExperience]:
    """
    Detect explicit fresher evidence in resume text.
    Handles phrases like:
      - "Fresher", "Fresh Graduate", "Recent Graduate"
      - "No work experience", "No professional experience"
      - "Entry-level candidate"
    """
    if not resume_text:
        return None

    resume_lower = resume_text.lower()

    fresher_indicators = [
        r"\bfresher\b",
        r"\bfresh\s+graduate\b",
        r"\brecent(?:\s+\w+)?\s+graduate\b",
        r"\bfirst\s+opportunity\b",
        r"\bfirst\s+role\b",
        r"\bfirst\s+job\b",
        r"\bno\s+work\s+experience\b",
        r"\bno\s+professional\s+experience\b",
        r"\bno\s+full\-time\s+experience\b",
        r"\binternship\s+only\b",
        r"\bentry\s*\-?\s*level\s+candidate\b",
        r"\bentry\s*\-?\s*level\s+software\b",
        r"\bentry\s*\-?\s*level\b",
        r"\bseeking\s+(?:an?\s+)?entry\s*\-?\s*level\b"
    ]

    for pat in fresher_indicators:
        m = re.search(pat, resume_lower)
        if m:
            return NormalizedExperience(
                display_str="Fresher",
                numeric_years=0.0,
                numeric_months=0,
                source="fresher_statement",
                confidence=95.0,
                notes=f"Fresher identified from explicit indicator: '{m.group(0)}'",
                explicit_val="Fresher"
            )

    return None


def evaluate_total_experience(resume_text: str) -> NormalizedExperience:
    """
    Master Evaluation Pipeline:
    LEVEL 1: Explicit Fresher Statement (Highest priority if present without multi-year work history)
    LEVEL 2: Explicit professional experience statement (e.g. "5 years of experience")
    LEVEL 3: Date-based employment history calculation (merged & gap-checked)
    LEVEL 4: Safe Fallback ("Not Specified" when history is unparseable and NO fresher evidence exists)
    """
    if not resume_text or not resume_text.strip():
        return NormalizedExperience(
            display_str="Not Specified",
            numeric_years=0.0,
            numeric_months=0,
            source="insufficient_information",
            confidence=0.0,
            notes="Empty resume text."
        )

    # Check for explicit Fresher statement
    exp_fresher = detect_fresher(resume_text)

    # Try Explicit Experience Extractor
    exp_explicit = extract_explicit_experience(resume_text)

    # Try Employment Date Range Calculator
    exp_dates = calculate_experience_from_dates(resume_text)

    # If explicit fresher indicator is present AND there are no date-based multi-year jobs (>1.5 yrs), return Fresher!
    if exp_fresher:
        if not exp_dates or exp_dates.numeric_years < 1.5:
            if not exp_explicit or "fresher" in exp_explicit.display_str.lower():
                return exp_fresher

    # Reconcile Explicit Statement and Date Calculations
    if exp_explicit and exp_dates:
        diff = abs(exp_explicit.numeric_years - exp_dates.numeric_years)
        discrepancy = diff > 2.0
        
        if not discrepancy or exp_explicit.numeric_years >= exp_dates.numeric_years:
            exp_explicit.calculated_val = exp_dates.display_str
            exp_explicit.discrepancy_flag = discrepancy
            exp_explicit.notes += f" (Supported by date calculation: {exp_dates.numeric_years} Years)"
            return exp_explicit
        else:
            exp_dates.explicit_val = exp_explicit.display_str
            exp_dates.discrepancy_flag = discrepancy
            exp_dates.notes += f" (Explicit statement: '{exp_explicit.display_str}')"
            return exp_dates

    if exp_explicit:
        return exp_explicit

    if exp_dates:
        return exp_dates

    if exp_fresher:
        return exp_fresher

    # Default Safe Fallback: Return "Not Specified" rather than false Fresher
    return NormalizedExperience(
        display_str="Not Specified",
        numeric_years=0.0,
        numeric_months=0,
        source="insufficient_information",
        confidence=40.0,
        notes="No explicit experience statement or valid employment dates found."
    )
