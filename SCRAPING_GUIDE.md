# 🕷️ NBKR Institute Complete Scraping Pipeline

## 📋 Overview

Complete data scraping and RAG system for NBKR Institute chatbot.

---

## 📦 Files Created

### Scrapers:
1. **faculty_scraper_enhanced.py** - Scrapes AI & DS faculty data
2. **website_scraper_enhanced.py** - Scrapes main website
3. **pdf_scraper.py** - Extracts PDF documents
4. **portal_scraper.py** - Scrapes student portal (Selenium)

### Processing:
5. **preprocess.py** - Cleans and normalizes all data
6. **embeddings.py** - Creates vector embeddings (ChromaDB)
7. **chatbot_engine.py** - CLI chatbot for testing

### Main:
8. **main_scraper.py** - Orchestrates entire pipeline

---

## 🚀 Quick Start

### Run Complete Pipeline:
```bash
python main_scraper.py
```

This will:
1. Scrape faculty data
2. Scrape main website
3. Extract PDF content
4. Scrape student portal
5. Clean and preprocess data
6. Create vector embeddings
7. Store in ChromaDB

---

## 📊 Data Flow

```
Sources
  ├── Faculty Page → faculty_data.csv
  ├── Main Website → main_website.csv
  ├── PDF Document → academic_calendar.csv
  └── Student Portal → portal_data.csv
        ↓
  Preprocessing (preprocess.py)
        ↓
  Cleaned Data → all_cleaned_data.csv
        ↓
  Embeddings (sentence-transformers)
        ↓
  ChromaDB Vector Store
        ↓
  RAG Chatbot
```

---

## 🧪 Test the System

### CLI Chatbot:
```bash
python chatbot_engine.py
```

### Test Queries:
- "Who is the HOD?"
- "Tell me about faculty"
- "What is the academic calendar?"
- "How to access the portal?"

---

## 📁 Directory Structure

```
project/
├── data/
│   ├── raw/              # Raw scraped data
│   │   ├── faculty_data.csv
│   │   ├── main_website.csv
│   │   ├── academic_calendar.csv
│   │   └── portal_data.csv
│   └── cleaned/          # Processed data
│       ├── cleaned_faculty.csv
│       ├── cleaned_website.csv
│       └── all_cleaned_data.csv
├── chroma_db/            # Vector database
├── main_scraper.py       # Main pipeline
└── chatbot_engine.py     # Test chatbot
```

---

## 🔧 Individual Scrapers

### Run Individually:

```bash
# Faculty only
python faculty_scraper_enhanced.py

# Website only
python website_scraper_enhanced.py

# PDF only
python pdf_scraper.py

# Portal only (requires Chrome)
python portal_scraper.py

# Preprocess only
python preprocess.py

# Create embeddings only
python embeddings.py
```

---

## 🎯 Integration with FastAPI Chatbot

### Update rag_chatbot.py:

```python
# Use ChromaDB instead of FAISS
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("college_data")

# Query
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)
```

---

## 📊 Data Sources

| Source | URL | Type |
|--------|-----|------|
| Faculty | https://nbkrist.irins.org/faculty/index/Department+of++AI+and+DS | HTML |
| Website | https://www.nbkrist.org/ | HTML |
| PDF | https://nbkrist.org/Acdemic_calendar/II,III&IVB.Tech.ISem.2025.pdf | PDF |
| Portal | https://portal.nbkrsac.in/ | Dynamic (Selenium) |

---

## 🛠️ Technologies Used

- **requests** - HTTP requests
- **beautifulsoup4** - HTML parsing
- **selenium** - Browser automation
- **pandas** - Data processing
- **pdfplumber** - PDF extraction
- **sentence-transformers** - Embeddings
- **chromadb** - Vector database

---

## ⚙️ Configuration

### Customize URLs:

Edit the URL constants in each scraper:
- `faculty_scraper_enhanced.py`: Line 6
- `website_scraper_enhanced.py`: Line 6
- `pdf_scraper.py`: Line 7
- `portal_scraper.py`: Line 11

### Adjust Scraping:

- **Timeout**: Change `timeout=10` in requests
- **Wait time**: Change `time.sleep(5)` in Selenium
- **Batch size**: Change `batch_size=100` in embeddings

---

## 🐛 Troubleshooting

### Issue: ChromeDriver not found
**Solution**: 
```bash
pip install webdriver-manager
```
The script will auto-download ChromeDriver

### Issue: PDF download fails
**Solution**: Check PDF URL is accessible

### Issue: ChromaDB error
**Solution**: Delete `chroma_db` folder and run again

---

## 📈 Performance

- **Faculty scraping**: ~5 seconds
- **Website scraping**: ~10 seconds
- **PDF extraction**: ~15 seconds
- **Portal scraping**: ~10 seconds
- **Preprocessing**: ~5 seconds
- **Embeddings**: ~30 seconds (depends on data size)

**Total**: ~75 seconds for complete pipeline

---

## 🎓 Next Steps

1. ✅ Run `python main_scraper.py`
2. ✅ Test with `python chatbot_engine.py`
3. ✅ Integrate with FastAPI chatbot
4. ✅ Deploy to production

---

**Status**: ✅ Ready to use!
