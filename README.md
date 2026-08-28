# AI-Powered Resume Processing System

An intelligent, full-stack automated resume screening, extraction, and batch-processing system powered by Groq Cloud LLM (`llama-3.3-70b-versatile`), FastAPI, Streamlit, and React (Vite + Tailwind CSS).

---

## 🚀 Quick Start Guide

You have two user interface options to access and use the system:

### Option 1: Full-Stack React + FastAPI Web Application (Recommended)

1. **Start the FastAPI server** (which automatically serves the built React frontend):
   ```bash
   python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Access in your browser**:
   👉 [http://localhost:8000](http://localhost:8000)

---

### Option 2: Streamlit Interactive UI

1. **Start the Streamlit application**:
   ```bash
   streamlit run app.py
   ```
2. **Access in your browser**:
   👉 [http://localhost:8501](http://localhost:8501)

---

## 🛠️ Prerequisites & Environment Setup

1. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Groq API Configuration**:
   - Obtain a free API key from [https://console.groq.com/keys](https://console.groq.com/keys).
   - Set environment variable in `.env` (for local development) or **Streamlit Secrets** (for Streamlit Community Cloud deployment):
     ```ini
     GROQ_API_KEY=your_groq_api_key_here
     GROQ_MODEL=llama-3.3-70b-versatile
     ```

---


## 📁 Key Files & Directories

- [server.py](file:///c:/Users/nag93/Downloads/AI-Powered%20resume%20processing%20system%2005/server.py) — FastAPI REST Backend & static React server.
- [app.py](file:///c:/Users/nag93/Downloads/AI-Powered%20resume%20processing%20system%2005/app.py) — Streamlit Interactive Web Application.
- [frontend/](file:///c:/Users/nag93/Downloads/AI-Powered%20resume%20processing%20system%2005/frontend) — React + Tailwind CSS + Vite Frontend.
- [services/](file:///c:/Users/nag93/Downloads/AI-Powered%20resume%20processing%20system%2005/services) — Core business logic (resume parsing, field extraction, LLM communication, Excel generation, duplicate detection).
- [utils/](file:///c:/Users/nag93/Downloads/AI-Powered%20resume%20processing%20system%2005/utils) — Helper functions, skill dictionaries, regex normalizers.
- [verify_test.py](file:///c:/Users/nag93/Downloads/AI-Powered%20resume%20processing%20system%2005/verify_test.py) — End-to-end integration test suite.
