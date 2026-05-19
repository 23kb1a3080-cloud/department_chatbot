"""
NBKR Institute AI Chatbot — RAG + NLP + ML v6.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ML Layer   (Supervised — scikit-learn):
  • TF-IDF vectoriser  (1-2 grams, 3000 features)
  • Multinomial Naive Bayes intent classifier
  • Trained on labelled intent examples at startup
  • Predicts: greeting / farewell / help / timetable / faculty / services / general

NLP Layer  (spaCy en_core_web_sm):
  • Lemmatisation, POS tagging, NER, query expansion

RAG Layer:
  • Embeddings : sentence-transformers/all-MiniLM-L6-v2
  • Retrieval  : FAISS IndexFlatIP (cosine similarity)
  • Confidence : threshold 0.30

UI:
  • All responses rendered as structured HTML (tables / cards)
  • Frontend correctly renders innerHTML for ALL bot messages
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json, os, re, numpy as np, uvicorn

# ─────────────────────────────────────────────────────────────────────────────
# Global state
# ─────────────────────────────────────────────────────────────────────────────
chat_history: List[Dict] = []
active_connections: List[WebSocket] = []

embeddings_model  = None
faiss_index       = None
knowledge_docs: List[Dict] = []
nlp               = None   # spaCy
ml_classifier     = None   # TF-IDF + Naive Bayes pipeline
ml_vectorizer     = None

CONFIDENCE_THRESHOLD = 0.28
TOP_K = 7

# ─────────────────────────────────────────────────────────────────────────────
# Supervised ML — Training data & classifier
# ─────────────────────────────────────────────────────────────────────────────
_TRAIN_DATA = [
    # greeting
    ("hello", "greeting"), ("hi", "greeting"), ("hey", "greeting"),
    ("good morning", "greeting"), ("good afternoon", "greeting"),
    ("good evening", "greeting"), ("hi there", "greeting"),
    ("howdy", "greeting"), ("what's up", "greeting"), ("greetings", "greeting"),
    # farewell
    ("bye", "farewell"), ("goodbye", "farewell"), ("thank you", "farewell"),
    ("thanks", "farewell"), ("thank you so much", "farewell"),
    ("ok thanks", "farewell"), ("that's all", "farewell"),
    ("see you", "farewell"), ("appreciate it", "farewell"),
    # help
    ("help", "help"), ("what can you do", "help"), ("what do you know", "help"),
    ("how can you help", "help"), ("capabilities", "help"),
    ("what topics", "help"), ("what can i ask", "help"),
    ("show me options", "help"), ("menu", "help"),
    # timetable
    ("show section a timetable", "timetable"), ("section b schedule", "timetable"),
    ("section c timetable", "timetable"), ("section d timetable", "timetable"),
    ("timetable for section a", "timetable"), ("what is the timetable", "timetable"),
    ("class schedule", "timetable"), ("show timetable", "timetable"),
    ("monday schedule section a", "timetable"), ("section a monday", "timetable"),
    ("cp lab schedule", "timetable"), ("engineering physics timetable", "timetable"),
    ("beee schedule", "timetable"), ("all sections timetable", "timetable"),
    ("section time table", "timetable"), ("table format timetable", "timetable"),
    ("weekly schedule", "timetable"), ("class timing", "timetable"),
    ("lecture schedule", "timetable"), ("period schedule", "timetable"),
    # 2nd year timetable
    ("2nd year section a timetable", "timetable"), ("second year section b", "timetable"),
    ("2nd year timetable", "timetable"), ("second year schedule", "timetable"),
    ("2nd year section a", "timetable"), ("2nd year section b", "timetable"),
    ("ai lab schedule", "timetable"), ("ids lab timetable", "timetable"),
    ("full stack lab schedule", "timetable"), ("dti lab timetable", "timetable"),
    ("artificial intelligence schedule", "timetable"), ("smds timetable", "timetable"),
    # 3rd year timetable
    ("3rd year section a timetable", "timetable"), ("third year section b", "timetable"),
    ("3rd year timetable", "timetable"), ("third year schedule", "timetable"),
    ("3rd year section a", "timetable"), ("3rd year section b", "timetable"),
    ("deep learning lab schedule", "timetable"), ("nlp timetable", "timetable"),
    ("big data analytics schedule", "timetable"), ("social network analysis timetable", "timetable"),
    ("soft skills lab schedule", "timetable"), ("workshop timetable", "timetable"),
    # faculty
    ("who is the hod", "faculty"), ("head of department", "faculty"),
    ("list all faculty", "faculty"), ("faculty members", "faculty"),
    ("who teaches machine learning", "faculty"), ("professor list", "faculty"),
    ("show faculty", "faculty"), ("who is dr", "faculty"),
    ("assistant professor", "faculty"), ("associate professor", "faculty"),
    ("faculty specialization", "faculty"), ("how many faculty", "faculty"),
    ("staff members", "faculty"), ("teachers list", "faculty"),
    ("who are the lecturers", "faculty"), ("faculty details", "faculty"),
    # services
    ("how to check attendance", "services"), ("attendance system", "services"),
    ("e-journal", "services"), ("ejournal", "services"),
    ("online portal", "services"), ("intranet", "services"),
    ("assessment tool", "services"), ("exam duties", "services"),
    ("how to login", "services"), ("portal access", "services"),
    ("library timings", "services"), ("hostel", "services"),
    ("fee structure", "services"), ("admission process", "services"),
    ("placement record", "services"), ("courses offered", "services"),
    ("exam schedule", "services"), ("results", "services"),
    # general
    ("tell me about nbkr", "general"), ("about the college", "general"),
    ("nbkr institute", "general"), ("what is nbkr", "general"),
    ("college information", "general"), ("department info", "general"),
    # circulars
    ("circular", "circulars"), ("notice", "circulars"),
    ("announcement", "circulars"), ("show circulars", "circulars"),
    ("latest notice", "circulars"), ("recent circular", "circulars"),
    ("fee notice", "circulars"), ("class commencement notice", "circulars"),
    ("tuition fee circular", "circulars"), ("early bird offer", "circulars"),
    ("btech classes start", "circulars"), ("when do classes start", "circulars"),
    ("fee payment deadline", "circulars"), ("enrolment notice", "circulars"),
    ("show announcements", "circulars"), ("any new notice", "circulars"),
    ("college notice", "circulars"), ("notice board", "circulars"),
    ("b-10/2026/01", "circulars"), ("iii iv btech notice", "circulars"),
]

def train_ml_classifier():
    """Train TF-IDF + Multinomial Naive Bayes intent classifier."""
    global ml_classifier, ml_vectorizer
    try:
        from sklearn.pipeline import Pipeline
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.preprocessing import LabelEncoder
        import pickle

        texts  = [t for t, _ in _TRAIN_DATA]
        labels = [l for _, l in _TRAIN_DATA]

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=3000,
                                      sublinear_tf=True)),
            ("clf",   MultinomialNB(alpha=0.3)),
        ])
        pipeline.fit(texts, labels)
        ml_classifier = pipeline
        print(f"✓ ML classifier trained  (TF-IDF + Naive Bayes, {len(texts)} samples, "
              f"{len(set(labels))} classes)")
        return True
    except Exception as e:
        print(f"⚠ ML classifier failed: {e}")
        return False


def ml_predict_intent(query: str) -> Tuple[str, float]:
    """Return (intent_label, confidence) from the trained ML classifier."""
    if ml_classifier is None:
        return "general", 0.0
    proba = ml_classifier.predict_proba([query.lower()])[0]
    classes = ml_classifier.classes_
    idx = int(np.argmax(proba))
    return classes[idx], float(proba[idx])


# ─────────────────────────────────────────────────────────────────────────────
# NLP — spaCy query analysis
# ─────────────────────────────────────────────────────────────────────────────
class QueryAnalysis:
    def __init__(self):
        self.original: str = ""
        self.lemmatized: str = ""
        self.expanded: str = ""
        self.tokens: List[str] = []
        self.entities: List[Tuple[str, str]] = []
        self.person_names: List[str] = []
        self.intent_signals: List[str] = []
        self.question_type: str = "unknown"


def analyse_query(query: str) -> QueryAnalysis:
    qa = QueryAnalysis()
    qa.original = query
    if nlp is None:
        qa.lemmatized = query.lower()
        qa.expanded   = query.lower()
        qa.tokens     = query.lower().split()
        return qa

    doc = nlp(query)
    q_lower = query.lower()
    if q_lower.startswith(("who", "whose")):       qa.question_type = "who"
    elif q_lower.startswith(("what", "which")):    qa.question_type = "what"
    elif q_lower.startswith(("when",)):            qa.question_type = "when"
    elif q_lower.startswith(("how many","how much","list","show all")): qa.question_type = "list"
    elif q_lower.startswith(("how",)):             qa.question_type = "how"
    elif q_lower.startswith(("where",)):           qa.question_type = "where"
    elif q_lower.startswith(("show","display","give")): qa.question_type = "show"

    keep_pos = {"NOUN", "PROPN", "VERB", "ADJ"}
    meaningful = []
    for token in doc:
        if (not token.is_stop and not token.is_punct and not token.is_space
                and token.pos_ in keep_pos and len(token.lemma_) > 1):
            meaningful.append(token.lemma_.lower())

    qa.tokens     = meaningful
    qa.lemmatized = " ".join(meaningful)

    for ent in doc.ents:
        qa.entities.append((ent.text, ent.label_))
        if ent.label_ == "PERSON":
            qa.person_names.append(ent.text.lower())

    qa.intent_signals = [t.lemma_.lower() for t in doc
                         if t.pos_ in {"NOUN", "PROPN"} and not t.is_stop]
    extra = " ".join(qa.tokens + [e[0] for e in qa.entities])
    qa.expanded = f"{query} {extra}".strip()
    return qa


def initialize_nlp() -> bool:
    global nlp
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✓ spaCy NLP model loaded  (en_core_web_sm)")
        return True
    except Exception as e:
        print(f"⚠ spaCy not available: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Intent detection — ML first, NLP rules as fallback
# ─────────────────────────────────────────────────────────────────────────────
def detect_intent(query: str, qa: QueryAnalysis) -> str:
    """
    Two-stage intent detection:
      Stage 1 — Supervised ML (TF-IDF + Naive Bayes) with confidence ≥ 0.45
      Stage 2 — spaCy lemma/entity rule fallback
    """
    ml_intent, ml_conf = ml_predict_intent(query)
    if ml_conf >= 0.45:
        return ml_intent

    # Rule-based fallback using NLP signals
    q = query.lower()
    circular_signals = {"circular","notice","announcement","fee","enrolment",
                        "commencement","early bird","btech","b.tech"}
    timetable_lemmas = {"timetable","schedule","class","period","timing","slot","lecture"}
    faculty_lemmas   = {"faculty","professor","hod","head","teacher","lecturer",
                        "instructor","staff","doctor","dr","mr","mrs","ms","prof"}
    service_lemmas   = {"attendance","journal","portal","intranet","assessment",
                        "exam","hostel","admission","placement","library",
                        "result","mark","grade"}

    signals = set(qa.intent_signals + qa.tokens)
    if (signals & circular_signals
            or any(w in q for w in ["circular","notice","announcement","fee notice",
                                    "early bird","class start","commencement","enrolment"])):
        return "circulars"
    if signals & timetable_lemmas or any(w in q for w in ["timetable","schedule","time table"]):
        return "timetable"
    if (signals & faculty_lemmas or qa.question_type == "who"
            or qa.person_names
            or any(w in q for w in ["who is","who teaches","hod","head of"])):
        return "faculty"
    if signals & service_lemmas:
        return "services"
    return "general"


# ─────────────────────────────────────────────────────────────────────────────
# Faculty data
# ─────────────────────────────────────────────────────────────────────────────
_FACULTY_DATA: List[Dict] = []
_CIRCULARS: List[Dict] = []

def load_faculty_data():
    global _FACULTY_DATA
    if os.path.exists("aids_faculty_data.json"):
        with open("aids_faculty_data.json", "r", encoding="utf-8") as f:
            _FACULTY_DATA = json.load(f)

def load_circulars():
    global _CIRCULARS
    if os.path.exists("nbkr_circulars.json"):
        with open("nbkr_circulars.json", "r", encoding="utf-8") as f:
            _CIRCULARS = json.load(f)
        print(f"✓ Circulars loaded: {len(_CIRCULARS)} notices")

_DESIG_ORDER = {"head of the department":0,"professor":1,
                "associate professor":2,"assistant professor":3}
def _desig_rank(d): return _DESIG_ORDER.get(d.lower().strip(), 9)

_DESIG_COLOR = {
    "Head of the Department": ("#1a237e","#e8eaf6"),
    "Professor":              ("#1b5e20","#e8f5e9"),
    "Associate Professor":    ("#e65100","#fff3e0"),
    "Assistant Professor":    ("#4a148c","#f3e5f5"),
}
def _badge(designation):
    fg, bg = _DESIG_COLOR.get(designation, ("#333","#f5f5f5"))
    return (f'<span style="background:{bg};color:{fg};padding:2px 10px;'
            f'border-radius:10px;font-size:11px;font-weight:600">{designation}</span>')

_FTH = 'style="border:1px solid #ddd;padding:10px 14px;text-align:left;font-size:13px;background:#f0f4ff;font-weight:700;color:#333"'
_FTD = 'style="border:1px solid #ddd;padding:9px 13px;font-size:13px;vertical-align:top"'
_FTD_C = 'style="border:1px solid #ddd;padding:9px 13px;font-size:13px;text-align:center;vertical-align:middle"'


def build_faculty_list_table(faculty_list=None):
    data = sorted(faculty_list if faculty_list else _FACULTY_DATA,
                  key=lambda x: _desig_rank(x.get("designation","")))
    rows = ""
    for i, f in enumerate(data, 1):
        bg = "#fafafa" if i % 2 == 0 else "#fff"
        rows += (f'<tr style="background:{bg}">'
                 f'<td {_FTD_C}>{i}</td>'
                 f'<td {_FTD}><b>{f.get("name","—")}</b></td>'
                 f'<td {_FTD}>{_badge(f.get("designation","—"))}</td>'
                 f'<td {_FTD} style="color:#555">{f.get("specialization","—")}</td>'
                 f'</tr>')
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;
              padding:10px 16px;border-radius:8px 8px 0 0;display:flex;
              justify-content:space-between;align-items:center">
    <b>👥 AI &amp; DS Department — Faculty List</b>
    <span style="font-size:11px;opacity:.85">{len(data)} Members</span>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse;min-width:520px">
      <thead><tr>
        <th {_FTH} style="text-align:center;width:55px">S.No</th>
        <th {_FTH}>Name</th>
        <th {_FTH}>Designation</th>
        <th {_FTH}>Specialization</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


def build_faculty_card(f):
    name  = f.get("name","—")
    desig = f.get("designation","—")
    spec  = f.get("specialization","—")
    qual  = f.get("Qualification","")
    qual_html = ""
    if qual:
        entries = [e.strip() for e in qual.split(",") if e.strip()]
        qual_rows = "".join(f'<tr><td {_FTD} style="color:#555">{e}</td></tr>' for e in entries)
        qual_html = f'<tr><td {_FTD} style="font-weight:700;color:#555">🎓 Qualifications</td><td {_FTD}><table style="border-collapse:collapse">{qual_rows}</table></td></tr>'
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0">
    <b>👤 {name}</b>
  </div>
  <div style="border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;overflow:hidden">
    <table style="width:100%;border-collapse:collapse">
      <tr style="background:#f8f9ff"><td {_FTD} style="font-weight:700;color:#555;width:160px">🏷️ Designation</td><td {_FTD}>{_badge(desig)}</td></tr>
      <tr><td {_FTD} style="font-weight:700;color:#555">🔬 Specialization</td><td {_FTD}>{spec}</td></tr>
      {qual_html}
    </table>
  </div>
</div>"""


def build_specialization_table(spec_label, faculty_list):
    if not faculty_list:
        return f'<p style="font-family:Segoe UI,sans-serif">No faculty found for <b>{spec_label}</b>.</p>'
    rows = ""
    for i, f in enumerate(faculty_list, 1):
        bg = "#fafafa" if i % 2 == 0 else "#fff"
        rows += (f'<tr style="background:{bg}"><td {_FTD_C}>{i}</td>'
                 f'<td {_FTD}><b>{f.get("name","—")}</b></td>'
                 f'<td {_FTD}>{_badge(f.get("designation","—"))}</td>'
                 f'<td {_FTD} style="color:#555">{f.get("specialization","—")}</td></tr>')
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0">
    <b>🔬 Faculty — {spec_label}</b>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse;min-width:420px">
      <thead><tr>
        <th {_FTH} style="text-align:center;width:55px">S.No</th>
        <th {_FTH}>Name</th><th {_FTH}>Designation</th><th {_FTH}>Specialization</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Circular HTML builder
# ─────────────────────────────────────────────────────────────────────────────
def build_circular_card(c: Dict) -> str:
    """Render a single circular as a structured HTML card."""
    cid    = c.get("id", "—")
    date   = c.get("date", "—")
    title  = c.get("title", "Notice")
    content= c.get("content", "")
    portal = c.get("payment_portal", "")
    kd     = c.get("key_dates", {})
    applic = c.get("applicable_to", "")

    # Key dates rows
    kd_rows = ""
    if kd.get("class_commencement"):
        kd_rows += f'<tr style="background:#fff8e1"><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#e65100;width:200px">📅 Class Commencement</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#e65100">{kd["class_commencement"]}</td></tr>'
    if kd.get("early_bird_deadline"):
        kd_rows += f'<tr style="background:#e8f5e9"><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#2e7d32">🎯 Early Bird Deadline</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#2e7d32">{kd["early_bird_deadline"]} — {kd.get("early_bird_discount","10%")} discount</td></tr>'

    portal_row = ""
    if portal:
        portal_row = f'<tr><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#555">🌐 Payment Portal</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px"><a href="{portal}" style="color:#667eea">{portal}</a></td></tr>'

    applic_row = ""
    if applic:
        applic_row = f'<tr style="background:#f8f9ff"><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#555">👥 Applicable To</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px">{applic}</td></tr>'

    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#e65100,#bf360c);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0;display:flex;justify-content:space-between;align-items:center">
    <b>📢 {title}</b>
    <span style="font-size:11px;opacity:.85">No. {cid} &nbsp;|&nbsp; {date}</span>
  </div>
  <div style="border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;overflow:hidden">
    <table style="width:100%;border-collapse:collapse">
      <tr style="background:#fff3e0"><td colspan="2" style="border:1px solid #ddd;padding:10px 14px;font-size:13px;color:#333;line-height:1.6">{content}</td></tr>
      {kd_rows}
      {applic_row}
      {portal_row}
      <tr style="background:#f8f9ff"><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#555">📝 Action Required</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px">Pay fee via portal &amp; submit fund transfer details at college office to collect receipt.</td></tr>
    </table>
  </div>
</div>"""


def build_all_circulars_table() -> str:
    """Render all circulars as a summary table."""
    if not _CIRCULARS:
        return _info_card("📢 Circulars & Announcements", [
            ("Status", "No circulars available at this time."),
        ])

    rows = ""
    for i, c in enumerate(_CIRCULARS):
        bg = "#f8f9ff" if i % 2 == 0 else "#fff"
        rows += (f'<tr style="background:{bg}">'
                 f'<td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;text-align:center">{i+1}</td>'
                 f'<td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#e65100">{c.get("id","—")}</td>'
                 f'<td style="border:1px solid #ddd;padding:9px 14px;font-size:13px">{c.get("date","—")}</td>'
                 f'<td style="border:1px solid #ddd;padding:9px 14px;font-size:13px">{c.get("title","—")}</td>'
                 f'</tr>')

    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#e65100,#bf360c);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0;display:flex;justify-content:space-between;align-items:center">
    <b>📢 NBKR Circulars &amp; Announcements</b>
    <span style="font-size:11px;opacity:.85">{len(_CIRCULARS)} Notice(s)</span>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse;min-width:500px">
      <thead><tr style="background:#fff3e0">
        <th style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;text-align:center;width:50px">S.No</th>
        <th style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;text-align:left">Notice No.</th>
        <th style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;text-align:left">Date</th>
        <th style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;text-align:left">Subject</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <p style="font-size:11px;color:#888;margin-top:5px;font-family:Segoe UI,sans-serif">
    Ask "show circular B-10/2026/01" or "fee notice" for full details.
  </p>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge base loading
# ─────────────────────────────────────────────────────────────────────────────
def load_knowledge_base() -> List[Dict]:
    docs = []
    if os.path.exists("aids_faculty_data.json"):
        with open("aids_faculty_data.json","r",encoding="utf-8") as f:
            for fac in json.load(f):
                name  = fac.get("name","")
                desig = fac.get("designation","")
                spec  = fac.get("specialization","")
                qual  = fac.get("Qualification","")
                text  = f"{name} is {desig} in AI & DS Department at NBKR. Specialization: {spec}."
                if qual: text += f" Qualifications: {qual}."
                docs.append({"text":text,"type":"faculty","name":name,"designation":desig})

    if os.path.exists("aids_timetable_data.json"):
        with open("aids_timetable_data.json","r",encoding="utf-8") as f:
            tt = json.load(f)
        subjects_map = tt.get("subjects", {})
        faculty_map  = tt.get("faculty", {})
        for section, days in tt.get("timetable",{}).items():
            # Determine year label from section key
            if "2nd_Year" in section:
                year_label = "2nd Year 2nd Semester"
            else:
                year_label = "1st Year 1st Semester"
            sec_label = section.replace("_"," ")
            for day, periods in days.items():
                lines = [f"{sec_label} {year_label} {day} timetable:"]
                for slot, subj in periods.items():
                    full_subj = subjects_map.get(subj.split("(")[0].strip(), subj)
                    lines.append(f"  {slot} → {subj} ({full_subj})")
                docs.append({"text":"\n".join(lines),"type":"timetable",
                             "section":section,"day":day,"year":year_label})

    for kb_file in ["nbkr_knowledge_base.json","aids_faculty_kb.json","aids_timetable_kb.json"]:
        if os.path.exists(kb_file):
            with open(kb_file,"r",encoding="utf-8") as f:
                for key, val in json.load(f).items():
                    if val and str(val).strip():
                        docs.append({"text":f"{key}: {val}","type":"knowledge","key":key})

    # Load circulars
    if os.path.exists("nbkr_circulars.json"):
        with open("nbkr_circulars.json","r",encoding="utf-8") as f:
            for c in json.load(f):
                text = (f"Circular {c.get('id','')} dated {c.get('date','')}: "
                        f"{c.get('title','')}. {c.get('content','')}")
                docs.append({"text": text, "type": "circular",
                             "id": c.get("id",""), "date": c.get("date",""),
                             "title": c.get("title",""), "data": c})

    print(f"✓ Knowledge base: {len(docs)} documents loaded")
    return docs


# ─────────────────────────────────────────────────────────────────────────────
# RAG — FAISS initialisation
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
        faiss_index = faiss.IndexFlatIP(dim)
        faiss_index.add(vecs.astype("float32"))
        print(f"✓ FAISS index built  ({len(knowledge_docs)} vectors, dim={dim})")
        return True
    except Exception as e:
        print(f"⚠ FAISS failed: {e}"); return False


def retrieve(qa: QueryAnalysis, top_k: int = TOP_K) -> List[Tuple[Dict, float]]:
    if embeddings_model is None or faiss_index is None:
        return []
    search_text = qa.expanded if qa.expanded.strip() else qa.original
    q_vec = embeddings_model.encode([search_text], normalize_embeddings=True).astype("float32")
    scores, indices = faiss_index.search(q_vec, top_k)
    return [(knowledge_docs[idx], float(score))
            for score, idx in zip(scores[0], indices[0]) if idx < len(knowledge_docs)]


# ─────────────────────────────────────────────────────────────────────────────
# Timetable data & HTML builders
# ─────────────────────────────────────────────────────────────────────────────
_TT_DATA: Dict = {}

def load_timetable_data():
    global _TT_DATA
    if os.path.exists("aids_timetable_data.json"):
        with open("aids_timetable_data.json","r",encoding="utf-8") as f:
            _TT_DATA = json.load(f)

SLOT_ORDER = ["9-10","10-11","11-12","9-12","10-12","1-2","2-3","3-4","4-5","1-4","2-4","2-5","3-5"]
DAYS_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
SUBJECT_FULL = {
    # 1st Year
    "LAC":"Linear Algebra & Calculus",
    "EP":"Engineering Physics",
    "BEEE":"Basic Electrical & Electronics Engineering",
    "CP LAB":"Computer Programming Lab",
    "EP-LAB":"Engineering Physics Lab",
    "EEE WS":"EEE Workshop",
    "IT WS":"IT Workshop",
    "NGCS":"NSS/NCC/Community Service",
    "ENGINEERING GRAPHICS":"Engineering Graphics",
    "INTRODUCTION TO PROGRAMMING":"Introduction to Programming",
    # 2nd Year
    "AI":"Artificial Intelligence",
    "IDS":"Introduction to Data Science",
    "DL_CO":"Digital Logic & Computer Organization",
    "BE":"Business Environment",
    "SMDS":"Statistical Methods for Data Science",
    "DTI LAB":"Design Thinking & Innovation Lab",
    "IDS LAB":"Introduction to Data Science Lab",
    "AI LAB":"Artificial Intelligence Lab",
    "FULL STACK DEVELOPMENT LAB":"Full Stack Development Lab",
    # 3rd Year
    "SNA":"Social Network Analysis",
    "BDA":"Big Data Analytics",
    "AIF":"AI for Finance",
    "NLP":"Natural Language Processing",
    "DL":"Deep Learning",
    "AWPS":"Academic Writing and Public Speaking",
    "TPW.IPR":"Technical Paper Writing & IPR",
    "DL LAB":"Deep Learning Lab",
    "BD and DV LAB":"Big Data & Data Visualization Lab",
    "WORKSHOP":"Workshop",
    "SOFT SKILLS LAB":"Soft Skills Lab",
}

_TH_TT = 'style="border:1px solid #ccc;padding:10px 13px;text-align:center;font-size:12px;font-weight:700"'
_TD_TT = 'style="border:1px solid #ccc;padding:9px 11px;text-align:center;font-size:12px"'
_TD_TIME = 'style="border:1px solid #ccc;padding:9px 11px;font-weight:700;background:#f0f4ff;font-size:12px;white-space:nowrap"'
_TD_EMPTY = 'style="border:1px solid #ccc;padding:9px 11px;text-align:center;background:#fafafa;color:#bbb;font-size:12px"'

_SUBJ_COLORS = {
    # 1st Year
    "LAC":"#e8f4fd","EP":"#fef9e7","BEEE":"#fdf2f8","CP LAB":"#e8f8f5",
    "EP-LAB":"#fef5e4","EEE WS":"#f4ecf7","IT WS":"#eafaf1",
    "NGCS":"#fdfefe","ENGINEERING GRAPHICS":"#f0f3ff",
    "INTRODUCTION TO PROGRAMMING":"#fff3e0",
    # 2nd Year
    "AI":"#e3f2fd","IDS":"#f3e5f5","DL_CO":"#e8f5e9","BE":"#fff8e1",
    "SMDS":"#fce4ec","DTI LAB":"#ffe0b2","IDS LAB":"#e8eaf6",
    "AI LAB":"#e0f7fa","FULL STACK DEVELOPMENT LAB":"#f9fbe7",
    # 3rd Year
    "SNA":"#e8f5e9","BDA":"#fff3e0","AIF":"#e3f2fd","NLP":"#f3e5f5",
    "DL":"#fce4ec","AWPS":"#fff8e1","TPW.IPR":"#f1f8e9",
    "DL LAB":"#e8eaf6","BD and DV LAB":"#e0f7fa",
    "WORKSHOP":"#ffe0b2","SOFT SKILLS LAB":"#f9fbe7",
}

def _cell(val):
    if val == "-":
        return f'<td {_TD_EMPTY}>—</td>'
    bg = "#fff"
    for code, colour in _SUBJ_COLORS.items():
        if code in val:
            bg = colour; break
    return f'<td style="border:1px solid #ccc;padding:9px 11px;text-align:center;background:{bg};font-size:12px">{val}</td>'


def build_section_week_table(section_key):
    tt   = _TT_DATA.get("timetable",{})
    data = tt.get(section_key,{})
    if not data:
        return f'<p style="font-family:Segoe UI,sans-serif">No timetable found for {section_key.replace("_"," ")}.</p>'
    all_slots = set()
    for dd in data.values(): all_slots.update(dd.keys())
    slots = sorted(all_slots, key=lambda x: SLOT_ORDER.index(x) if x in SLOT_ORDER else 99)
    label = section_key.replace("_"," ")
    year_label = "3rd Year · 2nd Semester" if "3rd_Year" in section_key else \
                 "2nd Year · 2nd Semester" if "2nd_Year" in section_key else \
                 "1st Year · 1st Semester"
    day_headers = "".join(f'<th {_TH_TT}>{d}</th>' for d in DAYS_ORDER)
    header = (f'<tr style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff">'
              f'<th {_TH_TT}>Time</th>{day_headers}</tr>')
    rows = ""
    for slot in slots:
        cells = "".join(_cell(data.get(day,{}).get(slot,"-")) for day in DAYS_ORDER)
        rows += f'<tr><td {_TD_TIME}>{slot}</td>{cells}</tr>'
    legend = " &nbsp;|&nbsp; ".join(f"<b>{k}</b> = {v}" for k,v in SUBJECT_FULL.items())
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0;display:flex;justify-content:space-between;align-items:center">
    <b>📅 AI &amp; DS — {label} Weekly Timetable</b>
    <span style="font-size:11px;opacity:.85">{year_label}</span>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse;min-width:720px">
      <thead>{header}</thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <div style="margin-top:6px;padding:8px 12px;background:#f8f9fa;border-radius:6px;font-size:10px;color:#555;line-height:1.8">{legend}</div>
</div>"""


def build_day_table(section_key, day):
    tt   = _TT_DATA.get("timetable",{})
    data = tt.get(section_key,{}).get(day,{})
    if not data:
        return f'<p style="font-family:Segoe UI,sans-serif">No classes for {section_key.replace("_"," ")} on {day}.</p>'
    slots = sorted(data.keys(), key=lambda x: SLOT_ORDER.index(x) if x in SLOT_ORDER else 99)
    label = section_key.replace("_"," ")
    rows  = "".join(f'<tr><td {_TD_TIME}>{slot}</td>{_cell(data[slot])}</tr>' for slot in slots)
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0">
    <b>📅 {label} — {day} Schedule</b>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse">
      <thead><tr style="background:#f0f4ff">
        <th {_TH_TT}>Time Slot</th><th {_TH_TT}>Subject</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


def build_subject_table(subject_code, section_key=None):
    tt = _TT_DATA.get("timetable",{})
    # Search all sections across all years, or just the specified one
    sections = [section_key] if section_key else list(tt.keys())
    rows = ""
    for sec in sections:
        for day in DAYS_ORDER:
            for slot, val in tt.get(sec,{}).get(day,{}).items():
                if subject_code in val:
                    sec_label = sec.replace("_"," ")
                    rows += (f'<tr><td {_TD_TT}>{sec_label}</td>'
                             f'<td {_TD_TT}>{day}</td>'
                             f'<td {_TD_TIME}>{slot}</td>'
                             f'{_cell(val)}</tr>')
    if not rows:
        return f'<p style="font-family:Segoe UI,sans-serif">No <b>{subject_code}</b> classes found.</p>'
    full_name = SUBJECT_FULL.get(subject_code, subject_code)
    scope = section_key.replace("_"," ") if section_key else "All Sections"
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0">
    <b>📚 {full_name} ({subject_code}) — {scope}</b>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse">
      <thead><tr style="background:#f0f4ff">
        <th {_TH_TT}>Section</th><th {_TH_TT}>Day</th><th {_TH_TT}>Time</th><th {_TH_TT}>Subject</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""


def build_all_sections_overview(year: int = 1):
    tt = _TT_DATA.get("timetable",{})
    if year == 3:
        sections = ["3rd_Year_Section_A","3rd_Year_Section_B"]
        title = "3rd Year — All Sections Overview"
    elif year == 2:
        sections = ["2nd_Year_Section_A","2nd_Year_Section_B"]
        title = "2nd Year — All Sections Overview"
    else:
        sections = ["1st_Year_Section_A","1st_Year_Section_B","1st_Year_Section_C","1st_Year_Section_D"]
        title = "1st Year — All Sections Overview"
    day_headers = "".join(f'<th {_TH_TT}>{d[:3]}</th>' for d in DAYS_ORDER)
    header = (f'<tr style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff">'
              f'<th {_TH_TT}>Section</th>{day_headers}</tr>')
    rows = ""
    for sec in sections:
        cells = ""
        for day in DAYS_ORDER:
            day_data = tt.get(sec,{}).get(day,{})
            if day_data:
                code = list(day_data.values())[0].split("(")[0].strip()
                cells += f'<td style="border:1px solid #ccc;padding:7px 9px;text-align:center;font-size:11px">{code}</td>'
            else:
                cells += f'<td {_TD_EMPTY}>—</td>'
        label = sec.replace("_"," ").replace("1st Year ","").replace("2nd Year ","")
        rows += (f'<tr><td style="border:1px solid #ccc;padding:9px;font-weight:700;'
                 f'background:#f0f4ff;font-size:12px">{label}</td>{cells}</tr>')
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0">
    <b>📅 AI &amp; DS — {title}</b>
  </div>
  <div style="overflow-x:auto;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse">
      <thead>{header}</thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <p style="font-size:11px;color:#888;margin-top:5px;font-family:Segoe UI,sans-serif">
    Ask "2nd year Section A timetable" or "1st year Section B Monday" for full details.
  </p>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Timetable query parser
# ─────────────────────────────────────────────────────────────────────────────
def parse_timetable_query(qa: QueryAnalysis) -> Dict:
    q = qa.original.lower().strip()
    result = {"section": None, "day": None, "subject": None, "year": None}

    # ── Year detection (do this FIRST) ───────────────────────────────────
    year_map = {
        "1st year": 1, "first year": 1, "1 year": 1, "year 1": 1, "i year": 1,
        "2nd year": 2, "second year": 2, "2 year": 2, "year 2": 2, "ii year": 2,
        "3rd year": 3, "third year": 3, "3 year": 3, "year 3": 3, "iii year": 3,
        "4th year": 4, "fourth year": 4, "4 year": 4, "year 4": 4,
    }
    for phrase, yr in year_map.items():
        if phrase in q:
            result["year"] = yr
            break
    if result["year"] is None:
        m = re.search(r'\b([1-4])\s*(?:st|nd|rd|th)?\s*year\b', q)
        if m:
            result["year"] = int(m.group(1))

    # ── Section detection ─────────────────────────────────────────────────
    sec_patterns = [
        (r"\bsection\s*a\b|\bsec\s*a\b|\bsect\s*a\b", "A"),
        (r"\bsection\s*b\b|\bsec\s*b\b|\bsect\s*b\b", "B"),
        (r"\bsection\s*c\b|\bsec\s*c\b|\bsect\s*c\b", "C"),
        (r"\bsection\s*d\b|\bsec\s*d\b|\bsect\s*d\b", "D"),
    ]
    sec_letter = None
    for pattern, letter in sec_patterns:
        if re.search(pattern, q):
            sec_letter = letter
            break

    # Build full section key from year + letter
    if sec_letter:
        yr = result["year"]
        if yr == 3:
            result["section"] = f"3rd_Year_Section_{sec_letter}"
        elif yr == 2:
            result["section"] = f"2nd_Year_Section_{sec_letter}"
        else:
            result["section"] = f"1st_Year_Section_{sec_letter}"

    # ── Day detection ─────────────────────────────────────────────────────
    for day in DAYS_ORDER:
        if day.lower() in q:
            result["day"] = day
            break

    # ── Subject detection (only when no section) ──────────────────────────
    if result["section"] is None:
        subject_aliases = [
            # 1st year
            ("linear algebra","LAC"),("calculus","LAC"),(" lac ","LAC"),
            ("engineering physics","EP"),(" ep ","EP"),("physics lab","EP-LAB"),
            ("ep-lab","EP-LAB"),("ep lab","EP-LAB"),
            ("basic electrical","BEEE"),("beee","BEEE"),("electrical","BEEE"),
            ("cp lab","CP LAB"),("programming lab","CP LAB"),
            ("eee workshop","EEE WS"),("eee ws","EEE WS"),
            ("it workshop","IT WS"),("it ws","IT WS"),
            ("engineering graphics","ENGINEERING GRAPHICS"),("graphics","ENGINEERING GRAPHICS"),
            ("introduction to programming","INTRODUCTION TO PROGRAMMING"),
            ("ngcs","NGCS"),(" nss ","NGCS"),(" ncc ","NGCS"),
            # 2nd year
            ("artificial intelligence"," AI "),(" ai ","AI"),
            ("introduction to data science","IDS"),(" ids ","IDS"),
            ("digital logic","DL_CO"),("dl_co","DL_CO"),("dl co","DL_CO"),
            ("computer organization","DL_CO"),
            ("business environment","BE"),
            ("statistical methods","SMDS"),("smds","SMDS"),
            ("design thinking","DTI LAB"),("dti lab","DTI LAB"),("dti","DTI LAB"),
            ("ids lab","IDS LAB"),("data science lab","IDS LAB"),
            ("ai lab","AI LAB"),
            ("full stack","FULL STACK DEVELOPMENT LAB"),("fullstack","FULL STACK DEVELOPMENT LAB"),
            # 3rd year
            ("social network","SNA"),(" sna ","SNA"),
            ("big data analytics","BDA"),(" bda ","BDA"),
            ("ai for finance","AIF"),(" aif ","AIF"),
            ("natural language processing","NLP"),(" nlp ","NLP"),
            ("deep learning","DL"),(" dl ","DL"),
            ("academic writing","AWPS"),("awps","AWPS"),("public speaking","AWPS"),
            ("technical paper","TPW.IPR"),("tpw","TPW.IPR"),("ipr","TPW.IPR"),
            ("dl lab","DL LAB"),("deep learning lab","DL LAB"),
            ("bd and dv lab","BD and DV LAB"),("data visualization lab","BD and DV LAB"),
            ("soft skills","SOFT SKILLS LAB"),("workshop","WORKSHOP"),
        ]
        padded = f" {q} "
        for alias, code in subject_aliases:
            if alias in padded:
                result["subject"] = code.strip()
                break

    return result


def handle_timetable_query(qa: QueryAnalysis) -> str:
    parsed  = parse_timetable_query(qa)
    section = parsed["section"]
    day     = parsed["day"]
    subject = parsed["subject"]
    year    = parsed["year"]

    if section and day:   return build_day_table(section, day)
    if section:           return build_section_week_table(section)
    if subject:           return build_subject_table(subject)

    q = qa.original.lower()
    if any(w in q for w in ["all section","all timetable","every section","overview"]):
        if year == 3:
            return build_all_sections_overview(year=3)
        elif year == 2:
            return build_all_sections_overview(year=2)
        else:
            return build_all_sections_overview(year=1)

    # Prompt user with year + section selection table
    return """
<div style="font-family:'Segoe UI',sans-serif;padding:12px 16px;background:#fff;border:1px solid #ddd;border-radius:10px">
  <b style="color:#667eea;font-size:14px">📅 Please specify the year and section:</b>
  <table style="margin-top:10px;border-collapse:collapse;width:100%">
    <thead>
      <tr style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff">
        <th style="padding:9px 14px;text-align:left;font-size:13px">Year</th>
        <th style="padding:9px 14px;text-align:left;font-size:13px">Command</th>
        <th style="padding:9px 14px;text-align:left;font-size:13px">What you get</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background:#f8f9ff"><td style="padding:8px 14px;font-size:13px;font-weight:700;color:#667eea" rowspan="4">1st Year</td><td style="padding:8px 14px;font-size:13px"><b>1st year Section A timetable</b></td><td style="padding:8px 14px;font-size:13px">Full week — 1st Year Sec A</td></tr>
      <tr><td style="padding:8px 14px;font-size:13px"><b>1st year Section B timetable</b></td><td style="padding:8px 14px;font-size:13px">Full week — 1st Year Sec B</td></tr>
      <tr style="background:#f8f9ff"><td style="padding:8px 14px;font-size:13px"><b>1st year Section C timetable</b></td><td style="padding:8px 14px;font-size:13px">Full week — 1st Year Sec C</td></tr>
      <tr><td style="padding:8px 14px;font-size:13px"><b>1st year Section D timetable</b></td><td style="padding:8px 14px;font-size:13px">Full week — 1st Year Sec D</td></tr>
      <tr style="background:#e8eaf6"><td style="padding:8px 14px;font-size:13px;font-weight:700;color:#764ba2" rowspan="2">2nd Year</td><td style="padding:8px 14px;font-size:13px"><b>2nd year Section A timetable</b></td><td style="padding:8px 14px;font-size:13px">Full week — 2nd Year Sec A</td></tr>
      <tr style="background:#f3e5f5"><td style="padding:8px 14px;font-size:13px"><b>2nd year Section B timetable</b></td><td style="padding:8px 14px;font-size:13px">Full week — 2nd Year Sec B</td></tr>
      <tr style="background:#e8f5e9"><td style="padding:8px 14px;font-size:13px;font-weight:700;color:#2e7d32" rowspan="2">3rd Year</td><td style="padding:8px 14px;font-size:13px"><b>3rd year Section A timetable</b></td><td style="padding:8px 14px;font-size:13px">Full week — 3rd Year Sec A</td></tr>
      <tr style="background:#f1f8e9"><td style="padding:8px 14px;font-size:13px"><b>3rd year Section B timetable</b></td><td style="padding:8px 14px;font-size:13px">Full week — 3rd Year Sec B</td></tr>
      <tr style="background:#f8f9ff"><td style="padding:8px 14px;font-size:13px;font-weight:700;color:#555" colspan="1">Any year</td><td style="padding:8px 14px;font-size:13px"><b>Section A Monday</b></td><td style="padding:8px 14px;font-size:13px">Single day schedule</td></tr>
      <tr><td style="padding:8px 14px;font-size:13px;font-weight:700;color:#555"></td><td style="padding:8px 14px;font-size:13px"><b>AI Lab schedule</b></td><td style="padding:8px 14px;font-size:13px">Subject across all sections</td></tr>
    </tbody>
  </table>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Answer synthesis — RAG context → structured HTML
# ─────────────────────────────────────────────────────────────────────────────
def _fuzzy_name_match(query_name: str, faculty_name: str) -> float:
    """
    Score how well query_name matches faculty_name.
    Returns 0.0–1.0. Uses token overlap + substring checks.
    """
    from difflib import SequenceMatcher
    q = query_name.lower().strip()
    f = faculty_name.lower().strip()

    # Exact full match
    if q == f:
        return 1.0

    # Full substring
    if q in f or f in q:
        return 0.95

    # Token overlap — split both into parts, count matches
    q_parts = [p for p in re.split(r'\s+', q) if len(p) > 1]
    f_parts = [p for p in re.split(r'\s+', f) if len(p) > 1]

    if not q_parts:
        return 0.0

    matched = sum(1 for qp in q_parts if any(qp in fp or fp in qp for fp in f_parts))
    token_score = matched / len(q_parts)

    # Sequence similarity as tiebreaker
    seq_score = SequenceMatcher(None, q, f).ratio()

    return max(token_score, seq_score)


def _find_faculty_by_name(query: str) -> Optional[Dict]:
    """
    Find the single best-matching faculty member for a name query.
    Returns None if no match scores above 0.35.
    """
    best_score = 0.0
    best_match = None

    # Extract candidate name from query — strip common prefixes
    name_query = re.sub(
        r'\b(who is|tell me about|about|details of|info on|information about|'
        r'show me|find|search|get|what does|what is the specialization of|'
        r'qualification of|designation of)\b',
        '', query, flags=re.IGNORECASE
    ).strip()

    for f in _FACULTY_DATA:
        score = _fuzzy_name_match(name_query, f.get("name", ""))
        if score > best_score:
            best_score = score
            best_match = f

    return best_match if best_score >= 0.35 else None


def synthesize_answer(qa: QueryAnalysis, docs_with_scores: List[Tuple[Dict,float]], intent: str) -> Optional[str]:
    if not docs_with_scores or docs_with_scores[0][1] < CONFIDENCE_THRESHOLD:
        return None
    q = qa.original.lower()

    # ── Faculty intent ────────────────────────────────────────────────────
    if intent == "faculty":
        # 1. HOD / head query
        if any(w in q for w in ["hod","head of department","head of dept","head of the"]):
            hod = next((f for f in _FACULTY_DATA if "head" in f.get("designation","").lower()), None)
            if hod: return build_faculty_card(hod)

        # 2. Specific person — try NER extracted names first
        if qa.person_names:
            for pname in qa.person_names:
                match = _find_faculty_by_name(pname)
                if match:
                    return build_faculty_card(match)

        # 3. Specific person — fuzzy match on the whole query
        #    Only do this when query looks like a name lookup (not "list all")
        list_signals = {"list","all","show","every","members","staff","teachers","lecturers","how many"}
        is_list_query = bool(set(qa.tokens) & list_signals) or any(
            w in q for w in ["list","all faculty","faculty members","show faculty",
                             "who are","how many","all staff"]
        )

        if not is_list_query:
            name_match = _find_faculty_by_name(qa.original)
            if name_match:
                return build_faculty_card(name_match)

            # Also try individual tokens as partial names
            for tok in qa.tokens:
                if len(tok) > 3:
                    for f in _FACULTY_DATA:
                        if tok in f.get("name","").lower():
                            return build_faculty_card(f)

        # 4. Specialization query
        spec_map = {
            "Machine Learning":        ["machine","learn","ml"],
            "Deep Learning":           ["deep","learn","dl"],
            "Artificial Intelligence": ["artificial","intelligence","ai"],
            "Python Programming":      ["python"],
            "Computer Networks":       ["network","cn"],
            "Software Engineering":    ["software","engineer"],
            "DBMS / Database":         ["dbms","database"],
            "Computer Science":        ["computer","science","cs"],
        }
        for spec_label, lemmas in spec_map.items():
            if any(lm in qa.tokens for lm in lemmas) or spec_label.lower() in q:
                matched = [f for f in _FACULTY_DATA
                           if any(lm in f.get("specialization","").lower() for lm in lemmas)]
                if matched: return build_specialization_table(spec_label, matched)

        # 5. Explicit list request → full table
        if is_list_query:
            return build_faculty_list_table()

        # 6. Fallback: full list only if nothing else matched
        return build_faculty_list_table()

    # ── Timetable (safety fallback) ───────────────────────────────────────
    if intent == "timetable":
        return handle_timetable_query(qa)

    # ── Services / general — structured info card ─────────────────────────
    top_texts = [d["text"] for d, s in docs_with_scores[:4] if s >= CONFIDENCE_THRESHOLD]
    if not top_texts:
        return None

    seen, rows = set(), []
    for text in top_texts:
        for sentence in re.split(r"[.\n]", text):
            s = sentence.strip()
            if s and s not in seen and len(s) > 12:
                seen.add(s)
                rows.append(s)

    if not rows:
        return None

    # Render as a structured info table
    row_html = "".join(
        f'<tr style="background:{"#f8f9ff" if i%2==0 else "#fff"}">'
        f'<td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;color:#333">{r}</td></tr>'
        for i, r in enumerate(rows[:6])
    )
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0">
    <b>ℹ️ Information</b>
  </div>
  <div style="border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;overflow:hidden">
    <table style="width:100%;border-collapse:collapse">
      <tbody>{row_html}</tbody>
    </table>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# Structured HTML for static responses
# ─────────────────────────────────────────────────────────────────────────────
def _info_card(title: str, rows: List[Tuple[str,str]]) -> str:
    """Render a two-column key/value card."""
    row_html = "".join(
        f'<tr style="background:{"#f8f9ff" if i%2==0 else "#fff"}">'
        f'<td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#555;white-space:nowrap;width:180px">{k}</td>'
        f'<td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;color:#333">{v}</td></tr>'
        for i,(k,v) in enumerate(rows)
    )
    return f"""
<div style="margin:8px 0;font-family:'Segoe UI',sans-serif">
  <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0">
    <b>{title}</b>
  </div>
  <div style="border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;overflow:hidden">
    <table style="width:100%;border-collapse:collapse"><tbody>{row_html}</tbody></table>
  </div>
</div>"""


def _help_table() -> str:
    rows = [
        ("📅 Timetables",  "1st/2nd/3rd Year Section A/B/C/D weekly schedules"),
        ("👥 Faculty",     "Names, designations, specializations, qualifications"),
        ("📢 Circulars",   "Notices, announcements, fee circulars — try: 'show circulars'"),
        ("💻 Services",    "Attendance, e-journals, assessments, portal login"),
        ("📚 Academics",   "Courses, admissions, exams, library, hostel"),
        ("🏢 About NBKR",  "Institute overview, departments, facilities"),
    ]
    return _info_card("💡 What I can help you with", rows)


# ─────────────────────────────────────────────────────────────────────────────
# Main response function
# ─────────────────────────────────────────────────────────────────────────────
def get_response(query: str, conn_id: str = "default") -> str:
    query = query.strip()
    if not query:
        return _info_card("⚠️ Empty Query", [("Tip","Please type a question.")])

    qa     = analyse_query(query)
    intent = detect_intent(query, qa)

    # ── Static intents ────────────────────────────────────────────────────
    if intent == "greeting":
        return _info_card("👋 Hello! I'm the NBKR AI &amp; DS Assistant", [
            ("📅 Timetables", 'Try: "2nd year Section A timetable"'),
            ("👥 Faculty",    'Try: "Who is the HOD?"'),
            ("📢 Circulars",  'Try: "Show circulars" or "fee notice"'),
            ("💻 Services",   'Try: "How to check attendance?"'),
            ("💡 Tip",        "I'll tell you honestly if I don't know something."),
        ])

    if intent == "farewell":
        return _info_card("😊 You're Welcome!", [
            ("Status","Happy to help anytime."),
            ("Tip","Come back if you have more questions about NBKR Institute."),
        ])

    if intent == "help":
        return _help_table()

    # ── Circulars / Announcements ─────────────────────────────────────────
    if intent == "circulars":
        q_lower = query.lower()
        # Specific circular by ID
        for c in _CIRCULARS:
            if c.get("id","").lower() in q_lower:
                return build_circular_card(c)
        # Latest circular
        if any(w in q_lower for w in ["latest","recent","new","last","current"]):
            if _CIRCULARS:
                return build_circular_card(_CIRCULARS[-1])
        # Fee / early bird / commencement specific
        if any(w in q_lower for w in ["fee","tuition","early bird","payment","pay",
                                       "commencement","start","enrolment","enroll"]):
            for c in _CIRCULARS:
                if any(k in c.get("content","").lower()
                       for k in ["fee","tuition","early bird","commencement"]):
                    return build_circular_card(c)
        # Default: show all circulars table
        return build_all_circulars_table()

    # ── Timetable — direct handler, no RAG ───────────────────────────────
    if intent == "timetable":
        return handle_timetable_query(qa)

    # ── Faculty — try direct name lookup BEFORE RAG ───────────────────────
    if intent == "faculty":
        q_lower = query.lower()
        # HOD shortcut
        if any(w in q_lower for w in ["hod","head of department","head of dept"]):
            hod = next((f for f in _FACULTY_DATA if "head" in f.get("designation","").lower()), None)
            if hod:
                return build_faculty_card(hod)
        # Name lookup — skip if it's clearly a list request
        list_signals = {"list","all","show","every","members","staff","teachers","lecturers","how many"}
        is_list = bool(set(qa.tokens) & list_signals) or any(
            w in q_lower for w in ["list","all faculty","faculty members","show faculty","who are","how many"]
        )
        if not is_list:
            direct = _find_faculty_by_name(query)
            if direct:
                return build_faculty_card(direct)

    # ── RAG retrieval ─────────────────────────────────────────────────────
    results = retrieve(qa, top_k=TOP_K)

    if not results:
        return _info_card("❓ Not Found", [
            ("Query", query),
            ("Suggestion","Ask about NBKR AI &amp; DS faculty, timetables, or services."),
        ])

    answer = synthesize_answer(qa, results, intent)

    if answer is None:
        best_score = results[0][1] if results else 0
        if best_score < 0.20:
            return _info_card("🤷 Out of Scope", [
                ("Query",      query),
                ("Confidence", f"{best_score:.2f} (below threshold)"),
                ("Suggestion", "Try asking about faculty, timetables, or institute services."),
            ])
        return _info_card("❓ Insufficient Information", [
            ("Query",      query),
            ("Suggestion", "Could you rephrase or ask something more specific about NBKR Institute?"),
        ])

    return answer


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("🎓 NBKR Institute AI Chatbot v6.0 — RAG + NLP + ML")
    print("=" * 70)
    initialize_nlp()
    train_ml_classifier()
    load_timetable_data()
    load_faculty_data()
    load_circulars()
    ok = initialize_rag()
    print("✓ RAG ready" if ok else "⚠ RAG unavailable — check data files")
    # Reload any admin-uploaded knowledge into FAISS
    try:
        from admin_panel import load_updates, chunk_text, add_to_live_index
        updates = load_updates()
        if updates:
            total = 0
            for u in updates:
                text = u.get("text","")
                if text:
                    total += add_to_live_index(chunk_text(text), u)
            print(f"✓ Admin updates reloaded: {len(updates)} entries, {total} vectors")
    except Exception as e:
        print(f"⚠ Admin updates reload skipped: {e}")
    print("=" * 70)
    yield

app = FastAPI(title="NBKR RAG+NLP+ML Chatbot v6", version="6.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Mount Admin Panel ─────────────────────────────────────────────────────────
from admin_panel import admin_app
app.mount("/admin", admin_app)


@app.get("/")
async def home():
    html = """<!DOCTYPE html>
<html>
<head>
  <title>NBKR AI Chatbot</title>
  <meta charset="utf-8">
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);height:100vh;display:flex;justify-content:center;align-items:center}
    .wrap{width:92%;max-width:960px;height:93vh;background:#fff;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,.3);display:flex;flex-direction:column;overflow:hidden}
    .hdr{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:16px 20px;text-align:center}
    .hdr h1{font-size:21px;margin-bottom:3px}
    .hdr p{font-size:12px;opacity:.9}
    .badge{display:inline-block;background:rgba(255,255,255,.2);padding:3px 10px;border-radius:10px;font-size:10px;margin:2px}
    .status{padding:7px 20px;text-align:center;font-size:12px;color:#888;background:#fafafa;border-bottom:1px solid #eee}
    .status.on{color:#4caf50}
    .msgs{flex:1;padding:16px;overflow-y:auto;background:#f0f2f5;display:flex;flex-direction:column;gap:12px}
    .msg{display:flex}
    .msg.user{justify-content:flex-end}
    .bubble{max-width:75%;padding:11px 15px;border-radius:18px;word-wrap:break-word;line-height:1.55;font-size:14px;animation:pop .22s ease}
    @keyframes pop{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
    .msg.bot .bubble{background:#fff;color:#333;border-bottom-left-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,.1);max-width:90%}
    .msg.user .bubble{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-bottom-right-radius:4px;white-space:pre-wrap}
    .inp-row{padding:14px 18px;background:#fff;border-top:1px solid #e8e8e8;display:flex;gap:10px}
    .inp{flex:1;padding:11px 16px;border:2px solid #e0e0e0;border-radius:25px;font-size:14px;outline:none;transition:border-color .2s}
    .inp:focus{border-color:#667eea}
    .btn{padding:11px 24px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border:none;border-radius:25px;cursor:pointer;font-size:14px;font-weight:600;transition:transform .15s}
    .btn:hover{transform:scale(1.04)}
    .dot{display:inline-block;width:6px;height:6px;background:#aaa;border-radius:50%;margin:0 2px;animation:blink 1.2s infinite}
    .dot:nth-child(2){animation-delay:.2s}.dot:nth-child(3){animation-delay:.4s}
    @keyframes blink{0%,80%,100%{opacity:0}40%{opacity:1}}
    /* Table styles inside bubbles */
    .bubble table{border-collapse:collapse;width:100%}
    .bubble th,.bubble td{border:1px solid #ddd;padding:8px 12px;font-size:12px}
  </style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>🎓 NBKR Institute AI Chatbot</h1>
    <p>AI &amp; DS Department Assistant — RAG + NLP + ML</p>
    <div style="margin-top:6px">
      <span class="badge">🤖 ML Classifier</span>
      <span class="badge">🔍 RAG v6</span>
      <span class="badge">🧠 Sentence Transformers</span>
      <span class="badge">📊 FAISS Cosine</span>
      <span class="badge">🔤 spaCy NLP</span>
    </div>
  </div>
  <div class="status" id="st">Connecting…</div>
  <div class="msgs" id="msgs">
    <div class="msg bot"><div class="bubble">
      <div style="font-family:'Segoe UI',sans-serif">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 16px;border-radius:8px 8px 0 0"><b>👋 Hello! I'm the NBKR AI &amp; DS Assistant</b></div>
        <div style="border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px;overflow:hidden">
          <table style="width:100%;border-collapse:collapse">
            <tr style="background:#f8f9ff"><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#555;width:180px">📅 Timetables</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px">Try: "Show Section A timetable"</td></tr>
            <tr><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#555">👥 Faculty</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px">Try: "Who is the HOD?"</td></tr>
            <tr style="background:#f8f9ff"><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#555">💻 Services</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px">Try: "How to check attendance?"</td></tr>
            <tr><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px;font-weight:700;color:#555">💡 Tip</td><td style="border:1px solid #ddd;padding:9px 14px;font-size:13px">I'll tell you honestly if I don't know something.</td></tr>
          </table>
        </div>
      </div>
    </div></div>
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
    const proto=location.protocol==='https:'?'wss:':'ws:';
    ws=new WebSocket(proto+'//'+location.host+'/ws');
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
    if(who==='bot'){
      // Always render bot messages as HTML (tables, cards, etc.)
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
    d.innerHTML='<div style="padding:10px 14px;background:#fff;border-radius:18px;border-bottom-left-radius:4px;box-shadow:0 2px 6px rgba(0,0,0,.1);font-size:13px;color:#888"><span class=\\"dot\\"></span><span class=\\"dot\\"></span><span class=\\"dot\\"></span></div>';
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
            raw      = await websocket.receive_text()
            data     = json.loads(raw)
            user_msg = data.get("message","").strip()
            chat_history.append({"ts":datetime.now().isoformat(),"user":user_msg,"bot":None})
            response = get_response(user_msg, conn_id)
            chat_history[-1]["bot"] = response
            await websocket.send_json({"message":response,"timestamp":datetime.now().isoformat()})
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/health")
async def health():
    return {
        "status":       "healthy",
        "version":      "6.0.0",
        "nlp_enabled":  nlp is not None,
        "ml_enabled":   ml_classifier is not None,
        "rag_enabled":  faiss_index is not None,
        "documents":    len(knowledge_docs),
        "threshold":    CONFIDENCE_THRESHOLD,
    }


if __name__ == "__main__":
    print("\n🚀 Starting NBKR RAG+NLP+ML Chatbot v6.0 …")
    print("📍 http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
