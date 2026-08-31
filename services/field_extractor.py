import re
from datetime import datetime
from typing import Dict, Any, Tuple, List

NON_NAME_KEYWORDS = {
    "resume", "curriculum vitae", "cv", "profile", "summary", "objective",
    "education", "experience", "work experience", "skills", "technical skills",
    "projects", "certifications", "contact", "contact details", "personal details",
    "declaration", "hobbies", "languages", "page", "email", "mobile", "phone",
    "address", "linkedin", "github"
}

# Standard technology dictionary for normalization
TECH_DICTIONARY = {
    "prompt engineering": "Prompt Engineering",
    "promp engineering": "Prompt Engineering",
    "retrieval augmented generation": "Retrieval Augmented Generation (RAG)",
    "retrieval-augmented generation": "Retrieval Augmented Generation (RAG)",
    "rag": "Retrieval Augmented Generation (RAG)",
    "react.js": "React.js",
    "reactjs": "React.js",
    "react": "React.js",
    "fastapi": "FastAPI",
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "html5": "HTML5",
    "css3": "CSS3",
    "sql": "SQL",
    "django": "Django",
    "flask": "Flask",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "aws bedrock": "AWS Bedrock",
    "large language models": "Large Language Models (LLMs)",
    "llms": "Large Language Models (LLMs)",
    "llm": "Large Language Models (LLMs)",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "openpyxl": "OpenPyXL",
    "git": "Git",
    "bitbucket": "Bitbucket",
    "postman": "Postman",
    "langchain": "LangChain",
    "salesforce": "Salesforce",
    "sap": "SAP",
    "oracle": "Oracle",
    "pl/sql": "PL/SQL",
    "plsql": "PL/SQL",
    "rest apis": "REST APIs",
    "rest api": "REST APIs",
    "node.js": "Node.js",
    "nodejs": "Node.js"
}


def clean_and_reconstruct_text(raw_text: str) -> str:
    """
    Clean raw resume text and reconstruct broken words.
    - Fixes hyphens split across line breaks (e.g. 'Retrieval-\\nAugmented' -> 'Retrieval-Augmented').
    - Reconstructs space-split technology terms (e.g. 'Rea ct.js' -> 'React.js', 'Promp t Engin eering' -> 'Prompt Engineering').
    - Normalizes multiple spaces and tabs.
    """
    if not raw_text:
        return ""

    # Fix line-wrap hyphens
    cleaned = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1-\2", raw_text)
    
    # Specific space-split word reconstructions
    replacements = [
        (r"\bPromp\s*t\s+Engin\s*eering\b", "Prompt Engineering"),
        (r"\bPromp\s*Engin\s*ring\b", "Prompt Engineering"),
        (r"\bR\s*etr\s*ieval\s+Aug\s*mented\s+Gen\s*eration\b", "Retrieval Augmented Generation"),
        (r"\bR\s*tr\s*iva\s+A\s*gm\s*n\s+d\s+G\s*n\s*ra\s*ion\b", "Retrieval Augmented Generation"),
        (r"\bRea\s*ct\.js\b", "React.js"),
        (r"\bRea\s*ctjs\b", "React.js"),
        (r"\bFast\s*API\b", "FastAPI"),
        (r"\bJava\s*Script\b", "JavaScript"),
        (r"\bHTML\s*5\b", "HTML5"),
        (r"\bCSS\s*3\b", "CSS3"),
        (r"\bPy\s*Thon\b", "Python"),
        (r"\bPost\s*gre\s*SQL\b", "PostgreSQL"),
        (r"\bOpen\s*Py\s*XL\b", "OpenPyXL"),
        (r"\bLang\s*Chain\b", "LangChain"),
        (r"\bPy\s*Torch\b", "PyTorch"),
        (r"\bTensor\s*Flow\b", "TensorFlow")
    ]

    for pat, repl in replacements:
        cleaned = re.sub(pat, repl, cleaned, flags=re.IGNORECASE)

    # Normalize multiple whitespace lines/spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def extract_name(resume_text: str) -> str:
    """Extract candidate name from resume text."""
    if not resume_text:
        return ""
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    for line in lines[:20]:
        m = re.search(r"^(?:candidate\s+name|full\s+name|name)\s*[:\-]\s*(.+)$", line, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            candidate = re.sub(r"[^\w\s\.]", "", candidate).strip()
            if candidate and len(candidate.split()) <= 5 and candidate.lower() not in NON_NAME_KEYWORDS:
                return candidate.title()

    for line in lines[:10]:
        clean_line = re.sub(r"[^\w\s]", "", line).strip()
        line_lower = clean_line.lower()
        if ("@" in line or "http" in line or "www" in line or 
            re.search(r"\d", line) or line_lower in NON_NAME_KEYWORDS):
            continue
        words = clean_line.split()
        if 1 <= len(words) <= 4 and all(w.isalpha() for w in words):
            if not any(w.lower() in NON_NAME_KEYWORDS for w in words):
                return clean_line.title()
    return ""


def extract_mobile(resume_text: str) -> str:
    """Extract mobile number from resume text."""
    if not resume_text:
        return ""
    m_labeled = re.search(
        r"(?:mobile|phone|contact|mob|tel|call)\s*[:\-]?\s*(\+?\d[\d\s\-\(\)]{8,16}\d)",
        resume_text,
        re.IGNORECASE
    )
    if m_labeled:
        raw_num = m_labeled.group(1).strip()
        digits = re.sub(r"\D", "", raw_num)
        if 10 <= len(digits) <= 13:
            return raw_num

    phone_patterns = [
        r"\+91[\s-]?[6-9]\d{9}\b",
        r"\b[6-9]\d{4}[\s-]\d{5}\b",
        r"\b[6-9]\d{9}\b",
        r"\+\d{1,3}[\s-]?\d{9,12}\b"
    ]
    for pat in phone_patterns:
        matches = re.findall(pat, resume_text)
        for match in matches:
            digits = re.sub(r"\D", "", match)
            if len(digits) >= 10:
                return match.strip()
    return ""


def normalize_skills(raw_skills: str) -> Tuple[str, float]:
    """
    Normalize extracted skill list and assign extraction confidence score.
    Maps terms to canonical TECH_DICTIONARY names without corruption.
    """
    if not raw_skills:
        return "", 0.0

    # FIX: Use unicode bullet point escape [\u2022\u25cf\*\-\|] to prevent replacing letters 'e','u','l','t'!
    cleaned = re.sub(r"[\u2022\u25cf\*\-\|]", " ", raw_skills)
    items = [item.strip() for item in re.split(r"[,;\n]", cleaned) if item.strip()]

    normalized_list = []
    seen = set()

    for item in items:
        item_lower = item.lower().strip()
        if not item_lower or len(item_lower) > 50:
            continue

        matched_name = TECH_DICTIONARY.get(item_lower)
        if not matched_name:
            for k, canonical in TECH_DICTIONARY.items():
                if k in item_lower and len(k) >= 3:
                    matched_name = canonical
                    break

        final_skill = matched_name if matched_name else item.title()

        if final_skill.lower() not in seen:
            seen.add(final_skill.lower())
            normalized_list.append(final_skill)

    skill_result = ", ".join(normalized_list)
    confidence = 92.0 if normalized_list else 50.0
    return skill_result, confidence


def extract_skills(resume_text: str) -> str:
    """Extract skills section from raw resume text."""
    if not resume_text:
        return ""
    skill_header_pat = r"(?:technical\s+skills|key\s+skills|core\s+skills|it\s+skills|technical\s+expertise|tools\s*&\s*technologies|programming\s+skills|skills\s*&\s*competencies|core\s+competencies|competencies|areas?\s+of\s+expertise|skills\s*&\s*tools|technical\s+summary|technologies|skills)"
    lines = resume_text.splitlines()
    capturing = False
    captured_lines = []
    stop_headers = {
        "experience", "work experience", "professional experience", "employment history",
        "education", "academic background", "projects", "key projects", "certifications",
        "achievements", "declaration", "personal details", "languages", "summary"
    }

    for i, line in enumerate(lines):
        line_clean = line.strip()
        line_lower = line_clean.lower().rstrip(":")
        if not line_clean:
            if capturing and len(captured_lines) >= 3:
                break
            continue
        if not capturing and re.match(r"^" + skill_header_pat + r"\s*[:\-]?$", line_lower, re.IGNORECASE):
            capturing = True
            continue
        if not capturing:
            m_inline = re.match(r"^" + skill_header_pat + r"\s*[:\-]\s*(.+)$", line_clean, re.IGNORECASE)
            if m_inline:
                captured_lines.append(m_inline.group(1).strip())
                capturing = True
                continue
        if capturing:
            if any(line_lower == h or line_lower.startswith(h + ":") for h in stop_headers):
                break
            captured_lines.append(line_clean)

    if captured_lines:
        combined = ", ".join(captured_lines)
        norm_skills, _ = normalize_skills(combined)
        return norm_skills
    return ""


def extract_notice_period(resume_text: str) -> str:
    """Extract notice period / availability from resume text."""
    if not resume_text:
        return ""
    imm_pattern = r"\b(?:immediate\s+joiner|available\s+immediately|can\s+join\s+immediately|available\s+to\s+join\s+immediately|immediate)\b"
    if re.search(imm_pattern, resume_text, re.IGNORECASE):
        return "Immediate"
    np_patterns = [
        r"(?:notice\s+period|notice|availability)\s*[:\-]\s*([^\n\,\.]+)",
        r"(\d+\s*(?:days?|months?|weeks?))\s*(?:notice|notice\s+period)",
        r"(?:serving\s+notice\s+period\s*[\(\-]?\s*)([^\n\)\,\.]+)"
    ]
    for pat in np_patterns:
        m = re.search(pat, resume_text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if "immediate" in val.lower() or "0" in val:
                return "Immediate"
            return val.title()
    return ""


def parse_month_year(date_str: str) -> Tuple[int, int]:
    """Parse month and year from string snippet like 'Nov 2022', '11/2022', '2022'."""
    months_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    date_clean = date_str.lower().strip()
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", date_clean)
    if not year_match:
        return None, None
    year = int(year_match.group(1))

    month = 1
    for m_name, m_num in months_map.items():
        if m_name in date_clean:
            month = m_num
            break
    return year, month


from services.experience_engine import evaluate_total_experience

def calculate_experience_from_dates(resume_text: str) -> Tuple[str, float, str]:
    """
    Delegate total experience calculation to generic experience engine.
    Returns (formatted_experience, confidence_score, log_notes).
    """
    norm_exp = evaluate_total_experience(resume_text)
    return norm_exp.display_str, norm_exp.confidence, norm_exp.notes


def extract_experience(resume_text: str) -> str:
    """Extract total experience using generic experience engine."""
    norm_exp = evaluate_total_experience(resume_text)
    print(f"[EXPERIENCE CALCULATION] Result: {norm_exp.display_str} (Source: {norm_exp.source}, Confidence: {norm_exp.confidence}%) - {norm_exp.notes}")
    return norm_exp.display_str


def extract_email(resume_text: str) -> str:
    """Extract email address from resume text."""
    if not resume_text:
        return ""
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text)
    return m.group(0).strip().lower() if m else ""


def extract_linkedin(resume_text: str) -> str:
    """Extract LinkedIn URL or handle from resume text."""
    if not resume_text:
        return ""
    m = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+", resume_text, re.IGNORECASE)
    return m.group(0).strip() if m else ""


def extract_education(resume_text: str) -> str:
    """Extract education summary from resume text."""
    if not resume_text:
        return ""
    edu_patterns = [
        r"\b(?:b\.?tech|b\.?e|m\.?tech|m\.?e|bca|mca|b\.?sc|m\.?sc|bba|mba|phd|bachelor|master|degree|diploma)\b[^\n]*",
    ]
    matches = []
    for pat in edu_patterns:
        m = re.findall(pat, resume_text, re.IGNORECASE)
        if m:
            matches.extend([x.strip() for x in m if len(x.strip()) < 80])
    if matches:
        return "; ".join(list(dict.fromkeys(matches))[:3])
    return ""


def extract_certifications(resume_text: str) -> str:
    """Extract certifications summary from resume text."""
    if not resume_text:
        return ""
    cert_pat = r"(?:certification|certified|course|completed)\s*[:\-]?\s*([^\n]+)"
    matches = re.findall(cert_pat, resume_text, re.IGNORECASE)
    if matches:
        return "; ".join(list(dict.fromkeys([x.strip() for x in matches if len(x.strip()) < 100]))[:3])
    return ""


def extract_location(resume_text: str) -> str:
    """Extract location from resume text."""
    if not resume_text:
        return ""
    cities = ["Bangalore", "Bengaluru", "Hyderabad", "Chennai", "Mumbai", "Pune", "Delhi", "Noida", "Gurgaon", "Gurugram", "Kolkata", "Ahmedabad", "Kochi", "Trivandrum", "Warangal", "Karimnagar"]
    for c in cities:
        if re.search(r"\b" + re.escape(c) + r"\b", resume_text, re.IGNORECASE):
            return c
    m = re.search(r"(?:location|city|address|based\s+in)\s*[:\-]\s*([^\n\,]+)", resume_text, re.IGNORECASE)
    if m:
        return m.group(1).strip().title()
    return ""


def extract_ctc(resume_text: str, ctc_type: str = "current") -> str:
    """
    Extract CTC figure from resume text.
    Strictly separates Current CTC from Expected CTC.
    Never returns experience strings like 'Fresher' or 'X Years'.
    """
    if not resume_text:
        return ""

    if ctc_type == "expected":
        exp_pat = r"(?:expected\s+(?:ctc|salary|compensation|package|remuneration)|exp\.?\s+(?:ctc|salary|compensation|package)|target\s+(?:ctc|salary|package)|desired\s+(?:ctc|salary|package))\s*[:\-]?\s*([^\n\,\.]+)"
        m = re.search(exp_pat, resume_text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # Ensure it is not an experience value or invalid word
            if not any(k in val.lower() for k in ["fresher", "years", "yrs", "year", "month", "mos"]):
                return val
        return ""
    else:
        # Current CTC
        curr_pat = r"(?:current\s+(?:ctc|salary|compensation|package|remuneration)|present\s+(?:ctc|salary|compensation|package|remuneration)|fixed\s+(?:ctc|salary))\s*[:\-]?\s*([^\n\,\.]+)"
        m = re.search(curr_pat, resume_text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if not any(k in val.lower() for k in ["fresher", "years", "yrs", "year", "month", "mos"]):
                return val

        # General CTC / Salary label (only if not preceded by expected/target/desired)
        gen_pat = r"(?<!expected\s)(?<!target\s)(?<!desired\s)\b(?:ctc|salary|annual\s+package)\b\s*[:\-]?\s*([^\n\,\.]+)"
        m_gen = re.search(gen_pat, resume_text, re.IGNORECASE)
        if m_gen:
            val = m_gen.group(1).strip()
            if not any(k in val.lower() for k in ["fresher", "years", "yrs", "year", "month", "mos"]):
                return val

        # Standalone LPA search (only as fallback for current CTC if not expected)
        m_lpa = re.search(r"(\d+(?:\.\d+)?\s*(?:lpa|lakhs?|lac))", resume_text, re.IGNORECASE)
        if m_lpa:
            val = m_lpa.group(1).strip()
            if not any(k in val.lower() for k in ["fresher", "years", "yrs", "year", "month", "mos"]):
                return val

        return ""



def extract_relevant_experience(resume_text: str, skills_str: str = "") -> str:
    """Extract relevant experience years."""
    if not resume_text:
        return ""
    m = re.search(r"(?:relevant\s+experience|rel\.?\s+exp)\s*[:\-]\s*([^\n\,\.]+)", resume_text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return extract_experience(resume_text)


def run_ai_candidate_screening(resume_text: str, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Automated AI candidate screening Q&A solver."""
    resume_lower = resume_text.lower()
    skills_text = str(candidate_data.get("Skills", "")).lower()
    combined = f"{resume_lower} {skills_text}"

    has_oracle = "Yes" if "oracle" in combined or "pl/sql" in combined or "plsql" in combined else "No"
    
    java_fit = "Suitable" if any(k in combined for k in ["java", "spring", "hibernate"]) else "Unsuited"
    python_fit = "Suitable" if any(k in combined for k in ["python", "django", "fastapi", "flask"]) else "Unsuited"
    ai_ml_fit = "Suitable" if any(k in combined for k in ["ai", "ml", "llm", "rag", "pytorch", "tensorflow"]) else "Unsuited"

    suitability = []
    if java_fit == "Suitable": suitability.append("Java Developer")
    if python_fit == "Suitable": suitability.append("Python Developer")
    if ai_ml_fit == "Suitable": suitability.append("AI/ML Engineer")
    if not suitability: suitability.append("General Tech Role")

    screening_summary = f"Oracle Exp: {has_oracle} | Suitable Roles: {', '.join(suitability)}"

    return {
        "_oracle_exp": has_oracle,
        "_suitable_roles": ", ".join(suitability),
        "_ai_screening_summary": screening_summary
    }


def extract_all_fields_fallback(resume_text: str) -> Dict[str, str]:
    """Return dictionary of all fallback extracted candidate fields."""
    cleaned_text = clean_and_reconstruct_text(resume_text)
    exp_formatted, exp_conf, exp_notes = calculate_experience_from_dates(cleaned_text)

    return {
        "Candidate Name": extract_name(cleaned_text),
        "Mobile Number": extract_mobile(cleaned_text),
        "Email Address": extract_email(cleaned_text),
        "Skills": extract_skills(cleaned_text),
        "Notice Period": extract_notice_period(cleaned_text),
        "Total Experience": exp_formatted,
        "Relevant Experience": extract_relevant_experience(cleaned_text),
        "Current Location": extract_location(cleaned_text),
        "Preferred Location": extract_location(cleaned_text),
        "Current CTC": extract_ctc(cleaned_text, "current"),
        "Expected CTC": extract_ctc(cleaned_text, "expected"),
        "LinkedIn Profile": extract_linkedin(cleaned_text),
        "Education": extract_education(cleaned_text),
        "Certifications": extract_certifications(cleaned_text),
        "Remarks": ""
    }
