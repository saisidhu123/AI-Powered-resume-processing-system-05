import os
from services.field_extractor import (
    clean_and_reconstruct_text,
    normalize_skills,
    calculate_experience_from_dates
)
from services.llm_service import extract_candidate_data

def run_fixes_test():
    print("\n==================== VERIFYING FIXES (EXPERIENCE & SKILLS) ====================")

    # 1. Test Word Reconstruction & Character Regex Fix
    sample_corrupted_skills = "R tr iva A gm n d Gn ra ion, Promp Engin ring, Rea ct.js, Fast API, Py Thon"
    cleaned = clean_and_reconstruct_text(sample_corrupted_skills)
    norm_skills, conf = normalize_skills(cleaned)

    print("\n--- 1. Testing Skill Word Reconstruction & Normalization ---")
    print(f"Input Corrupted Skills: {sample_corrupted_skills}")
    print(f"Cleaned Text: {cleaned}")
    print(f"Normalized Output: {norm_skills}")
    print(f"Confidence Score: {conf}%")

    assert "Retrieval" in norm_skills or "RAG" in norm_skills, "Retrieval Augmented Generation must be reconstructed!"
    assert "Prompt Engineering" in norm_skills, "Prompt Engineering must be reconstructed!"
    assert "React.js" in norm_skills, "React.js must be reconstructed!"
    assert "FastAPI" in norm_skills, "FastAPI must be reconstructed!"
    assert "Python" in norm_skills, "Python must be reconstructed!"
    print("[OK] Skill Word Reconstruction Test Passed!")

    # 2. Test Date Range Experience Calculation
    sample_resume_with_dates = """
    SAISIDHU VEMULAPALLY
    Phone: 9381400974
    Email: saisidhu5558@gmail.com

    SUMMARY:
    AI & Python Developer specializing in LLM applications.

    WORK EXPERIENCE:
    Lead AI Engineer - Acme Tech (Nov 2022 - Present)
    - Built FastAPI backends and LangChain RAG pipelines.

    Software Developer - Global Corp (Jan 2020 - Oct 2022)
    - Developed Python web applications and SQL databases.

    EDUCATION:
    B.Tech CSE (2018 - 2022) | Malla Reddy Institute of Technology
    """

    print("\n--- 2. Testing Date Range Experience Calculation ---")
    exp_formatted, exp_conf, exp_log = calculate_experience_from_dates(sample_resume_with_dates)
    print(f"Calculated Experience: {exp_formatted}")
    print(f"Confidence Score: {exp_conf}%")
    print(f"Calculation Log: {exp_log}")

    assert exp_formatted != "Fresher", "Candidate with 5+ years work experience must NOT be classified as Fresher!"
    assert "Years" in exp_formatted, f"Experience should be formatted in years, got '{exp_formatted}'"
    print("[OK] Date Range Experience Calculation Test Passed!")

    print("\n[OK] ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_fixes_test()
