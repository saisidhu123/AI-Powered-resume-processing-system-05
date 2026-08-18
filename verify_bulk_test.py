import os
import glob
from services.excel_service import (
    read_excel_headers,
    populate_excel_template_batch,
    generate_duplicate_report,
    generate_error_and_missing_report,
    generate_classification_report,
    create_batch_zip_package
)
from services.batch_processor import process_resume_batch

def test_bulk_batch_system():
    print("\n==================== VERIFY BULK BATCH PROCESSING ====================")
    
    template_path = "uploads/test_template.xlsx"
    headers = [
        "Candidate Name", "Mobile Number", "Email Address", "Total Experience",
        "Relevant Experience", "Current Location", "Preferred Location", "Skills",
        "Notice Period", "Current CTC", "Expected CTC", "LinkedIn Profile",
        "Education", "Certifications", "Remarks"
    ]

    resume_files = [f for f in glob.glob("uploads/*") if f.endswith((".pdf", ".docx"))]
    print(f"Found {len(resume_files)} test resumes in uploads/ directory.")

    start_time = os.times().user
    
    def progress_printer(curr, total, fname):
        print(f"  [Worker Progress {curr}/{total}] Processed: {fname}")

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

    # Assertions
    assert batch_res['total_processed'] == len(resume_files), "Total processed count mismatch!"
    assert len(batch_res['unique_candidates']) > 0, "Unique candidates must not be empty!"

    # Generate Reports
    out_dir = "outputs/bulk_test"
    master_path = os.path.join(out_dir, "Master_Candidates_Bulk.xlsx")
    dup_path = os.path.join(out_dir, "Duplicate_Report_Bulk.xlsx")
    err_path = os.path.join(out_dir, "Error_Log_Bulk.xlsx")
    class_path = os.path.join(out_dir, "Classification_Analytics_Bulk.xlsx")
    zip_path = os.path.join(out_dir, "Batch_Reports_Bulk.zip")

    ok1, e1 = populate_excel_template_batch(template_path, batch_res['unique_candidates'], master_path)
    ok2, e2 = generate_duplicate_report(batch_res['duplicate_candidates'], headers, dup_path)
    ok3, e3 = generate_error_and_missing_report(batch_res['failed_resumes'], batch_res['missing_fields_log'], err_path)
    ok4, e4 = generate_classification_report(batch_res['tech_stats'], batch_res['exp_stats'], class_path)

    report_files = [
        (master_path, "Master_Candidates_Bulk.xlsx"),
        (dup_path, "Duplicate_Report_Bulk.xlsx"),
        (err_path, "Error_Log_Bulk.xlsx"),
        (class_path, "Classification_Analytics_Bulk.xlsx")
    ]
    ok5, e5 = create_batch_zip_package(report_files, zip_path)

    assert ok1 and os.path.exists(master_path), f"Master Excel failed: {e1}"
    assert ok2 and os.path.exists(dup_path), f"Duplicate report failed: {e2}"
    assert ok3 and os.path.exists(err_path), f"Error log failed: {e3}"
    assert ok4 and os.path.exists(class_path), f"Classification report failed: {e4}"
    assert ok5 and os.path.exists(zip_path), f"ZIP package failed: {e5}"

    print(f"\n[OK] Master Excel Created: {master_path} ({os.path.getsize(master_path)} bytes)")
    print(f"[OK] Duplicate Report Created: {dup_path} ({os.path.getsize(dup_path)} bytes)")
    print(f"[OK] Error Log Created: {err_path} ({os.path.getsize(err_path)} bytes)")
    print(f"[OK] Classification Report Created: {class_path} ({os.path.getsize(class_path)} bytes)")
    print(f"[OK] ZIP Package Created: {zip_path} ({os.path.getsize(zip_path)} bytes)")

    print("\n[OK] BULK BATCH PROCESSING VERIFICATION SUCCESSFUL!")

if __name__ == "__main__":
    test_bulk_batch_system()
