import os
import re
import json
import requests
from typing import Tuple, Dict, Any, List
from dotenv import load_dotenv

from utils.helpers import (
    extract_json_from_response,
    classify_technology,
    classify_experience
)
from services.field_extractor import (
    clean_and_reconstruct_text,
    calculate_experience_from_dates,
    normalize_skills,
    extract_all_fields_fallback,
    extract_name,
    extract_mobile,
    extract_skills,
    extract_notice_period,
    extract_experience,
    run_ai_candidate_screening
)

# Load environment variables
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

def check_ollama_status() -> Tuple[bool, str, List[str]]:
    """
    Check if Ollama server is accessible and retrieve available models.
    Returns (is_online, message, model_list).
    """
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            if OLLAMA_MODEL in models or any(OLLAMA_MODEL in m for m in models):
                return True, f"Ollama Online ({OLLAMA_MODEL} available)", models
            else:
                return False, f"Ollama Online, but model '{OLLAMA_MODEL}' was not found.", models
        else:
            return False, f"Ollama returned HTTP status {response.status_code}.", []
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Ollama at http://localhost:11434. Please start Ollama.", []
    except Exception as e:
        return False, f"Error checking Ollama status: {str(e)}", []


def extract_candidate_data(resume_text: str, excel_headers: List[str]) -> Tuple[bool, Dict[str, Any], str, str]:
    """
    Processing Architecture:
    Resume Text -> Text Cleanup & Word Reconstruction -> AI Analysis -> Experience Calculation -> Skills Normalization -> Mapping.
    Returns (success, candidate_dict, raw_response, error_message).
    """
    if not resume_text or not resume_text.strip():
        return False, {}, "", "Resume text is empty."

    # Step 1: Text Cleanup & Word Reconstruction
    cleaned_text = clean_and_reconstruct_text(resume_text)

    # Step 2: Pre-extract deterministic fallbacks & calculated experience
    fallback_data = extract_all_fields_fallback(cleaned_text)
    calc_exp, exp_conf, exp_notes = calculate_experience_from_dates(cleaned_text)

    # Build exact JSON template schema for the prompt
    schema = {header: "" for header in excel_headers}
    schema_str = json.dumps(schema, indent=2)

    prompt = f"""You are an expert HR data extraction assistant.
Extract information from the provided candidate resume text to populate an Excel template.

CRITICAL INSTRUCTIONS:
1. Extract candidate information matching EXACTLY these required target keys:
{schema_str}

2. ABSOLUTE ACCURACY RULE: NEVER invent, hallucinate, or guess candidate details.
   - If a requested field is NOT explicitly mentioned or available in the resume, set its value to "".
   - Do NOT guess mobile numbers, email addresses, notice period, CTC, or experience if not present.

3. Output format: Respond ONLY with a valid JSON object matching the requested schema keys. Do not include markdown preamble or conversational text.

RESUME TEXT:
-------------------
{cleaned_text}
-------------------
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_predict": 1024
        }
    }

    raw_llm_text = ""
    extracted_dict = {}

    try:
        url = f"{OLLAMA_URL}/api/generate"
        response = requests.post(url, json=payload, timeout=60)

        if response.status_code == 200:
            res_json = response.json()
            raw_llm_text = res_json.get("response", "")
            extracted_dict = extract_json_from_response(raw_llm_text)
    except Exception as e:
        print(f"Warning: Ollama API call failed or timed out ({str(e)}). Using deterministic extraction fallback.")

    def classify_header_concept(header_str: str) -> str:
        """
        Map an arbitrary header name to its canonical semantic concept.
        Strictly differentiates Expected CTC vs Current CTC vs Experience vs Location.
        """
        if not header_str:
            return "UNKNOWN"
        h = str(header_str).strip().lower().replace("_", " ").replace("-", " ").replace(".", " ")
        h = re.sub(r"\s+", " ", h).strip()

        # 1. Email (Check before address/location)
        if "email" in h or "mail" in h:
            return "EMAIL_ADDRESS"

        # 2. LinkedIn (Check before link/url)
        if "linkedin" in h:
            return "LINKEDIN"

        # 3. Expected CTC / Salary (Check before Experience and before Current CTC!)
        if any(k in h for k in ["expected ctc", "exp ctc", "expected salary", "exp salary", "target ctc", "target salary", "desired ctc", "desired salary", "expected comp", "expected package", "expected remuneration"]):
            return "EXPECTED_CTC"
        if "expected" in h and any(c in h for c in ["ctc", "salary", "comp", "remuneration", "package", "lpa", "fixed"]):
            return "EXPECTED_CTC"
        if h.startswith("exp ") and any(c in h for c in ["ctc", "salary", "package", "comp"]):
            return "EXPECTED_CTC"

        # 4. Current CTC / Salary
        if any(k in h for k in ["current ctc", "present ctc", "fixed ctc", "current salary", "present salary", "annual salary", "current comp", "present comp"]):
            return "CURRENT_CTC"
        if any(k in h for k in ["ctc", "salary", "compensation", "remuneration", "package"]) and not any(k in h for k in ["expected", "target", "desired"]):
            return "CURRENT_CTC"

        # 5. Experience Category / Level / Bucket
        if any(k in h for k in ["exp level", "experience level", "experience category", "exp category", "experience bucket", "exp bucket"]):
            return "EXP_BUCKET"

        # 6. Skills (Check specific skills keywords before generic domain keywords)
        if any(k in h for k in ["technical skill", "key skill", "skill", "competenc", "tools", "programming language"]):
            return "SKILLS"

        # 7. Technology Domain / Category / Tech Stack
        if any(k in h for k in ["technology domain", "tech domain", "domain", "technology category", "tech category", "tech stack", "technology"]):
            return "TECH_DOMAIN"

        # 8. Relevant Experience (Check before Total Experience!)
        if any(k in h for k in ["relevant experience", "relevant exp", "rel experience", "rel exp", "related experience"]):
            return "RELEVANT_EXPERIENCE"
        if "relevant" in h and any(k in h for k in ["exp", "experience", "work"]):
            return "RELEVANT_EXPERIENCE"

        # 9. Total Experience / Work Experience
        if any(k in h for k in ["total experience", "total exp", "overall experience", "overall exp", "work experience", "total work experience", "years of experience", "years experience", "experience years", "experience duration"]):
            return "TOTAL_EXPERIENCE"
        if h in ["experience", "exp", "total experience (years)", "experience (years)", "exp (years)", "years of exp"]:
            return "TOTAL_EXPERIENCE"
        if "experience" in h and not any(k in h for k in ["relevant", "rel", "level", "category", "bucket"]):
            return "TOTAL_EXPERIENCE"

        # 10. Preferred Location (Check before Current Location!)
        if any(k in h for k in ["preferred location", "pref location", "target location", "preferred city", "desired location", "relocation"]):
            return "PREFERRED_LOCATION"

        # 11. Current Location
        if any(k in h for k in ["current location", "present location", "current city", "location", "city", "address", "based in", "residence"]):
            return "CURRENT_LOCATION"

        # 12. Candidate Name
        if any(k in h for k in ["candidate name", "full name", "applicant name", "person name"]) or h in ["name", "candidate", "applicant"]:
            return "CANDIDATE_NAME"

        # 13. Mobile / Phone
        if any(k in h for k in ["mobile", "phone", "contact number", "contact no", "cell"]) or h in ["contact"]:
            return "MOBILE_NUMBER"

        # 14. Notice Period / Availability
        if any(k in h for k in ["notice", "availability", "joining"]):
            return "NOTICE_PERIOD"

        # 15. Education
        if any(k in h for k in ["education", "qualification", "degree", "academic", "academics"]):
            return "EDUCATION"

        # 16. Certifications
        if any(k in h for k in ["certif", "course", "certified"]):
            return "CERTIFICATIONS"

        # 17. Remarks
        if any(k in h for k in ["remark", "comment", "note"]):
            return "REMARKS"

        return "UNKNOWN"

    # Step 3: Map LLM output & Fallback Data to Excel headers using concept mapping
    final_dict = {header: "" for header in excel_headers}

    for excel_header in excel_headers:
        concept = classify_header_concept(excel_header)
        found_val = ""

        # 1. Exact or Concept match in LLM output
        for llm_key, value in extracted_dict.items():
            if value is not None and str(value).strip():
                val_str = str(value).strip()
                if val_str.lower() in ["none", "null", "n/a", "na"]:
                    continue
                # Match by exact header name or matching concept
                if llm_key.strip().lower() == excel_header.strip().lower() or classify_header_concept(llm_key) == concept:
                    found_val = val_str
                    break

        # 2. Fallback extraction if LLM value is missing or empty
        if not found_val:
            if concept == "CANDIDATE_NAME":
                found_val = fallback_data.get("Candidate Name", "")
            elif concept == "MOBILE_NUMBER":
                found_val = fallback_data.get("Mobile Number", "")
            elif concept == "EMAIL_ADDRESS":
                found_val = fallback_data.get("Email Address", "")
            elif concept == "SKILLS":
                found_val = fallback_data.get("Skills", "")
            elif concept == "NOTICE_PERIOD":
                found_val = fallback_data.get("Notice Period", "")
            elif concept == "RELEVANT_EXPERIENCE":
                found_val = fallback_data.get("Relevant Experience", "")
            elif concept == "TOTAL_EXPERIENCE":
                found_val = calc_exp
            elif concept == "PREFERRED_LOCATION":
                found_val = fallback_data.get("Preferred Location", "") or fallback_data.get("Current Location", "")
            elif concept == "CURRENT_LOCATION":
                found_val = fallback_data.get("Current Location", "")
            elif concept == "CURRENT_CTC":
                found_val = fallback_data.get("Current CTC", "")
            elif concept == "EXPECTED_CTC":
                found_val = fallback_data.get("Expected CTC", "")
            elif concept == "LINKEDIN":
                found_val = fallback_data.get("LinkedIn Profile", "")
            elif concept == "EDUCATION":
                found_val = fallback_data.get("Education", "")
            elif concept == "CERTIFICATIONS":
                found_val = fallback_data.get("Certifications", "")
            elif concept == "TECH_DOMAIN":
                found_val = ", ".join(classify_technology(cleaned_text))
            elif concept == "EXP_BUCKET":
                found_val = classify_experience(calc_exp, cleaned_text)
            elif concept == "REMARKS":
                found_val = ""

        # 3. Semantic Guardrails & Field-Type Sanitization
        # Rule: EXPECTED CTC & CURRENT CTC must NEVER contain experience values
        if concept in ["EXPECTED_CTC", "CURRENT_CTC"]:
            val_lower = found_val.lower()
            if any(k in val_lower for k in ["fresher", "years", "yrs", "year", "month", "mos", "intern", "entry level"]):
                found_val = ""
            if concept == "EXPECTED_CTC" and found_val:
                # If expected CTC was mistakenly filled with current CTC and no expected keyword in text, clear it
                curr_ctc_val = fallback_data.get("Current CTC", "")
                if found_val == curr_ctc_val and not re.search(r"(?:expected|target|desired)\s*(?:ctc|salary|package)", cleaned_text, re.IGNORECASE):
                    found_val = ""

        # Rule: TOTAL_EXPERIENCE must receive only experience values
        elif concept == "TOTAL_EXPERIENCE":
            val_lower = found_val.lower()
            if any(k in val_lower for k in ["lpa", "lakh", "lac", "ctc", "salary", "inr"]) or not found_val:
                found_val = calc_exp

        # Rule: RELEVANT_EXPERIENCE must receive only experience values
        elif concept == "RELEVANT_EXPERIENCE":
            val_lower = found_val.lower()
            if any(k in val_lower for k in ["lpa", "lakh", "lac", "ctc", "salary", "inr"]):
                found_val = calc_exp

        final_dict[excel_header] = found_val

    # Step 4: Normalize extracted skills
    skills_header = None
    for h in excel_headers:
        if classify_header_concept(h) == "SKILLS":
            skills_header = h
            break

    raw_skills = final_dict.get(skills_header, "") if skills_header else fallback_data.get("Skills", "")
    norm_skills_str, skills_conf = normalize_skills(raw_skills)

    if skills_header and norm_skills_str:
        final_dict[skills_header] = norm_skills_str

    # Step 5: Force computed Experience if header is present and still blank
    for header in excel_headers:
        if classify_header_concept(header) == "TOTAL_EXPERIENCE" and not final_dict[header]:
            final_dict[header] = calc_exp

    # Step 6: Technology & Experience Classifications
    tech_domains = classify_technology(cleaned_text, norm_skills_str)
    tech_domain_str = ", ".join(tech_domains)
    exp_bucket = classify_experience(final_dict.get("Total Experience", calc_exp), cleaned_text)
    screening_res = run_ai_candidate_screening(cleaned_text, final_dict)

    # Populate domain / experience headers
    for header in excel_headers:
        c_concept = classify_header_concept(header)
        if c_concept == "TECH_DOMAIN":
            final_dict[header] = tech_domain_str
        elif c_concept == "EXP_BUCKET" and not final_dict[header]:
            final_dict[header] = exp_bucket

    # Always ensure Technology Domain key is present
    if "Technology Domain" not in final_dict or not final_dict["Technology Domain"]:
        final_dict["Technology Domain"] = tech_domain_str

    # Attach Debugging & Confidence Metadata
    final_dict["_raw_text"] = resume_text
    final_dict["_cleaned_text"] = cleaned_text
    final_dict["_exp_confidence"] = exp_conf
    final_dict["_exp_notes"] = exp_notes
    final_dict["_skills_confidence"] = skills_conf
    final_dict["_tech_domains"] = tech_domains
    final_dict["_exp_bucket"] = exp_bucket
    final_dict["_oracle_exp"] = screening_res["_oracle_exp"]
    final_dict["_suitable_roles"] = screening_res["_suitable_roles"]
    final_dict["_ai_screening_summary"] = screening_res["_ai_screening_summary"]

    return True, final_dict, raw_llm_text, ""
