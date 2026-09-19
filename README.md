# 🔬 AI Research Copilot

An intelligent, full-stack research copilot designed to help researchers ingest, read, analyze, compare, and synthesize academic papers with citation-backed AI assistance using **Flask**, **Google Gemini 2.5 Flash**, **ChromaDB**, and modern web technologies.

---

## ✨ Features

- 📑 **Dual Ingestion Engine**:
  - **Local PDF Upload**: Drag-and-drop research PDFs; extracts text, academic headings (*Abstract, Methods, Results, Discussion, References*), and page numbers using PyMuPDF.
  - **arXiv Live Search & Ingestion**: Query arXiv API by keyword or paper ID (e.g., `2312.00752`) with one-click metadata retrieval and PDF downloading.
- 🧠 **Citation-Grounded AI Copilot**:
  - Powered by Google Gemini 2.5 Flash using the official `google-genai` SDK.
  - Strict academic grounding: Answers cite exact page numbers `[Page X]` or `[Section, Page X]`.
  - Server-Sent Events (SSE) streaming for real-time word-by-word responses.
- 📖 **Split-Screen Reader Workspace**:
  - **Left Pane**: In-browser PDF preview with direct page jump controls and download options.
  - **Right Pane**: Interactive AI Copilot with quick action chips (*Summarize*, *Methodology*, *Limitations*, *Math*), live Markdown parsing, and KaTeX LaTeX math formula rendering.
  - **Synchronized Citations**: Clicking any citation badge `[Page 4]` in an AI response automatically scrolls the PDF to that exact page.
  - **BibTeX Exporter**: 1-click formatted citation generation with clipboard copy.
- 📊 **Comparative Literature Matrix**:
  - Cross-compare 2+ papers side-by-side across:
    1. Research Objective & Problem
    2. Proposed Methodology & Architecture
    3. Datasets & Benchmarks
    4. Key Quantitative Results
    5. Novel Strengths
    6. Limitations & Gaps
  - Export comparative review tables to **Markdown** or **CSV**.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask 3.1, Flask-CORS, PyMuPDF (fitz), ChromaDB, Google GenAI SDK (`google-genai`), Requests, Pydantic, python-dotenv.
- **Frontend**: HTML5, Tailwind CSS, Lucide Icons, Marked.js, KaTeX (LaTeX Math), Server-Sent Events (SSE).

---

## 🚀 Quick Start

### 1. Clone & Setup
```powershell
git clone https://github.com/YOUR_USERNAME/ai-research-copilot.git
cd ai-research-copilot
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the `.env.example` template:
```powershell
Copy-Item .env.example .env
```
Open `.env` and add your Google Gemini API key:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

### 4. Run the Application
```powershell
python run.py
```
Open your browser to: **http://127.0.0.1:5000**

---

## 📁 Directory Structure

```
ai-research-copilot/
├── app/
│   ├── __init__.py               # Flask application factory & CORS setup
│   ├── config.py                 # Configuration paths & environment variables
│   ├── models.py                 # Paper metadata & persistent store
│   ├── routes/
│   │   ├── __init__.py           # HTML view routes (/, /matrix, /reader/<id>, /about)
│   │   ├── papers.py             # Paper upload, arXiv search & PDF serving
│   │   ├── chat.py               # RAG streaming chat & BibTeX endpoints
│   │   └── synthesis.py          # Multi-paper comparative literature matrix
│   ├── services/
│   │   ├── pdf_parser.py         # PyMuPDF section extraction & chunker
│   │   ├── arxiv_client.py       # arXiv API search & downloader
│   │   ├── vector_store.py       # ChromaDB vector indexing & similarity search
│   │   ├── gemini_service.py     # Gemini 2.5 Flash RAG & streaming engine
│   │   └── citation_service.py   # BibTeX citation generation
│   ├── static/
│   │   ├── css/style.css         # Glassmorphism & custom scrollbars
│   │   └── js/
│   │       ├── app.js            # Dashboard, upload & arXiv client
│   │       ├── reader.js         # Streaming chat, PDF jump & KaTeX parser
│   │       └── matrix.js         # Literature matrix & Markdown/CSV export
│   └── templates/
│       ├── base.html             # Shared layout with navbar & toast alerts
│       ├── index.html            # Paper Library dashboard & Ingestion modal
│       ├── reader.html           # Split-screen PDF reader & Copilot chat
│       ├── matrix.html           # Multi-paper comparative analysis view
│       └── about.html            # System documentation & usage guide
├── data/
│   ├── pdfs/                     # Stored PDF documents
│   └── vectordb/                 # Persistent ChromaDB vector index
├── .env.example                  # Environment variable template
├── .gitignore                    # Git exclude file (venv, .env, data)
├── requirements.txt              # Project dependencies
├── run.py                        # Entry point
├── info.txt                      # Architecture plan & milestone tracker
└── README.md                     # Documentation
```
