# AI-Powered Resume Processing System

A high-performance, enterprise-ready automated resume screening, extraction, and candidate classification platform powered by **Groq Cloud LLM** (`groq/compound-mini` / `llama-3.3-70b-versatile`), Streamlit, Python, FastAPI, and React.

---

## 🎯 Project Purpose & Overview

Recruitment teams face significant administrative overhead manually reviewing candidate resumes, extracting personal & technical details, checking for duplicates, and compiling spreadsheet trackers. 

This platform automates the end-to-end HR resume ingestion workflow:
1. **Automated Data Extraction**: Extracts candidate name, mobile number, email address, total & relevant experience, location preferences, technical skills, notice period, current & expected CTC, education, and certifications with high-precision AI mapping.
2. **Dynamic Excel Template Mapping**: Automatically parses custom Excel template column headers (Row 1) and dynamically maps extracted fields without fixed layout dependencies.
3. **Parallel Bulk Processing**: Processes batches of 30+ candidate resumes concurrently with multi-worker execution and real-time progress indicators.
4. **Technology Domain Classification**: Automatically classifies candidates into 12 tech domains (Java, Python, Oracle, Data Engineering, AI/ML, DevOps, Salesforce, SAP, Testing, Full Stack, Cloud, Others) with dual-shortlisting filter controls.
5. **Smart Duplicate Detection**: Scans incoming resumes against existing template rows to flag duplicate candidates by email, phone, or name matching.
6. **Consolidated Excel & Report Packaging**: Generates multi-sheet Master Excel workbooks, Duplicate Reports, Error/Missing Info Logs, Classification Analytics, and one-click ZIP download packages.

---

## ✨ Key Features

- **Multi-Mode UI**: Supports both **⚡ Bulk Batch Processing (30+ Resumes)** and **🚀 Single Resume Processing**.
- **Groq Cloud AI Acceleration**: Powered by Groq Cloud API for ultra-fast Llama-3 inference and structured JSON extraction.
- **Deterministic Guardrails**: Combines AI extraction with date-range experience calculation and regex skill normalization.
- **Dual-Shortlisting Engine**: Interactively filter candidates by technology domain and experience level.
- **Automated AI Candidate Screening**: Evaluates candidate suitability and generates screening Q&A summaries.
- **Multi-Report Excel Generation**: Auto-generates Master Excel, Flagged Duplicates Report, Error & Missing Info Log, and Technology Analytics.

---

## 💻 Technologies Used

- **AI/LLM Provider**: Groq Cloud API (`groq/compound-mini`, `llama-3.3-70b-versatile`)
- **Frontend & App Framework**: Streamlit (Web App), React (Vite + Tailwind CSS)
- **Backend & REST API**: FastAPI, Uvicorn
- **Document Parsing**: PyMuPDF (PDF), python-docx (DOCX)
- **Data & Excel Processing**: Pandas, OpenPyXL
- **Language & Runtime**: Python 3.10+

---

## 🔒 Groq Cloud API Integration & Secure Key Configuration

The system connects to Groq Cloud LLM for intelligent candidate screening and data extraction.

### Security Architecture
- **Streamlit Secrets Support**: When deployed on **Streamlit Community Cloud**, the application reads the API key securely via `st.secrets["GROQ_API_KEY"]`.
- **Environment Fallback**: For local development, keys are loaded from `.env` via `load_dotenv()`.
- **Zero API Key Exposure**: API key values are never displayed in UI text, logs, error outputs, or source repositories.
- **Git Protection**: `.env` is listed in `.gitignore` and is strictly untracked in Git.

#### Setting up your API key locally:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your Groq API key (obtainable from [https://console.groq.com/keys](https://console.groq.com/keys)):
   ```ini
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=groq/compound-mini
   ```

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.10+ installed
- Virtual environment recommended (`python -m venv venv`)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Streamlit Application (Primary HR Interface)
```bash
streamlit run app.py
```
Access in browser at: `http://localhost:8501`

### 3. (Optional) Launch Full-Stack FastAPI + React Server
```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```
Access in browser at: `http://127.0.0.1:8000`

---

## ☁️ How to Deploy on Streamlit Community Cloud

1. **Push Repository to GitHub**: Ensure `.env` is **NOT** committed (`.gitignore` protects it).
2. **Log into Streamlit Cloud**: Go to [https://share.streamlit.io](https://share.streamlit.io) and connect your GitHub account.
3. **Deploy New App**:
   - **Repository**: `your-username/your-repo-name`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **Configure Secrets**:
   - In Streamlit Cloud App Settings -> **Secrets**, paste:
     ```toml
     GROQ_API_KEY = "your_groq_api_key_here"
     GROQ_MODEL = "groq/compound-mini"
     ```
5. **Deploy**: Click **Deploy**. Streamlit Cloud will build the app and load secrets automatically.

---

## 🛡️ Important Security Notes

- **Never Commit Secrets**: Never place real API key strings inside code files or commit `.env` to public version control.
- **Repository Safety**: Always verify `.gitignore` contains `.env` before pushing changes.
- **Error Protection**: Sanitization guardrails automatically mask authorization tokens in runtime tracebacks.
