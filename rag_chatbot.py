"""
NBKR Institute AI Chatbot — RAG + NLP v5.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NLP Layer  (spaCy en_core_web_sm):
  • Tokenisation & stop-word removal
  • Lemmatisation  — "teaching" → "teach", "classes" → "class"
  • POS tagging    — keep only NOUN / PROPN / VERB / ADJ
  • Named-Entity Recognition (NER) — extract PERSON, ORG, DATE …
  • Dependency parsing — find question subject/object
  • Query expansion  — add lemmas + entities to the FAISS query

RAG Layer  (same as ChatGPT architecture):
  • Embeddings : sentence-transformers/all-MiniLM-L6-v2
  • Retrieval  : FAISS IndexFlatIP (cosine similarity on L2-normalised vecs)
  • Confidence : cosine threshold 0.30 → honest "I don't know"
  • Generation : intent-aware answer synthesis from retrieved context
  • Memory     : per-connection sliding-window conversation history
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
import json, os, re, numpy as np, uvicorn

# ─────────────────────────────────────────────────────────────────────────────
# Global state
# ─────────────────────────────────────────────────────────────────────────────
chat_history: List[Dict] = []
active_connections: List[WebSocket] = []
conversation_memory: Dict[str, List[Dict]] = {}

embeddings_model = None
faiss_index      = None
knowledge_docs: List[Dict] = []
nlp              = None          # spaCy model

CONFIDENCE_THRESHOLD = 0.30
TOP_K = 7                        # retrieve more candidates; NLP re-ranks them

# ─────────────────────────────────────────────────────────────────────────────
# NLP initialisation
# ─────────────────────────────────────────────────────────────────────────────
def initialize_nlp() -> bool:
    global nlp
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✓ spaCy NLP model loaded  (en_core_web_sm)")
        return True
    except Exception as e:
        print(f"⚠ spaCy not available: {e}  — NLP features disabled")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# NLP query analysis
# ─────────────────────────────────────────────────────────────────────────────
class QueryAnalysis:
    """Holds all NLP-extracted information about a user query."""
    def __init__(self):
        self.original: str = ""
        self.lemmatized: str = ""          # lemmatised, stop-words removed
        self.expanded: str = ""            # original + lemmas + entities
        self.tokens: List[str] = []        # meaningful tokens (lemmas)
        self.entities: List[Tuple[str,str]] = []   # (text, label)
        self.person_names: List[str] = []
        self.intent_signals: List[str] = []        # POS-filtered keywords
        self.question_type: str = "unknown"        # who/what/when/how/list


def analyse_query(query: str) -> QueryAnalysis:
    """
    Run full spaCy NLP pipeline on the query.
    Returns a QueryAnalysis with lemmas, entities, POS tokens, etc.
    Falls back gracefully if spaCy is unavailable.
    """
    qa = QueryAnalysis()
    qa.original = query

    if nlp is None:
        qa.lemmatized = query.lower()
        qa.expanded   = query.lower()
        qa.tokens     = query.lower().split()
        return qa

    doc = nlp(query)

    # ── Question type detection via first WH-word ─────────────────────────
    q_lower = query.lower()
    if q_lower.startswith(("who", "whose")):
        qa.question_type = "who"
    elif q_lower.startswith(("what", "which")):
        qa.question_type = "what"
    elif q_lower.startswith(("when",)):
        qa.question_type = "when"
    elif q_lower.startswith(("how many", "how much", "list", "show all")):
        qa.question_type = "list"
    elif q_lower.startswith(("how",)):
        qa.question_type = "how"
    elif q_lower.startswith(("where",)):
        qa.question_type = "where"
    elif q_lower.startswith(("show", "display", "give")):
        qa.question_type = "show"

    # ── Lemmatisation + POS filtering ────────────────────────────────────
    keep_pos = {"NOUN", "PROPN", "VERB", "ADJ"}
    meaningful_tokens = []
    for token in doc:
        if (not token.is_stop and
                not token.is_punct and
                not token.is_space and
                token.pos_ in keep_pos and
                len(token.lemma_) > 1):
            meaningful_tokens.append(token.lemma_.lower())

    qa.tokens     = meaningful_tokens
    qa.lemmatized = " ".join(meaningful_tokens)

    # ── Named Entity Recognition ──────────────────────────────────────────
    for ent in doc.ents:
        qa.entities.append((ent.text, ent.label_))
        if ent.label_ == "PERSON":
            qa.person_names.append(ent.text.lower())

    # ── Intent signals: nouns + proper nouns only ─────────────────────────
    qa.intent_signals = [t.lemma_.lower() for t in doc
                         if t.pos_ in {"NOUN", "PROPN"} and not t.is_stop]

    # ── Expanded query: original + lemmas + entity texts ─────────────────
    extra = " ".join(qa.tokens + [e[0] for e in qa.entities])
    qa.expanded = f"{query} {extra}".strip()

    return qa


# ─────────────────────────────────────────────────────────────────────────────
# NLP-enhanced intent detection
# ─────────────────────────────────────────────────────────────────────────────
def detect_intent(query: str, qa: QueryAnalysis) -> str:
    """
    Two-pass intent detection:
      Pass 1 — keyword rules on original query (fast)
      Pass 2 — spaCy lemma/entity signals (accurate)
    """
    q = query.lower()

    # Pass 1: keyword rules
    if any(w in q for w in ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]):
        return "greeting"
    if any(w in q for w in ["bye", "goodbye", "thank", "thanks", "appreciate"]):
        return "farewell"
    if any(w in q for w in ["help", "what can you", "what do you know", "capabilities"]):
        return "help"

    # Pass 2: NLP signals
    timetable_lemmas = {"timetable", "schedule", "class", "period", "timing", "slot", "lecture"}
    faculty_lemmas   = {"faculty", "professor", "hod", "head", "teacher", "lecturer",
                        "instructor", "staff", "doctor", "dr", "mr", "mrs", "ms", "prof"}
    service_lemmas   = {"attendance", "journal", "portal", "intranet", "assessment",
                        "exam", "fee", "hostel", "admission", "placement", "library",
                        "result", "mark", "grade"}

    signals = set(qa.intent_signals + qa.tokens)

    if signals & timetable_lemmas or any(w in q for w in ["timetable","schedule","time table"]):
        return "timetable"
    if (signals & faculty_lemmas
            or qa.question_type == "who"
            or qa.person_names
            or any(w in q for w in ["who is","who teaches","who are","hod","head of"])):
        return "faculty"
    if signals & service_lemmas:
        return "services"

    return "general"

# ─────────────────────────────────────────────────────────────────────────────
# Faculty data — loaded once at startup
# ─────────────────────────────────────────────────────────────────────────────
_FACULTY_DATA: List[Dict] = []

def load_faculty_data():
    global _FACULTY_DATA
    if os.path.exists("aids_faculty_data.json"):
        with open("aids_faculty_data.json", "r", encoding="utf-8") as f:
            _FACULTY_DATA = json.load(f)

# Designation order for sorting (senior first)
_DESIG_ORDER = {
    "head of the department": 0,
    "professor": 1,
    "associate professor": 2,
    "assistant professor": 3,
}

def _desig_rank(d: str) -> int:
    return _DESIG_ORDER.get(d.lower().strip(), 9)

# Designation badge colours
_DESIG_COLOR = {
    "Head of the Department": ("#1a237e", "#e8eaf6"),
    "Professor":              ("#1b5e20", "#e8f5e9"),
    "Associate Professor":    ("#e65100", "#fff3e0"),
    "Assistant Professor":    ("#4a148c", "#f3e5f5"),
}

def _badge(designation: str) -> str:
    fg, bg = _DESIG_COLOR.get(designation, ("#333", "#f5f5f5"))
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:10px;font-size:11px;font-weight:600">{designation}</span>')


# ─────────────────────────────────────────────────────────────────────────────
# Faculty HTML table builders
# ─────────────────────────────────────────────────────────────────────────────
_FTH = ('style="border:1px solid #ddd;padding:9px 12px;text-align:left;'
        'font-size:12px;background:#f0f4ff;font-weight:600"')
_FTD = 'style="border:1px solid #ddd;padding:8px 12px;font-size:13px;vertical-align:top"'
_FTD_C = 'style="border:1px solid #ddd;padding:8px 12px;font-size:13px;text-align:center;vertical-align:middle"'


def build_faculty_list_table(faculty_list: List[Dict] = None) -> str:
    """
    Renders a clean numbered table:
    S.No | Name | Designation | Specialization
    Sorted by designation rank (HOD → Professor → Associate → Assistant).
    """
    data = sorted(
        faculty_list if faculty_list else _FACULTY_DATA,
        key=lambda x: _desig_rank(x.get("designation", ""))
    )

    rows = ""
    for i, f in enumerate(data, 1):
        name  = f.get("name", "—")
        desig = f.get("designation", "—")
        spec  = f.get("specialization", "—")
        rows += (
            f'<tr style="background:{"#fafafa" if i % 2 == 0 else "#fff"}">'
            f'<td {_FTD_C}>{i}</td>'
            f'<td {_FTD}><b>{name}</b></td>'
            f'<td {_FTD}>{_badge(desig)}</td>'
            f'<td {_FTD} style="color:#555">{spec}</td>'
            f'</tr>'
        )

    total = len(data)
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;
              padding:10px 14px;border-radius:8px 8px 0 0;display:flex;
              justify-content:space-between;align-items:center">
    <b>👥 AI &amp; DS Department — Faculty List</b>
    <span style="font-size:11px;opacity:.85">{total} Members</span>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse;min-width:500px">
      <thead>
        <tr>
          <th {_FTH} style="text-align:center;width:50px">S.No</th>
          <th {_FTH}>Name</th>
          <th {_FTH}>Designation</th>
          <th {_FTH}>Specialization</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


def build_faculty_card(f: Dict) -> str:
    """
    Renders a single faculty member as a detailed card.
    """
    name  = f.get("name", "—")
    desig = f.get("designation", "—")
    spec  = f.get("specialization", "—")
    qual  = f.get("Qualification", "")

    qual_html = ""
    if qual:
        # Parse "2017-Ph.D-JNTU Ananthapur,2008-M.Tech-..." into rows
        entries = [e.strip() for e in qual.split(",") if e.strip()]
        qual_rows = "".join(
            f'<tr><td {_FTD} style="white-space:nowrap;color:#555">{e}</td></tr>'
            for e in entries
        )
        qual_html = f"""
        <tr>
          <td {_FTD} style="font-weight:600;color:#555;white-space:nowrap">🎓 Qualifications</td>
          <td {_FTD}>
            <table style="border-collapse:collapse">{qual_rows}</table>
          </td>
        </tr>"""

    fg, bg = _DESIG_COLOR.get(desig, ("#333", "#f5f5f5"))
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;
              padding:10px 14px;border-radius:8px 8px 0 0">
    <b>👤 {name}</b>
  </div>
  <div style="border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;overflow:hidden">
    <table style="width:100%;border-collapse:collapse">
      <tr style="background:#f8f9ff">
        <td {_FTD} style="font-weight:600;color:#555;white-space:nowrap;width:160px">🏷️ Designation</td>
        <td {_FTD}>{_badge(desig)}</td>
      </tr>
      <tr>
        <td {_FTD} style="font-weight:600;color:#555;white-space:nowrap">🔬 Specialization</td>
        <td {_FTD}>{spec}</td>
      </tr>
      {qual_html}
    </table>
  </div>
</div>"""


def build_specialization_table(spec_label: str, faculty_list: List[Dict]) -> str:
    """
    Renders faculty filtered by specialization as a table.
    """
    if not faculty_list:
        return f"<p>No faculty found specializing in <b>{spec_label}</b>.</p>"

    rows = ""
    for i, f in enumerate(faculty_list, 1):
        name  = f.get("name", "—")
        desig = f.get("designation", "—")
        spec  = f.get("specialization", "—")
        rows += (
            f'<tr style="background:{"#fafafa" if i % 2 == 0 else "#fff"}">'
            f'<td {_FTD_C}>{i}</td>'
            f'<td {_FTD}><b>{name}</b></td>'
            f'<td {_FTD}>{_badge(desig)}</td>'
            f'<td {_FTD} style="color:#555">{spec}</td>'
            f'</tr>'
        )

    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;
              padding:10px 14px;border-radius:8px 8px 0 0">
    <b>🔬 Faculty specializing in {spec_label}</b>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse;min-width:400px">
      <thead>
        <tr>
          <th {_FTH} style="text-align:center;width:50px">S.No</th>
          <th {_FTH}>Name</th>
          <th {_FTH}>Designation</th>
          <th {_FTH}>Specialization</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────
def load_knowledge_base() -> List[Dict]:
    docs = []

    # 1. Structured faculty data
    if os.path.exists("aids_faculty_data.json"):
        with open("aids_faculty_data.json", "r", encoding="utf-8") as f:
            for fac in json.load(f):
                name  = fac.get("name", "")
                desig = fac.get("designation", "")
                spec  = fac.get("specialization", "")
                qual  = fac.get("Qualification", "")
                text  = f"{name} is {desig} in the AI & DS Department at NBKR Institute. Specialization: {spec}."
                if qual:
                    text += f" Qualifications: {qual}."
                docs.append({"text": text, "type": "faculty",
                             "name": name, "designation": desig})

    # 2. Timetable — one doc per section+day for richer retrieval
    if os.path.exists("aids_timetable_data.json"):
        with open("aids_timetable_data.json", "r", encoding="utf-8") as f:
            tt = json.load(f)
        subjects_map = tt.get("subjects", {})
        for section, days in tt.get("timetable", {}).items():
            for day, periods in days.items():
                lines = [f"{section} {day} timetable:"]
                for slot, subj in periods.items():
                    lines.append(f"  {slot} → {subj}")
                docs.append({"text": "\n".join(lines), "type": "timetable",
                             "section": section, "day": day})

    # 3. Flat knowledge-base JSON files
    for kb_file in ["nbkr_knowledge_base.json", "aids_faculty_kb.json", "aids_timetable_kb.json"]:
        if os.path.exists(kb_file):
            with open(kb_file, "r", encoding="utf-8") as f:
                for key, val in json.load(f).items():
                    if val and str(val).strip():
                        docs.append({"text": f"{key}: {val}", "type": "knowledge", "key": key})

    print(f"✓ Knowledge base: {len(docs)} documents loaded")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
# RAG initialisation
# ─────────────────────────────────────────────────────────────────────────────
def initialize_rag() -> bool:
    global embeddings_model, faiss_index, knowledge_docs
    print("🔄 Initialising RAG engine …")

    try:
        from sentence_transformers import SentenceTransformer
        embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✓ Sentence-transformer model loaded")
    except Exception as e:
        print(f"⚠ Embedding model failed: {e}"); return False

    knowledge_docs = load_knowledge_base()
    if not knowledge_docs:
        print("⚠ No documents found"); return False

    try:
        import faiss
        texts = [d["text"] for d in knowledge_docs]
        vecs  = embeddings_model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        dim   = vecs.shape[1]
        faiss_index = faiss.IndexFlatIP(dim)   # Inner-product = cosine on normalised vecs
        faiss_index.add(vecs.astype("float32"))
        print(f"✓ FAISS index built  ({len(knowledge_docs)} vectors, dim={dim})")
        return True
    except Exception as e:
        print(f"⚠ FAISS failed: {e}"); return False


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval  — uses NLP-expanded query for better recall
# ─────────────────────────────────────────────────────────────────────────────
def retrieve(qa: QueryAnalysis, top_k: int = TOP_K) -> List[Tuple[Dict, float]]:
    """
    Encode the NLP-expanded query (original + lemmas + entities) so the
    embedding captures more semantic surface area than the raw query alone.
    """
    if embeddings_model is None or faiss_index is None:
        return []
    search_text = qa.expanded if qa.expanded.strip() else qa.original
    q_vec = embeddings_model.encode([search_text], normalize_embeddings=True).astype("float32")
    scores, indices = faiss_index.search(q_vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(knowledge_docs):
            results.append((knowledge_docs[idx], float(score)))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Timetable data — loaded once at startup
# ─────────────────────────────────────────────────────────────────────────────
_TT_DATA: Dict = {}   # full timetable JSON

def load_timetable_data():
    global _TT_DATA
    if os.path.exists("aids_timetable_data.json"):
        with open("aids_timetable_data.json", "r", encoding="utf-8") as f:
            _TT_DATA = json.load(f)

# Canonical time-slot order (morning → afternoon)
SLOT_ORDER = ["9-10","10-11","11-12","9-12","10-12",
              "1-2","2-3","3-4","1-4","2-4"]

DAYS_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

SUBJECT_FULL = {
    "LAC":  "Linear Algebra & Calculus",
    "EP":   "Engineering Physics",
    "BEEE": "Basic Electrical & Electronics Engineering",
    "CP LAB": "Computer Programming Lab",
    "EP-LAB": "Engineering Physics Lab",
    "EEE WS": "EEE Workshop",
    "IT WS":  "IT Workshop",
    "NGCS":   "NSS/NCC/Community Service",
    "ENGINEERING GRAPHICS": "Engineering Graphics",
    "INTRODUCTION TO PROGRAMMING": "Introduction to Programming",
}

# ─────────────────────────────────────────────────────────────────────────────
# NLP-powered timetable query parser
# ─────────────────────────────────────────────────────────────────────────────
def parse_timetable_query(qa: QueryAnalysis) -> Dict:
    """
    Use NLP tokens + regex to extract:
      section  : Section_A / B / C / D  (or None)
      day      : Monday … Saturday  (or None = full week)
      subject  : LAC / EP / BEEE … (or None)
      year     : 1 / 2 / 3 / 4  (or None)
    """
    q = qa.original.lower().strip()
    result = {"section": None, "day": None, "subject": None, "year": None}

    # ── Section detection — strict patterns, checked first ───────────────
    sec_patterns = [
        (r"\bsection\s*a\b|\bsec\s*a\b|\bsect\s*a\b", "Section_A"),
        (r"\bsection\s*b\b|\bsec\s*b\b|\bsect\s*b\b", "Section_B"),
        (r"\bsection\s*c\b|\bsec\s*c\b|\bsect\s*c\b", "Section_C"),
        (r"\bsection\s*d\b|\bsec\s*d\b|\bsect\s*d\b", "Section_D"),
    ]
    for pattern, key in sec_patterns:
        if re.search(pattern, q):
            result["section"] = key
            break

    # ── Day detection ─────────────────────────────────────────────────────
    for day in DAYS_ORDER:
        if day.lower() in q:
            result["day"] = day
            break

    # ── Subject detection — only when NO section found ────────────────────
    # (if section is present, subject is ignored — show full section table)
    if result["section"] is None:
        subject_aliases = [
            ("linear algebra", "LAC"), ("calculus", "LAC"), (" lac ", "LAC"),
            ("engineering physics", "EP"), (" ep ", "EP"), ("physics lab", "EP-LAB"),
            ("ep-lab", "EP-LAB"), ("ep lab", "EP-LAB"),
            ("basic electrical", "BEEE"), ("beee", "BEEE"), ("electrical", "BEEE"),
            ("cp lab", "CP LAB"), ("programming lab", "CP LAB"),
            ("eee workshop", "EEE WS"), ("eee ws", "EEE WS"),
            ("it workshop", "IT WS"), ("it ws", "IT WS"),
            ("engineering graphics", "ENGINEERING GRAPHICS"), ("graphics", "ENGINEERING GRAPHICS"),
            ("introduction to programming", "INTRODUCTION TO PROGRAMMING"),
            ("ngcs", "NGCS"), (" nss ", "NGCS"), (" ncc ", "NGCS"),
        ]
        padded = f" {q} "   # pad so word-boundary aliases work
        for alias, code in subject_aliases:
            if alias in padded:
                result["subject"] = code
                break

    # ── Year detection ────────────────────────────────────────────────────
    year_map = {"1st": 1, "first": 1, "2nd": 2, "second": 2,
                "3rd": 3, "third": 3, "4th": 4, "fourth": 4}
    for word, yr in year_map.items():
        if word in q:
            result["year"] = yr
            break
    m = re.search(r"\b([1-4])\s*(?:st|nd|rd|th)?\s*year\b", q)
    if m:
        result["year"] = int(m.group(1))

    return result


# ─────────────────────────────────────────────────────────────────────────────
# HTML table builders
# ─────────────────────────────────────────────────────────────────────────────
_TH = 'style="border:1px solid #ccc;padding:9px 12px;text-align:center;font-size:12px"'
_TD = 'style="border:1px solid #ccc;padding:8px 10px;text-align:center;font-size:12px"'
_TD_TIME = 'style="border:1px solid #ccc;padding:8px 10px;font-weight:bold;background:#f0f4ff;font-size:12px;white-space:nowrap"'
_TD_EMPTY = 'style="border:1px solid #ccc;padding:8px 10px;text-align:center;background:#fafafa;color:#bbb;font-size:12px"'

def _cell(val: str) -> str:
    """Colour-code a timetable cell by subject type."""
    if val == "-":
        return f'<td {_TD_EMPTY}>—</td>'
    colors = {
        "LAC": "#e8f4fd", "EP": "#fef9e7", "BEEE": "#fdf2f8",
        "CP LAB": "#e8f8f5", "EP-LAB": "#fef5e4", "EEE WS": "#f4ecf7",
        "IT WS": "#eafaf1", "NGCS": "#fdfefe",
        "ENGINEERING GRAPHICS": "#f0f3ff",
        "INTRODUCTION TO PROGRAMMING": "#fff3e0",
    }
    bg = "#fff"
    for code, colour in colors.items():
        if code in val:
            bg = colour
            break
    return f'<td style="border:1px solid #ccc;padding:8px 10px;text-align:center;background:{bg};font-size:12px">{val}</td>'


def build_section_week_table(section_key: str) -> str:
    """Full Mon–Sat table for one section (rows = time slots, cols = days)."""
    tt = _TT_DATA.get("timetable", {})
    data = tt.get(section_key, {})
    if not data:
        return f"<p>No timetable found for {section_key}.</p>"

    # Collect all slots that appear in this section
    all_slots = set()
    for day_data in data.values():
        all_slots.update(day_data.keys())
    slots = sorted(all_slots, key=lambda x: SLOT_ORDER.index(x) if x in SLOT_ORDER else 99)

    label = section_key.replace("_", " ")
    year_label = "1st Year · 1st Semester"   # extend when multi-year data added

    # Header row
    day_headers = "".join(f'<th {_TH}>{d}</th>' for d in DAYS_ORDER)
    header = f'<tr style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff"><th {_TH}>Time</th>{day_headers}</tr>'

    # Data rows
    rows = ""
    for slot in slots:
        cells = "".join(
            _cell(data.get(day, {}).get(slot, "-")) for day in DAYS_ORDER
        )
        rows += f'<tr><td {_TD_TIME}>{slot}</td>{cells}</tr>'

    legend_items = " | ".join(f"<b>{k}</b>={v}" for k, v in SUBJECT_FULL.items())

    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 14px;border-radius:8px 8px 0 0">
    <b>📅 AI &amp; DS Department — {label}</b>
    <span style="float:right;font-size:11px;opacity:.85">{year_label}</span>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse;min-width:700px">
      <thead>{header}</thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <div style="margin-top:6px;padding:7px 10px;background:#f8f9fa;border-radius:6px;font-size:10px;color:#555;line-height:1.7">
    {legend_items}
  </div>
</div>"""


def build_day_table(section_key: str, day: str) -> str:
    """Single-day table: rows = time slots, 2 cols (Time | Subject & Faculty)."""
    tt = _TT_DATA.get("timetable", {})
    data = tt.get(section_key, {}).get(day, {})
    if not data:
        return f"<p>No classes found for {section_key.replace('_',' ')} on {day}.</p>"

    slots = sorted(data.keys(), key=lambda x: SLOT_ORDER.index(x) if x in SLOT_ORDER else 99)
    label = section_key.replace("_", " ")

    rows = ""
    for slot in slots:
        val = data[slot]
        rows += f'<tr><td {_TD_TIME}>{slot}</td>{_cell(val)}</tr>'

    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 14px;border-radius:8px 8px 0 0">
    <b>📅 {label} — {day} Schedule</b>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse">
      <thead><tr style="background:#f0f4ff">
        <th {_TH}>Time Slot</th><th {_TH}>Subject &amp; Faculty</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


def build_subject_table(subject_code: str, section_key: str = None) -> str:
    """
    Show slots for a given subject.
    If section_key is given → only that section.
    If section_key is None  → all sections (only when user explicitly asks for subject only).
    """
    tt = _TT_DATA.get("timetable", {})
    sections = [section_key] if section_key else ["Section_A","Section_B","Section_C","Section_D"]
    rows = ""
    for sec in sections:
        sec_data = tt.get(sec, {})
        for day in DAYS_ORDER:
            for slot, val in sec_data.get(day, {}).items():
                if subject_code in val:
                    sec_label = sec.replace("_"," ")
                    rows += (f'<tr><td {_TD}>{sec_label}</td>'
                             f'<td {_TD}>{day}</td>'
                             f'<td {_TD_TIME}>{slot}</td>'
                             f'{_cell(val)}</tr>')

    if not rows:
        scope = section_key.replace("_"," ") if section_key else "any section"
        return f"<p>No <b>{subject_code}</b> classes found in {scope}.</p>"

    full_name = SUBJECT_FULL.get(subject_code, subject_code)
    scope_label = section_key.replace("_"," ") if section_key else "All Sections"
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 14px;border-radius:8px 8px 0 0">
    <b>📚 {full_name} ({subject_code}) — {scope_label}</b>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse">
      <thead><tr style="background:#f0f4ff">
        <th {_TH}>Section</th><th {_TH}>Day</th><th {_TH}>Time</th><th {_TH}>Subject &amp; Faculty</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


def build_all_sections_overview() -> str:
    """Summary table: rows = sections, cols = days, cell = first subject."""
    tt = _TT_DATA.get("timetable", {})
    sections = ["Section_A","Section_B","Section_C","Section_D"]

    day_headers = "".join(f'<th {_TH}>{d[:3]}</th>' for d in DAYS_ORDER)
    header = f'<tr style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff"><th {_TH}>Section</th>{day_headers}</tr>'

    rows = ""
    for sec in sections:
        sec_data = tt.get(sec, {})
        cells = ""
        for day in DAYS_ORDER:
            day_data = sec_data.get(day, {})
            if day_data:
                first_val = list(day_data.values())[0]
                # extract just subject code
                code = first_val.split("(")[0].strip()
                cells += f'<td style="border:1px solid #ccc;padding:6px 8px;text-align:center;font-size:11px">{code}</td>'
            else:
                cells += f'<td {_TD_EMPTY}>—</td>'
        rows += f'<tr><td style="border:1px solid #ccc;padding:8px;font-weight:bold;background:#f0f4ff;font-size:12px">{sec.replace("_"," ")}</td>{cells}</tr>'

    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 14px;border-radius:8px 8px 0 0">
    <b>📅 AI &amp; DS — All Sections Overview (First Period Each Day)</b>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse">
      <thead>{header}</thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <p style="font-size:11px;color:#888;margin-top:4px">Ask "Section A timetable" or "Section B Monday" for full details.</p>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Timetable response router — called BEFORE RAG retrieval
# ─────────────────────────────────────────────────────────────────────────────
def handle_timetable_query(qa: QueryAnalysis) -> str:
    """
    Deterministic timetable handler — bypasses RAG entirely.

    STRICT ISOLATION RULES:
      • Section A query  → ONLY Section A data, never B/C/D
      • Section B query  → ONLY Section B data, never A/C/D
      • Section C query  → ONLY Section C data, never A/B/D
      • Section D query  → ONLY Section D data, never A/B/C
      • Subject query (no section) → subject across all sections
      • No section, no subject → ask user to specify
    """
    parsed  = parse_timetable_query(qa)
    section = parsed["section"]   # e.g. "Section_A" or None
    day     = parsed["day"]       # e.g. "Monday" or None
    subject = parsed["subject"]   # e.g. "LAC" or None

    # ── Case 1: section + day  →  that section's single-day table ONLY ───
    if section and day:
        return build_day_table(section, day)

    # ── Case 2: section only  →  that section's full week table ONLY ─────
    if section:
        return build_section_week_table(section)

    # ── Case 3: subject only (no section)  →  subject across all sections ─
    if subject:
        return build_subject_table(subject, section_key=None)

    # ── Case 4: "all sections" or "overview" explicitly requested ─────────
    q = qa.original.lower()
    if any(w in q for w in ["all section", "all timetable", "every section", "overview"]):
        return build_all_sections_overview()

    # ── Case 5: vague "timetable" with no section → ask user ─────────────
    return (
        "<div style='font-family:Segoe UI,sans-serif;padding:4px'>"
        "<b>📅 Please specify which section you want:</b><br><br>"
        "• <b>Section A</b> timetable<br>"
        "• <b>Section B</b> timetable<br>"
        "• <b>Section C</b> timetable<br>"
        "• <b>Section D</b> timetable<br><br>"
        "<i>You can also ask:</i><br>"
        "• <i>Section A Monday</i> — single day schedule<br>"
        "• <i>CP Lab schedule</i> — specific subject across all sections<br>"
        "• <i>All sections overview</i> — summary grid"
        "</div>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# NLP-enhanced answer synthesis
# ─────────────────────────────────────────────────────────────────────────────
def synthesize_answer(qa: QueryAnalysis,
                      docs_with_scores: List[Tuple[Dict, float]],
                      intent: str) -> Optional[str]:
    """
    Build a coherent answer from retrieved context using NLP signals.
    Uses:
      • qa.person_names  — match specific faculty by NER-extracted name
      • qa.tokens        — lemma-based keyword matching inside docs
      • qa.question_type — shape the answer format (who/list/how/show)
      • qa.entities      — date/org entities for context
    """
    if not docs_with_scores:
        return None

    best_score = docs_with_scores[0][1]
    if best_score < CONFIDENCE_THRESHOLD:
        return None

    q = qa.original.lower()

    # ── Faculty intent ────────────────────────────────────────────────────────
    if intent == "faculty":
        q = qa.original.lower()

        # ── HOD / head query ──────────────────────────────────────────────
        hod_signals = {"hod", "head"} & set(qa.tokens + [q])
        if hod_signals or any(w in q for w in ["head of department", "head of dept"]):
            hod = next((f for f in _FACULTY_DATA
                        if "head" in f.get("designation","").lower()), None)
            if hod:
                return build_faculty_card(hod)

        # ── Specific person by NER name ───────────────────────────────────
        if qa.person_names:
            for pname in qa.person_names:
                parts = [p for p in pname.split() if len(p) > 2]
                match = next(
                    (f for f in _FACULTY_DATA
                     if any(p in f.get("name","").lower() for p in parts)),
                    None
                )
                if match:
                    return build_faculty_card(match)

        # ── Specific person by lemma token match ──────────────────────────
        for tok in qa.tokens:
            if len(tok) > 3:
                match = next(
                    (f for f in _FACULTY_DATA if tok in f.get("name","").lower()),
                    None
                )
                if match:
                    return build_faculty_card(match)

        # ── Specialization query ──────────────────────────────────────────
        spec_map = {
            "Machine Learning":           ["machine", "learn", "ml"],
            "Deep Learning":              ["deep", "learn", "dl"],
            "Artificial Intelligence":    ["artificial", "intelligence", "ai"],
            "Python Programming":         ["python"],
            "Computer Networks":          ["network", "cn"],
            "Software Engineering":       ["software", "engineer"],
            "DBMS / Database":            ["dbms", "database"],
            "Computer Organization":      ["computer", "organization", "organ"],
        }
        for spec_label, lemmas in spec_map.items():
            if any(lm in qa.tokens for lm in lemmas) or spec_label.lower() in q:
                matched = [f for f in _FACULTY_DATA
                           if any(lm in f.get("specialization","").lower() for lm in lemmas)]
                if matched:
                    return build_specialization_table(spec_label, matched)

        # ── List / all faculty query ──────────────────────────────────────
        list_signals = {"list", "all", "show", "faculty", "member", "staff",
                        "professor", "lecturer", "teacher", "how many"}
        if (qa.question_type in ("list", "show")
                or list_signals & set(qa.tokens)
                or any(w in q for w in ["list", "all faculty", "how many",
                                        "faculty members", "show faculty",
                                        "faculty list", "who are"])):
            return build_faculty_list_table()

        # ── Default: show full list ───────────────────────────────────────
        return build_faculty_list_table()

    # ── Timetable intent ──────────────────────────────────────────────────────
    if intent == "timetable":
        # Already handled before RAG — this is a safety fallback
        return handle_timetable_query(qa)

    # ── Services / general — merge top docs into clean answer ─────────────────
    top_texts = [d["text"] for d, s in docs_with_scores[:3] if s >= CONFIDENCE_THRESHOLD]
    if not top_texts:
        return None

    seen, merged = set(), []
    for text in top_texts:
        for sentence in re.split(r"[.\n]", text):
            s = sentence.strip()
            if s and s not in seen and len(s) > 10:
                seen.add(s)
                merged.append(s)

    answer = ". ".join(merged[:6]).strip()
    if not answer.endswith("."):
        answer += "."
    return f"ℹ️ {answer}"


# ─────────────────────────────────────────────────────────────────────────────
# Main response function — NLP → RAG → Synthesis
# ─────────────────────────────────────────────────────────────────────────────
def get_response(query: str, conn_id: str = "default") -> str:
    query = query.strip()
    if not query:
        return "Please type a question."

    # ── Step 1: NLP analysis ──────────────────────────────────────────────────
    qa = analyse_query(query)

    # ── Step 2: Intent detection (NLP-enhanced) ───────────────────────────────
    intent = detect_intent(query, qa)

    # ── Step 3: Hard-coded intents (no retrieval needed) ─────────────────────
    if intent == "greeting":
        return ("Hello! 👋 I'm the NBKR Institute AI & DS Department assistant.\n\n"
                "I can help you with:\n"
                "📅 Timetables — 'Show Section A timetable'\n"
                "👥 Faculty    — 'Who is the HOD?'\n"
                "💻 Services   — 'How to check attendance?'\n\n"
                "What would you like to know?")

    if intent == "farewell":
        return "You're welcome! Feel free to ask anytime. 😊"

    if intent == "help":
        return ("I can answer questions about:\n\n"
                "📅 Timetables — Section A/B/C/D weekly schedules\n"
                "👥 Faculty    — Names, designations, specializations, qualifications\n"
                "💻 Services   — Attendance, e-journals, assessments, portal\n"
                "📚 Academics  — Courses, admissions, exams, library\n\n"
                "If I don't have the information, I'll tell you honestly.")

    # ── Step 3b: Timetable — handled DIRECTLY, never goes through RAG ────────
    if intent == "timetable":
        return handle_timetable_query(qa)

    # ── Step 4: RAG retrieval with NLP-expanded query ─────────────────────────
    results = retrieve(qa, top_k=TOP_K)

    if not results:
        return ("❓ I don't have information about that in my knowledge base.\n"
                "Please ask about NBKR AI & DS Department faculty, timetables, or services.")

    # ── Step 5: NLP-guided answer synthesis ───────────────────────────────────
    answer = synthesize_answer(qa, results, intent)

    if answer is None:
        best_score = results[0][1] if results else 0
        if best_score < 0.20:
            return ("🤷 I'm not sure about that. This might not be related to the "
                    "NBKR AI & DS Department.\n\n"
                    "Try asking about faculty, timetables, or institute services.")
        return ("❓ I don't have enough information to answer that accurately.\n"
                "Could you rephrase or ask something more specific about NBKR Institute?")

    return answer


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("🎓 NBKR Institute AI Chatbot v5.0 — RAG + NLP")
    print("=" * 70)
    initialize_nlp()
    load_timetable_data()
    load_faculty_data()
    ok = initialize_rag()
    print("✓ RAG ready" if ok else "⚠ RAG unavailable — check data files")
    print("=" * 70)
    yield

app = FastAPI(title="NBKR RAG+NLP Chatbot v5", version="5.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/")
async def home():
    html = r"""<!DOCTYPE html>
<html>
<head>
  <title>NBKR AI Chatbot</title>
  <meta charset="utf-8">
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);height:100vh;display:flex;justify-content:center;align-items:center}
    .wrap{width:92%;max-width:900px;height:92vh;background:#fff;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.3);display:flex;flex-direction:column;overflow:hidden}
    .hdr{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:18px 20px;text-align:center}
    .hdr h1{font-size:22px;margin-bottom:4px}
    .hdr p{font-size:13px;opacity:.9}
    .badge{display:inline-block;background:rgba(255,255,255,.2);padding:3px 10px;border-radius:10px;font-size:10px;margin:2px}
    .status{padding:8px 20px;text-align:center;font-size:12px;color:#888;background:#fafafa;border-bottom:1px solid #eee}
    .status.on{color:#4caf50}
    .msgs{flex:1;padding:18px;overflow-y:auto;background:#f5f5f5;display:flex;flex-direction:column;gap:12px}
    .msg{display:flex}
    .msg.user{justify-content:flex-end}
    .bubble{max-width:72%;padding:11px 15px;border-radius:18px;word-wrap:break-word;white-space:pre-wrap;line-height:1.5;font-size:14px;animation:pop .25s ease}
    @keyframes pop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
    .msg.bot .bubble{background:#fff;color:#333;border-bottom-left-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,.1)}
    .msg.user .bubble{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-bottom-right-radius:4px}
    .inp-row{padding:16px 20px;background:#fff;border-top:1px solid #e8e8e8;display:flex;gap:10px}
    .inp{flex:1;padding:11px 16px;border:2px solid #e0e0e0;border-radius:25px;font-size:14px;outline:none;transition:border-color .2s}
    .inp:focus{border-color:#667eea}
    .btn{padding:11px 22px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;border-radius:25px;cursor:pointer;font-size:14px;font-weight:600;transition:transform .15s}
    .btn:hover{transform:scale(1.04)}
    .typing{display:none;padding:8px 14px;background:#fff;border-radius:18px;border-bottom-left-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,.1);font-size:13px;color:#888;width:fit-content}
    .dot{display:inline-block;width:6px;height:6px;background:#aaa;border-radius:50%;margin:0 2px;animation:blink 1.2s infinite}
    .dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}
    @keyframes blink{0%,80%,100%{opacity:0}40%{opacity:1}}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>🎓 NBKR Institute AI Chatbot</h1>
    <p>AI &amp; DS Department Assistant — RAG + NLP</p>
    <div style="margin-top:6px">
      <span class="badge">🔍 RAG v5</span>
      <span class="badge">🧠 Sentence Transformers</span>
      <span class="badge">📊 FAISS Cosine</span>
      <span class="badge">🔤 spaCy NLP</span>
      <span class="badge">🎯 NER + Lemma</span>
    </div>
  </div>
  <div class="status" id="st">Connecting…</div>
  <div class="msgs" id="msgs">
    <div class="msg bot"><div class="bubble">Hello! 👋 I'm the NBKR AI &amp; DS Department assistant.

I can help with:
📅 Timetables — "Show Section A timetable"
👥 Faculty — "Who is the HOD?"
💻 Services — "How to check attendance?"

If I don't know something, I'll tell you honestly!</div></div>
  </div>
  <div class="inp-row">
    <input class="inp" id="inp" placeholder="Ask me anything about NBKR AI &amp; DS…" autocomplete="off"/>
    <button class="btn" onclick="send()">Send</button>
  </div>
</div>
<script>
  let ws;
  const msgs=document.getElementById('msgs'),inp=document.getElementById('inp'),st=document.getElementById('st');

  function connect(){
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = proto + '//' + location.host + '/ws';
    ws=new WebSocket(wsUrl);
    ws.onopen=()=>{st.textContent='● Connected';st.className='status on'};
    ws.onclose=()=>{st.textContent='● Disconnected';st.className='status';setTimeout(connect,3000)};
    ws.onmessage=e=>{
      const d=JSON.parse(e.data);
      removeTyping();
      addMsg(d.message,'bot');
    };
  }

  function addMsg(text,who){
    const wrap=document.createElement('div');
    wrap.className='msg '+who;
    const b=document.createElement('div');
    b.className='bubble';
    if(who==='bot'&&text.includes('<table')){
      b.style.maxWidth='96%';
      b.innerHTML=text;
    } else {
      b.textContent=text;
    }
    wrap.appendChild(b);
    msgs.appendChild(wrap);
    msgs.scrollTop=msgs.scrollHeight;
  }

  function showTyping(){
    const d=document.createElement('div');
    d.className='msg bot';d.id='typing';
    d.innerHTML='<div class="typing" style="display:block"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
    msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight;
  }

  function removeTyping(){const t=document.getElementById('typing');if(t)t.remove();}

  function send(){
    const msg=inp.value.trim();
    if(!msg||ws.readyState!==1)return;
    addMsg(msg,'user');
    showTyping();
    ws.send(JSON.stringify({message:msg}));
    inp.value='';
  }

  inp.addEventListener('keypress',e=>{if(e.key==='Enter')send();});
  connect();
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    conn_id = str(id(websocket))
    active_connections.append(websocket)
    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)
            user_msg = data.get("message", "").strip()

            chat_history.append({"ts": datetime.now().isoformat(),
                                  "user": user_msg, "bot": None})

            response = get_response(user_msg, conn_id)
            chat_history[-1]["bot"] = response

            await websocket.send_json({"message": response,
                                       "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "5.0.0",
        "nlp_enabled": nlp is not None,
        "rag_enabled": faiss_index is not None,
        "documents": len(knowledge_docs),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
    }


if __name__ == "__main__":
    print("\n🚀 Starting NBKR RAG+NLP Chatbot v5.0 …")
    print("📍 http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
