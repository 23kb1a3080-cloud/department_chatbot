# 🎓 NBKR Institute AI & DS Department RAG Chatbot

An intelligent chatbot for the **AI & Data Science Department** at NBKR Institute of Science & Technology, powered by **RAG (Retrieval-Augmented Generation)** + **NLP (spaCy)**.

---

## 🚀 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI + WebSocket |
| **AI / RAG** | Sentence Transformers + FAISS |
| **NLP** | spaCy (en_core_web_sm) |
| **Vector DB** | ChromaDB |
| **Web Scraping** | Playwright + BeautifulSoup |
| **PDF Processing** | pdfplumber |
| **Data Processing** | Pandas |

---

## ✨ Features

- 📅 **Timetable** — Section A/B/C/D weekly schedules in structured table format
- 👥 **Faculty** — Numbered table with name, designation badge, specialization
- 🔍 **RAG Search** — FAISS cosine similarity retrieval with confidence scoring
- 🧠 **NLP Pipeline** — Lemmatisation, POS tagging, NER, query expansion
- 🤷 **Honest fallback** — Says "I don't know" when confidence is low
- 🕷️ **Web Scraping** — Playwright-based scrapers for live data collection

---

## 📦 Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/23kb1a3080-cloud/department_chatbot.git
cd department_chatbot

# 2. Install dependencies
pip install fastapi uvicorn sentence-transformers faiss-cpu spacy langchain chromadb
pip install pandas pdfplumber playwright beautifulsoup4 requests

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Install Playwright browser
python -m playwright install chromium
```

---

## ▶️ Run the Chatbot

```bash
python rag_chatbot.py
```

Open your browser at: **http://localhost:8000**

---

## 🕷️ Scrape Fresh Data

```bash
# Run complete scraping pipeline
python main_scraper.py
```

This will:
1. Scrape faculty data from NBKR IRINS portal
2. Scrape main website content
3. Extract PDF  documents
4. Scrape student portal
5. Clean and preprocess all data
6. Build ChromaDB vector embeddings

---

## 💬 Sample Queries

| Query | Response |
|-------|----------|
| `Section A timetable` | Full week table for Section A only |
| `Section B Monday` | Monday schedule for Section B |
| `List all faculty` | Numbered table: Name, Designation, Specialization |
| `Who is the HOD?` | Faculty card with full details |
| `Who teaches Machine Learning?` | Filtered faculty table |
| `How to check attendance?` | NBKR portal information |
| `What is the capital of France?` | "I'm not sure — not related to AI&DS dept" |

---

## 📁 Project Structure

```
department_chatbot/
├── rag_chatbot.py              # Main chatbot (RAG + NLP + FastAPI)
├── main_scraper.py             # Complete scraping pipeline
├── faculty_scraper.py          # Faculty data scraper (Playwright)
├── website_scraper.py          # Main website scraper (Playwright)
├── pdf_scraper.py              # PDF extractor (pdfplumber)
├── portal_scraper.py           # Student portal scraper (Playwright)
├── preprocess.py               # Data cleaning pipeline
├── embeddings.py               # ChromaDB vector store builder
├── chatbot_engine.py           # CLI chatbot for testing
├── aids_faculty_data.json      # Faculty knowledge base
├── aids_timetable_data.json    # Timetable data (Sections A-D)
├── aids_faculty_kb.json        # Faculty Q&A knowledge base
├── aids_timetable_kb.json      # Timetable Q&A knowledge base
├── nbkr_knowledge_base.json    # NBKR services knowledge base
└── data/                       # Scraped raw + cleaned data
```

---

## 🧠 How RAG Works

```
User Query
    ↓
spaCy NLP Analysis
(lemmatisation, NER, POS tagging, query expansion)
    ↓
FAISS Vector Search
(cosine similarity on 384-dim embeddings)
    ↓
Top-K Document Retrieval
    ↓
Intent-Aware Answer Synthesis
    ↓
Structured HTML Response
```

---

## 📊 Data Sources

| Source | URL |
|--------|-----|
| Faculty | https://nbkrist.irins.org/faculty/index/Department+of++AI+and+DS |
| Website | https://www.nbkrist.org/ |
| PDF | https://nbkrist.org/Acdemic_calendar/ |
| Portal | https://portal.nbkrsac.in/ |

---

## 👨‍💻 Department

**AI & Data Science Department**  
NBKR Institute of Science & Technology  
Vidyanagar, Nellore District, Andhra Pradesh

---

## 📄 License

MIT License
