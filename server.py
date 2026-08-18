import os
import time
import shutil
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.llm_service import check_ollama_status, extract_candidate_data, OLLAMA_MODEL, OLLAMA_URL
from services.resume_parser import parse_resume
from services.excel_service import (
    read_excel_headers,
    read_existing_candidate_rows,
    populate_excel_template,
    populate_excel_template_batch,
    generate_duplicate_report,
    generate_error_and_missing_report,
    generate_classification_report,
    create_batch_zip_package
)
from services.duplicate_detector import check_duplicate
from services.batch_processor import process_resume_batch

app = FastAPI(
    title="AI-Powered Resume Processing System API",
    description="REST API for automated candidate screening, batch resume processing, dynamic Excel population, and report generation.",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
OUTPUT_DIR = os.path.join(os.getcwd(), "outputs")
FRONTEND_DIST = os.path.join(os.getcwd(), "frontend", "dist")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.get("/api/status")
def get_system_status():
    """Check Ollama connectivity and return system info."""
    is_online, status_msg, available_models = check_ollama_status()
    return {
        "is_online": is_online,
        "status_msg": status_msg,
        "available_models": available_models,
        "ollama_url": OLLAMA_URL,
        "target_model": OLLAMA_MODEL
    }


@app.post("/api/upload-template")
async def upload_template(file: UploadFile = File(...)):
    """Upload Excel column template and extract headers."""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx Excel files are supported.")
    
    template_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(template_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    success, headers, error_msg = read_excel_headers(template_path)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to read headers: {error_msg}")
        
    return {
        "filename": file.filename,
        "headers": headers,
        "count": len(headers)
    }


@app.post("/api/process-single")
async def process_single_resume(
    resume: UploadFile = File(...),
    template: UploadFile = File(...)
):
    """Process a single resume against an Excel column template."""
    is_online, status_msg, _ = check_ollama_status()
    if not is_online:
        raise HTTPException(status_code=503, detail=f"Ollama offline: {status_msg}")

    # Save resume
    resume_path = os.path.join(UPLOAD_DIR, resume.filename)
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

    # Save template
    template_path = os.path.join(UPLOAD_DIR, template.filename)
    with open(template_path, "wb") as buffer:
        shutil.copyfileobj(template.file, buffer)

    # Read template headers
    success_hdr, headers, hdr_err = read_excel_headers(template_path)
    if not success_hdr:
        raise HTTPException(status_code=400, detail=f"Template header error: {hdr_err}")

    # Step 1: Parse resume text
    parsed_ok, resume_text, parse_err = parse_resume(resume_path)
    if not parsed_ok:
        raise HTTPException(status_code=400, detail=f"Resume parsing error: {parse_err}")

    # Step 2: Extract candidate data with LLM
    llm_ok, candidate_data, raw_llm, llm_err = extract_candidate_data(resume_text, headers)
    if not llm_ok:
        raise HTTPException(status_code=500, detail=f"AI extraction error: {llm_err}")

    # Step 3: Check duplicate against existing template records
    existing_records = read_existing_candidate_rows(template_path)
    is_dup, dup_warning, dup_details = check_duplicate(candidate_data, existing_records)

    # Step 4: Populate output Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate_name_clean = str(candidate_data.get("Candidate Name", "Candidate")).replace(" ", "_")
    output_filename = f"Processed_{candidate_name_clean}_{timestamp}.xlsx"
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)

    pop_ok, pop_err = populate_excel_template(template_path, candidate_data, output_filepath)
    if not pop_ok:
        raise HTTPException(status_code=500, detail=f"Excel population error: {pop_err}")

    # Build response data structures
    extracted_fields = []
    missing_fields = []
    for h in headers:
        val = candidate_data.get(h, "")
        if val != "" and val is not None and str(val).strip():
            extracted_fields.append({"column": h, "value": str(val).strip(), "status": "Extracted"})
        else:
            extracted_fields.append({"column": h, "value": "(Blank)", "status": "Missing / Blank"})
            missing_fields.append(h)

    return {
        "candidate_name": candidate_data.get("Candidate Name", "Unknown"),
        "is_duplicate": is_dup,
        "duplicate_warning": dup_warning if is_dup else None,
        "duplicate_details": dup_details if is_dup else None,
        "tech_domains": candidate_data.get("_tech_domains", ["Others"]),
        "exp_bucket": candidate_data.get("_exp_bucket", "Fresher"),
        "ai_screening": {
            "summary": candidate_data.get("_ai_screening_summary", "N/A"),
            "oracle_exp": candidate_data.get("_oracle_exp", "No"),
            "suitable_roles": candidate_data.get("_suitable_roles", "General Tech Role")
        },
        "diagnostics": {
            "exp_confidence": candidate_data.get("_exp_confidence", 0),
            "exp_notes": candidate_data.get("_exp_notes", "N/A"),
            "skills_confidence": candidate_data.get("_skills_confidence", 0),
            "cleaned_text": candidate_data.get("_cleaned_text", ""),
            "raw_text": candidate_data.get("_raw_text", "")
        },
        "extracted_fields": extracted_fields,
        "missing_fields": missing_fields,
        "output_filename": output_filename,
        "download_url": f"/api/download/{output_filename}"
    }


@app.post("/api/process-batch")
async def process_batch_resumes(
    template: UploadFile = File(...),
    resumes: List[UploadFile] = File(...)
):
    """Process multiple resumes in parallel and generate comprehensive report files."""
    if not resumes:
        raise HTTPException(status_code=400, detail="No resume files uploaded.")

    # Save template
    template_path = os.path.join(UPLOAD_DIR, template.filename)
    with open(template_path, "wb") as buffer:
        shutil.copyfileobj(template.file, buffer)

    success_hdr, headers, hdr_err = read_excel_headers(template_path)
    if not success_hdr:
        raise HTTPException(status_code=400, detail=f"Excel template error: {hdr_err}")

    # Save resume files
    file_paths = []
    for r in resumes:
        save_p = os.path.join(UPLOAD_DIR, r.filename)
        with open(save_p, "wb") as buffer:
            shutil.copyfileobj(r.file, buffer)
        file_paths.append(save_p)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_t = time.time()

    # Process batch
    batch_output = process_resume_batch(
        file_paths=file_paths,
        excel_headers=headers,
        template_path=template_path,
        progress_callback=None,
        max_workers=4
    )
    elapsed_sec = round(time.time() - start_t, 2)

    # Generate Output Files
    master_fname = f"Master_Candidates_{timestamp}.xlsx"
    dup_fname = f"Duplicate_Report_{timestamp}.xlsx"
    err_fname = f"Error_Log_{timestamp}.xlsx"
    class_fname = f"Classification_Analytics_{timestamp}.xlsx"
    zip_fname = f"Batch_Reports_{timestamp}.zip"

    master_path = os.path.join(OUTPUT_DIR, master_fname)
    dup_path = os.path.join(OUTPUT_DIR, dup_fname)
    err_path = os.path.join(OUTPUT_DIR, err_fname)
    class_path = os.path.join(OUTPUT_DIR, class_fname)
    zip_path = os.path.join(OUTPUT_DIR, zip_fname)

    populate_excel_template_batch(template_path, batch_output["unique_candidates"], master_path)
    generate_duplicate_report(batch_output["duplicate_candidates"], headers, dup_path)
    generate_error_and_missing_report(batch_output["failed_resumes"], batch_output["missing_fields_log"], err_path)
    generate_classification_report(batch_output["tech_stats"], batch_output["exp_stats"], class_path)

    report_files = [
        (master_path, master_fname),
        (dup_path, dup_fname),
        (err_path, err_fname),
        (class_path, class_fname)
    ]
    create_batch_zip_package(report_files, zip_path)

    return {
        "elapsed_seconds": elapsed_sec,
        "total_processed": batch_output["total_processed"],
        "unique_count": len(batch_output["unique_candidates"]),
        "duplicate_count": len(batch_output["duplicate_candidates"]),
        "failed_count": len(batch_output["failed_resumes"]),
        "headers": headers,
        "unique_candidates": batch_output["unique_candidates"],
        "duplicate_candidates": batch_output["duplicate_candidates"],
        "failed_resumes": batch_output["failed_resumes"],
        "missing_fields_log": batch_output["missing_fields_log"],
        "tech_stats": batch_output["tech_stats"],
        "exp_stats": batch_output["exp_stats"],
        "downloads": {
            "master_excel": f"/api/download/{master_fname}",
            "duplicate_report": f"/api/download/{dup_fname}",
            "error_log": f"/api/download/{err_fname}",
            "classification_analytics": f"/api/download/{class_fname}",
            "zip_package": f"/api/download/{zip_fname}"
        }
    }


@app.get("/api/download/{filename}")
def download_file(filename: str):
    """Download output report file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        # Also check upload directory if requested
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Requested file not found.")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )

# Mount React static frontend dist directory at root
if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
