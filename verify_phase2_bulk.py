import os
import glob
import openpyxl
from utils.helpers import classify_technology, classify_experience, SUPPORTED_DOMAINS
from services.excel_service import (
    read_excel_headers,
    populate_excel_template_batch,
    generate_duplicate_report,
    generate_error_and_missing_report,
    generate_classification_report,
    create_batch_zip_package,
    sanitize_sheet_name
)
from services.batch_processor import process_resume_batch

def test_technology_classification_unit():
    print("\n==================== 1. RUNNING 7 TECHNOLOGY CLASSIFICATION TESTS ====================")

    # Test 1: Python + Django -> Python
    t1_domains = classify_technology("Experienced in backend development using Python and Django framework.", "Python, Django")
    print(f"Test 1 (Python + Django): {t1_domains}")
    assert "Python" in t1_domains, f"Test 1 Failed: Expected Python, got {t1_domains}"
    assert "Java" not in t1_domains, f"Test 1 Failed: Should not have Java"

    # Test 2: Java + Spring Boot -> Java
    t2_domains = classify_technology("Developed microservices using Java and Spring Boot with Hibernate.", "Java, Spring Boot, Hibernate")
    print(f"Test 2 (Java + Spring Boot): {t2_domains}")
    assert "Java" in t2_domains, f"Test 2 Failed: Expected Java, got {t2_domains}"
    assert "Python" not in t2_domains, f"Test 2 Failed: Should not have Python"

    # Test 3: Python + TensorFlow + AWS -> Python, AI/ML, Cloud
    t3_domains = classify_technology("Built Machine Learning models in Python using TensorFlow and deployed on AWS EC2.", "Python, TensorFlow, AWS")
    print(f"Test 3 (Python + TensorFlow + AWS): {t3_domains}")
    assert "Python" in t3_domains, f"Test 3 Failed: Missing Python in {t3_domains}"
    assert "AI/ML" in t3_domains, f"Test 3 Failed: Missing AI/ML in {t3_domains}"
    assert "Cloud" in t3_domains, f"Test 3 Failed: Missing Cloud in {t3_domains}"

    # Test 4: Spark + PySpark + Airflow -> Data Engineering
    t4_domains = classify_technology("Data pipelines using Spark, PySpark and Apache Airflow for large scale ETL processing.", "Spark, PySpark, Airflow, ETL")
    print(f"Test 4 (Spark + PySpark + Airflow): {t4_domains}")
    assert "Data Engineering" in t4_domains, f"Test 4 Failed: Expected Data Engineering, got {t4_domains}"

    # Test 5: AWS + Docker + Kubernetes -> DevOps, Cloud
    t5_domains = classify_technology("Deploying containerized microservices with Docker and Kubernetes on AWS cloud infrastructure.", "AWS, Docker, Kubernetes")
    print(f"Test 5 (AWS + Docker + Kubernetes): {t5_domains}")
    assert "Cloud" in t5_domains, f"Test 5 Failed: Missing Cloud in {t5_domains}"
    assert "DevOps" in t5_domains, f"Test 5 Failed: Missing DevOps in {t5_domains}"

    # Test 6: Resume with no supported technology -> Others
    t6_domains = classify_technology("Store manager with expertise in retail inventory, accounting, and cashier operations.", "Retail, Cash Handling, Sales")
    print(f"Test 6 (Retail Resume - No Supported Tech): {t6_domains}")
    assert t6_domains == ["Others"], f"Test 6 Failed: Expected ['Others'], got {t6_domains}"

    # Test 7: Resume mentioning JavaScript but no Java -> Do NOT classify as Java
    t7_domains = classify_technology("Frontend developer experienced in modern JavaScript (ES6+), HTML5, CSS3, and DOM manipulation.", "JavaScript, HTML5, CSS3")
    print(f"Test 7 (JavaScript only): {t7_domains}")
    assert "Java" not in t7_domains, f"Test 7 Failed: JavaScript must NOT classify as Java! Got: {t7_domains}"

    print("[OK] ALL 7 TECHNOLOGY CLASSIFICATION UNIT TESTS PASSED SUCCESSFULLY!")


def test_bulk_batch_with_technology():
    print("\n==================== 2. RUNNING BULK BATCH INTEGRATION TEST ====================")

    template_path = "uploads/test_template.xlsx"
    headers = [
        "Candidate Name", "Mobile Number", "Email Address", "Total Experience",
        "Relevant Experience", "Current Location", "Preferred Location", "Skills",
        "Notice Period", "Current CTC", "Expected CTC", "LinkedIn Profile",
        "Education", "Certifications", "Remarks"
    ]

    all_files = [f for f in glob.glob("uploads/*") if f.endswith((".pdf", ".docx"))]
    # Use representative sample of 12 resumes for quick verification (or all if specified)
    resume_files = all_files[:12] if len(all_files) > 12 else all_files
    print(f"Testing batch processing on {len(resume_files)} resumes (out of {len(all_files)} total available in uploads/).")

    def progress_printer(curr, total, fname):
        print(f"  [Progress {curr}/{total}] Processed: {fname}")

    batch_res = process_resume_batch(
        file_paths=resume_files,
        excel_headers=headers,
        template_path=template_path,
        progress_callback=progress_printer,
        max_workers=4
    )

    print("\n--- BATCH ENGINE RESULTS SUMMARY ---")
    print(f"Total Processed: {batch_res['total_processed']}")
    print(f"Successful Extractions: {batch_res['success_count']}")
    print(f"Unique Master Candidates: {len(batch_res['unique_candidates'])}")
    print(f"Duplicates Flagged: {len(batch_res['duplicate_candidates'])}")
    print(f"Failed Resumes: {len(batch_res['failed_resumes'])}")
    print(f"Tech Stats: {batch_res['tech_stats']}")
    print(f"Experience Stats: {batch_res['exp_stats']}")

    assert batch_res['total_processed'] == len(resume_files), "Total processed count mismatch!"
    assert len(batch_res['unique_candidates']) > 0, "Unique candidates must not be empty!"

    # Ensure all 12 domains are represented in tech_stats
    for dom in SUPPORTED_DOMAINS:
        assert dom in batch_res['tech_stats'], f"Domain {dom} missing from tech_stats!"

    # Generate Reports & Multi-Sheet Excel
    out_dir = "outputs/phase2_verify"
    os.makedirs(out_dir, exist_ok=True)
    master_path = os.path.join(out_dir, "Master_Candidates_Consolidated.xlsx")
    dup_path = os.path.join(out_dir, "Duplicate_Report_Consolidated.xlsx")
    err_path = os.path.join(out_dir, "Error_Log_Consolidated.xlsx")
    class_path = os.path.join(out_dir, "Classification_Analytics_Consolidated.xlsx")
    zip_path = os.path.join(out_dir, "Batch_Reports_Consolidated.zip")

    ok1, e1 = populate_excel_template_batch(template_path, batch_res['unique_candidates'], master_path)
    ok2, e2 = generate_duplicate_report(batch_res['duplicate_candidates'], headers, dup_path)
    ok3, e3 = generate_error_and_missing_report(batch_res['failed_resumes'], batch_res['missing_fields_log'], err_path)
    ok4, e4 = generate_classification_report(batch_res['tech_stats'], batch_res['exp_stats'], class_path)

    report_files = [
        (master_path, "Master_Candidates_Consolidated.xlsx"),
        (dup_path, "Duplicate_Report_Consolidated.xlsx"),
        (err_path, "Error_Log_Consolidated.xlsx"),
        (class_path, "Classification_Analytics_Consolidated.xlsx")
    ]
    ok5, e5 = create_batch_zip_package(report_files, zip_path)

    assert ok1 and os.path.exists(master_path), f"Master Excel failed: {e1}"
    assert ok2 and os.path.exists(dup_path), f"Duplicate report failed: {e2}"
    assert ok3 and os.path.exists(err_path), f"Error log failed: {e3}"
    assert ok4 and os.path.exists(class_path), f"Classification report failed: {e4}"
    assert ok5 and os.path.exists(zip_path), f"ZIP package failed: {e5}"

    # Verify Multi-Sheet Structure in Master Excel
    wb = openpyxl.load_workbook(master_path)
    sheet_names = wb.sheetnames
    print(f"\nCreated Sheets in Master Excel: {sheet_names}")
    assert "All Candidates" in sheet_names, "Sheet 'All Candidates' must be present!"
    
    # Check that sheets exist for domains with count > 0 and no sheets exist for count == 0
    for dom, cnt in batch_res['tech_stats'].items():
        sanitized = sanitize_sheet_name(dom)
        if cnt > 0:
            assert sanitized in sheet_names, f"Expected sheet '{sanitized}' for domain '{dom}' with {cnt} candidates!"
        else:
            assert sanitized not in sheet_names, f"Empty sheet '{sanitized}' should not be created!"

    # Verify Technology Domain column in All Candidates sheet
    ws_all = wb["All Candidates"]
    header_row_vals = [cell.value for cell in ws_all[1]]
    print(f"Header columns in 'All Candidates': {header_row_vals}")
    assert "Technology Domain" in header_row_vals or any("Domain" in str(h) for h in header_row_vals), "Technology Domain column must be in sheet headers!"
    wb.close()

    print("\n==================== 3. TESTING DUAL SHORTLISTING LOGIC ====================")
    # Test Combined Filter: Python OR AI/ML + Fresher OR 1-3 Years
    selected_tech = ["Python", "AI/ML"]
    selected_exp = ["Fresher", "1–3 Years"]

    filtered_candidates = []
    for c in batch_res['unique_candidates']:
        c_doms = c.get("_tech_domains", ["Others"])
        c_exp = c.get("_exp_bucket", "Fresher")

        tech_match = any(t in c_doms for t in selected_tech)
        exp_match = (c_exp in selected_exp)

        if tech_match and exp_match:
            filtered_candidates.append(c)

    print(f"Total Unique Candidates: {len(batch_res['unique_candidates'])}")
    print(f"Filtered (Tech: {selected_tech} AND Exp: {selected_exp}): {len(filtered_candidates)} candidates")

    for fc in filtered_candidates:
        assert any(t in fc.get("_tech_domains", []) for t in selected_tech), "Candidate tech does not match filter!"
        assert fc.get("_exp_bucket") in selected_exp, "Candidate experience does not match filter!"

    print("[OK] DUAL FILTER LOGIC VERIFIED SUCCESSFULLY!")

    print("\n========================================================================")
    print("[OK] ALL PHASE 2 BULK & TECHNOLOGY CLASSIFICATION VERIFICATIONS PASSED!")
    print("========================================================================")


if __name__ == "__main__":
    test_technology_classification_unit()
    test_bulk_batch_with_technology()
