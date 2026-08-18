import os
import time
from typing import List, Dict, Any, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.resume_parser import parse_resume
from services.llm_service import extract_candidate_data
import services.duplicate_detector as dup_det
from services.excel_service import read_existing_candidate_rows

def process_single_resume_worker(file_path: str, excel_headers: List[str]) -> Dict[str, Any]:
    """
    Worker function to process a single resume file.
    Returns dictionary with execution results.
    """
    filename = os.path.basename(file_path)
    try:
        ok, text, err = parse_resume(file_path)
        if not ok:
            return {
                "success": False,
                "file_path": file_path,
                "filename": filename,
                "error": err,
                "candidate_data": {}
            }

        ok_llm, cand_data, raw_llm, err_llm = extract_candidate_data(text, excel_headers)
        if not ok_llm:
            return {
                "success": False,
                "file_path": file_path,
                "filename": filename,
                "error": err_llm,
                "candidate_data": {}
            }

        cand_data["_filename"] = filename
        cand_data["_file_path"] = file_path

        return {
            "success": True,
            "file_path": file_path,
            "filename": filename,
            "error": "",
            "candidate_data": cand_data
        }
    except Exception as e:
        return {
            "success": False,
            "file_path": file_path,
            "filename": filename,
            "error": f"Unexpected processing exception: {str(e)}",
            "candidate_data": {}
        }


def process_resume_batch(
    file_paths: List[str],
    excel_headers: List[str],
    template_path: str = None,
    progress_callback: Callable[[int, int, str], None] = None,
    max_workers: int = 4
) -> Dict[str, Any]:
    """
    Process multiple resumes in parallel.
    Detects duplicates, logs errors/missing fields, and classifies candidates.

    Returns dict containing:
        - unique_candidates: List[Dict]
        - duplicate_candidates: List[Dict]
        - failed_resumes: List[Dict]
        - missing_fields_log: List[Dict]
        - tech_stats: Dict[str, int]
        - exp_stats: Dict[str, int]
        - total_processed: int
    """
    total_files = len(file_paths)
    processed_count = 0

    results = []

    # Process in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(max_workers, total_files or 1)) as executor:
        future_to_file = {
            executor.submit(process_single_resume_worker, fp, excel_headers): fp
            for fp in file_paths
        }

        for future in as_completed(future_to_file):
            res = future.result()
            results.append(res)
            processed_count += 1

            if progress_callback:
                progress_callback(processed_count, total_files, res["filename"])

    # Collect successful candidates & failures
    successful_candidates = []
    failed_resumes = []
    missing_fields_log = []

    for r in results:
        if r["success"]:
            c_data = r["candidate_data"]
            successful_candidates.append(c_data)

            # Check missing key fields (Name, Mobile, Email)
            missing = []
            for h in excel_headers:
                val = str(c_data.get(h, "")).strip()
                if not val:
                    missing.append(h)

            if missing:
                missing_fields_log.append({
                    "Filename": r["filename"],
                    "Candidate Name": c_data.get("Candidate Name") or c_data.get("Name", "Unknown"),
                    "Missing Fields Count": len(missing),
                    "Missing Field Names": ", ".join(missing)
                })
        else:
            failed_resumes.append({
                "Filename": r["filename"],
                "Error": r["error"]
            })

    # Existing template records for duplicate check
    existing_records = []
    if template_path and os.path.exists(template_path):
        existing_records = read_existing_candidate_rows(template_path)

    # Run duplicate detection across current batch & template records
    unique_candidates, duplicate_candidates = dup_det.check_duplicate_batch(successful_candidates, existing_records)

    # Compute Classification Statistics
    tech_stats = {
        "Java": 0, "Python": 0, "Oracle": 0, "Data Engineering": 0,
        "AI/ML": 0, "DevOps": 0, "Salesforce": 0, "SAP": 0,
        "Testing": 0, "Full Stack": 0, "Cloud": 0, "Others": 0
    }
    exp_stats = {
        "Fresher": 0, "1–3 Years": 0, "3–5 Years": 0, "5–8 Years": 0, "8+ Years": 0
    }

    for c in unique_candidates:
        domains = c.get("_tech_domains", ["Others"])
        for d in domains:
            if d in tech_stats:
                tech_stats[d] += 1
            else:
                tech_stats["Others"] += 1

        bucket = c.get("_exp_bucket", "Fresher")
        if bucket in exp_stats:
            exp_stats[bucket] += 1
        else:
            exp_stats["Fresher"] += 1

    return {
        "unique_candidates": unique_candidates,
        "duplicate_candidates": duplicate_candidates,
        "failed_resumes": failed_resumes,
        "missing_fields_log": missing_fields_log,
        "tech_stats": tech_stats,
        "exp_stats": exp_stats,
        "total_processed": total_files,
        "success_count": len(successful_candidates)
    }
