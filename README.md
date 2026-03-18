# 🤖 Zecpath AI System

> Autonomous AI-powered hiring intelligence pipeline — from resume ingestion to final candidate decision.



---

## 📌 Overview

**Zecpath AI** is a fully automated hiring intelligence system that streamlines the entire recruitment process using AI and machine learning.

It automatically:
- 📄 Ingests and parses resumes (PDF & DOCX)
- 📋 Analyzes and understands job descriptions
- 🎯 Screens and ranks candidates using ATS scoring
- 🧠 Evaluates candidates through AI-powered interview analysis
- ✅ Delivers final hiring decisions with intelligent scoring

---

## 📁 Project Structure
```
ZECPATH-AI/
│
├── ats_engine/                → ATS scoring & intelligence
├── data/                      → Raw resumes & JD input data
├── extraction_output/         → Parsed & extracted results
├── interview_ai/              → AI interview evaluation engine
├── job_description_engine/    → JD parsing & requirement analysis
├── logs/                      → System & application logs
├── output/                    → Final ranked candidate output
├── resume_ingestion/          → Resume ingestion & parsing (PDF/DOCX)
├── samples/                   → Sample resumes & job descriptions
├── scoring/                   → Final candidate decision engine
├── screening_ai/              → AI-powered candidate screening
├── sectioning/                → Document sectioning & segmentation
├── tests/                     → Automated test suite
├── utils/                     → Logging, config & helper utilities
├── venv/                      → Virtual environment
│
├── .gitignore
├── main.py                    → Main entry point
├── README.md
└── requirements.txt
```

---

## 🧠 Features

- ✅ **Resume Parsing** — Extracts structured data from PDF and DOCX resumes
- ✅ **JD Analysis** — Parses job descriptions and identifies key requirements
- ✅ **ATS Scoring** — Matches candidates against job requirements intelligently
- ✅ **AI Screening** — Ranks candidates using transformer-based NLP models
- ✅ **Document Sectioning** — Segments resumes into structured sections
- ✅ **Interview Evaluation** — AI-powered scoring of interview responses
- ✅ **Final Decision Engine** — Automated hiring decision and candidate ranking
- ✅ **Structured Output** — Clean JSON output for every pipeline stage
- ✅ **Logging** — Full pipeline traceability using Loguru
- ✅ **REST API** — FastAPI endpoints for seamless system integration

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.8+ |
| **API Framework** | FastAPI + Uvicorn |
| **AI / NLP** | HuggingFace Transformers, spaCy |
| **Deep Learning** | PyTorch |
| **Data Processing** | Pandas, NumPy, Scikit-learn |
| **Resume Parsing** | pdfplumber, python-docx |
| **Validation** | Pydantic |
| **Logging** | Loguru |
| **Testing** | Pytest |
| **Config** | python-dotenv |

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/yourusername/zecpath-ai.git
cd zecpath-ai
```

**2. Create virtual environment**
```bash
python -m venv venv
```

**3. Activate virtual environment**

On Windows:
```bash
venv\Scripts\activate
```
On Mac/Linux:
```bash
source venv/bin/activate
```

**4. Install dependencies**
```bash
pip install -r requirements.txt
```


**6. Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

---

## 🚀 Usage

**Run the main pipeline**
```bash
python main.py
```



## 🧪 Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_parser.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

---

## 📊 Pipeline Flow
```
Resume (PDF/DOCX)          Job Description
       │                          │
       ▼                          ▼
resume_ingestion/      job_description_engine/
       │                          │
       ▼                          ▼
   sectioning/              extraction_output/
       │                          │
       └──────────┬───────────────┘
                  ▼
            ats_engine/
                  │
                  ▼
           screening_ai/
                  │
                  ▼
           interview_ai/
                  │
                  ▼
              scoring/
                  │
                  ▼
              output/
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your branch
```bash
git checkout -b feature/your-feature
```
3. Commit your changes
```bash
git commit -m "Add your feature"
```
4. Push to the branch
```bash
git push origin feature/your-feature
```
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

