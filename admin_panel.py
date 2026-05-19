"""
admin_panel.py — NBKR Admin Dynamic Knowledge Update System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Architecture:
  Admin UI  →  FastAPI endpoints  →  Document Processor
      →  Chunker  →  Embedder (sentence-transformers)
      →  FAISS hot-reload  →  Chatbot answers instantly

Features:
  • Admin login (JWT token, hardcoded credentials — extend with DB)
  • Upload: PDF, DOCX, TXT, plain text paste
  • Auto extract text (pdfplumber / python-docx / plain)
  • Chunk text into 300-word overlapping segments
  • Generate embeddings via sentence-transformers
  • Append to live FAISS index (no restart needed)
  • Persist new docs to knowledge_updates.json
  • View / delete uploaded knowledge entries
  • Full audit log of all admin actions
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import List, Optional
import json, os, re, hashlib, io
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
ADMIN_CREDENTIALS = {
    "admin":    hashlib.sha256("nbkr@admin2026".encode()).hexdigest(),
    "hod":      hashlib.sha256("hod@aids2026".encode()).hexdigest(),
    "principal":hashlib.sha256("principal@nbkr2026".encode()).hexdigest(),
}
JWT_SECRET   = "nbkr-admin-secret-key-2026"
JWT_EXPIRE_H = 8
UPDATES_FILE = "knowledge_updates.json"
AUDIT_FILE   = "admin_audit.json"
UPLOAD_DIR   = "admin_uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Simple JWT (no external library needed)
# ─────────────────────────────────────────────────────────────────────────────
import base64, hmac, time as _time

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)

def create_token(username: str) -> str:
    header  = _b64(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    payload = _b64(json.dumps({
        "sub": username,
        "exp": int(_time.time()) + JWT_EXPIRE_H * 3600,
        "iat": int(_time.time()),
    }).encode())
    sig = _b64(hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(),
                        "sha256").digest())
    return f"{header}.{payload}.{sig}"

def verify_token(token: str) -> Optional[str]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, sig = parts
        expected = _b64(hmac.new(JWT_SECRET.encode(),
                                  f"{header}.{payload}".encode(), "sha256").digest())
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(_unb64(payload))
        if data["exp"] < int(_time.time()):
            return None
        return data["sub"]
    except Exception:
        return None

security = HTTPBearer(auto_error=False)

def get_admin(creds: HTTPAuthorizationCredentials = Depends(security)):
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = verify_token(creds.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

# ─────────────────────────────────────────────────────────────────────────────
# Audit log
# ─────────────────────────────────────────────────────────────────────────────
def audit(action: str, user: str, detail: str = ""):
    log = []
    if os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, encoding="utf-8") as f:
            log = json.load(f)
    log.append({
        "ts":     datetime.now().isoformat(),
        "user":   user,
        "action": action,
        "detail": detail,
    })
    with open(AUDIT_FILE, "w", encoding="utf-8") as f:
        json.dump(log[-500:], f, indent=2, ensure_ascii=False)  # keep last 500

# ─────────────────────────────────────────────────────────────────────────────
# Text extraction
# ─────────────────────────────────────────────────────────────────────────────
def extract_text_from_pdf(data: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
        return "\n".join(pages).strip()
    except ImportError:
        return "[pdfplumber not installed — pip install pdfplumber]"
    except Exception as e:
        return f"[PDF extraction error: {e}]"

def extract_text_from_docx(data: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return "[python-docx not installed — pip install python-docx]"
    except Exception as e:
        return f"[DOCX extraction error: {e}]"

def extract_text(filename: str, data: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return extract_text_from_pdf(data)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(data)
    else:
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                return data.decode(enc)
            except Exception:
                continue
        return data.decode("utf-8", errors="replace")

# ─────────────────────────────────────────────────────────────────────────────
# Text chunker
# ─────────────────────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """Split text into overlapping word-based chunks."""
    words  = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if len(chunk.strip()) > 20:
            chunks.append(chunk.strip())
        i += chunk_size - overlap
    return chunks

# ─────────────────────────────────────────────────────────────────────────────
# Auto-summarise (extractive — top sentences by TF score)
# ─────────────────────────────────────────────────────────────────────────────
def auto_summarize(text: str, max_sentences: int = 4) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text.strip()
    # Score by word frequency
    words = re.findall(r'\b\w+\b', text.lower())
    freq  = {}
    for w in words:
        if len(w) > 3:
            freq[w] = freq.get(w, 0) + 1
    scores = []
    for s in sentences:
        ws = re.findall(r'\b\w+\b', s.lower())
        score = sum(freq.get(w, 0) for w in ws) / max(len(ws), 1)
        scores.append(score)
    top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:max_sentences]
    top_idx.sort()
    return " ".join(sentences[i] for i in top_idx)

# ─────────────────────────────────────────────────────────────────────────────
# FAISS hot-reload — adds new vectors to the live index
# ─────────────────────────────────────────────────────────────────────────────
def add_to_live_index(chunks: List[str], meta: dict) -> int:
    """
    Encode chunks and append to the live FAISS index in rag_chatbot.py.
    Returns number of vectors added.
    """
    import rag_chatbot as rc
    if rc.embeddings_model is None or rc.faiss_index is None:
        return 0

    new_docs = []
    for chunk in chunks:
        new_docs.append({
            "text":     chunk,
            "type":     meta.get("category", "admin_upload"),
            "title":    meta.get("title", ""),
            "source":   meta.get("filename", ""),
            "added_by": meta.get("added_by", "admin"),
            "added_at": meta.get("added_at", ""),
        })

    texts = [d["text"] for d in new_docs]
    vecs  = rc.embeddings_model.encode(texts, normalize_embeddings=True).astype("float32")
    rc.faiss_index.add(vecs)
    rc.knowledge_docs.extend(new_docs)
    return len(new_docs)

# ─────────────────────────────────────────────────────────────────────────────
# Persist updates to JSON
# ─────────────────────────────────────────────────────────────────────────────
def save_update(entry: dict):
    updates = []
    if os.path.exists(UPDATES_FILE):
        with open(UPDATES_FILE, encoding="utf-8") as f:
            updates = json.load(f)
    updates.append(entry)
    with open(UPDATES_FILE, "w", encoding="utf-8") as f:
        json.dump(updates, f, indent=2, ensure_ascii=False)

def load_updates() -> List[dict]:
    if not os.path.exists(UPDATES_FILE):
        return []
    with open(UPDATES_FILE, encoding="utf-8") as f:
        return json.load(f)

def delete_update(uid: str) -> bool:
    updates = load_updates()
    new = [u for u in updates if u.get("id") != uid]
    if len(new) == len(updates):
        return False
    with open(UPDATES_FILE, "w", encoding="utf-8") as f:
        json.dump(new, f, indent=2, ensure_ascii=False)
    return True

# ─────────────────────────────────────────────────────────────────────────────
# Admin FastAPI app
# ─────────────────────────────────────────────────────────────────────────────
admin_app = FastAPI(title="NBKR Admin Panel", version="1.0.0")

# ── Login ─────────────────────────────────────────────────────────────────────
@admin_app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    if ADMIN_CREDENTIALS.get(username) != hashed:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(username)
    audit("LOGIN", username)
    return {"token": token, "username": username, "expires_in": f"{JWT_EXPIRE_H}h"}

# ── Upload file ───────────────────────────────────────────────────────────────
@admin_app.post("/upload")
async def upload_file(
    file:     UploadFile = File(...),
    title:    str        = Form(""),
    category: str        = Form("general"),
    admin:    str        = Depends(get_admin),
):
    data     = await file.read()
    filename = file.filename or "upload.txt"
    text     = extract_text(filename, data)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    summary = auto_summarize(text)
    chunks  = chunk_text(text)
    uid     = hashlib.md5(f"{filename}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    added_at = datetime.now().isoformat()

    meta = {
        "id":        uid,
        "title":     title or filename,
        "filename":  filename,
        "category":  category,
        "added_by":  admin,
        "added_at":  added_at,
        "summary":   summary,
        "chunks":    len(chunks),
        "text":      text[:5000],   # store first 5000 chars
    }

    # Save file to disk
    save_path = os.path.join(UPLOAD_DIR, f"{uid}_{filename}")
    with open(save_path, "wb") as f:
        f.write(data)

    # Add to live FAISS index
    added = add_to_live_index(chunks, meta)
    meta["vectors_added"] = added

    # Persist metadata
    save_update(meta)
    audit("UPLOAD", admin, f"file={filename}, chunks={len(chunks)}, vectors={added}")

    return {
        "status":        "success",
        "id":            uid,
        "title":         meta["title"],
        "chunks":        len(chunks),
        "vectors_added": added,
        "summary":       summary,
        "message":       f"✓ {filename} processed — {added} vectors added to live knowledge base",
    }

# ── Add text directly ─────────────────────────────────────────────────────────
@admin_app.post("/add-text")
async def add_text(
    title:    str = Form(...),
    content:  str = Form(...),
    category: str = Form("general"),
    admin:    str = Depends(get_admin),
):
    if len(content.strip()) < 10:
        raise HTTPException(status_code=400, detail="Content too short")

    summary  = auto_summarize(content)
    chunks   = chunk_text(content)
    uid      = hashlib.md5(f"{title}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    added_at = datetime.now().isoformat()

    meta = {
        "id":       uid,
        "title":    title,
        "filename": "text_input",
        "category": category,
        "added_by": admin,
        "added_at": added_at,
        "summary":  summary,
        "chunks":   len(chunks),
        "text":     content[:5000],
    }

    added = add_to_live_index(chunks, meta)
    meta["vectors_added"] = added
    save_update(meta)
    audit("ADD_TEXT", admin, f"title={title}, chunks={len(chunks)}, vectors={added}")

    return {
        "status":        "success",
        "id":            uid,
        "chunks":        len(chunks),
        "vectors_added": added,
        "summary":       summary,
        "message":       f"✓ '{title}' added — {added} vectors in live knowledge base",
    }

# ── List all updates ──────────────────────────────────────────────────────────
@admin_app.get("/updates")
async def list_updates(admin: str = Depends(get_admin)):
    updates = load_updates()
    return {
        "total": len(updates),
        "updates": [
            {
                "id":       u.get("id"),
                "title":    u.get("title"),
                "category": u.get("category"),
                "added_by": u.get("added_by"),
                "added_at": u.get("added_at"),
                "chunks":   u.get("chunks"),
                "summary":  u.get("summary","")[:200],
            }
            for u in reversed(updates)
        ],
    }

# ── Delete an update ──────────────────────────────────────────────────────────
@admin_app.delete("/updates/{uid}")
async def delete_update_entry(uid: str, admin: str = Depends(get_admin)):
    if not delete_update(uid):
        raise HTTPException(status_code=404, detail="Entry not found")
    audit("DELETE", admin, f"uid={uid}")
    return {"status": "deleted", "id": uid,
            "note": "Entry removed from store. Restart to remove from FAISS index."}

# ── Audit log ─────────────────────────────────────────────────────────────────
@admin_app.get("/audit")
async def get_audit(admin: str = Depends(get_admin)):
    if not os.path.exists(AUDIT_FILE):
        return {"logs": []}
    with open(AUDIT_FILE, encoding="utf-8") as f:
        logs = json.load(f)
    return {"total": len(logs), "logs": list(reversed(logs))[:100]}

# ── FAISS status ──────────────────────────────────────────────────────────────
@admin_app.get("/status")
async def kb_status(admin: str = Depends(get_admin)):
    import rag_chatbot as rc
    return {
        "faiss_vectors":   int(rc.faiss_index.ntotal) if rc.faiss_index else 0,
        "knowledge_docs":  len(rc.knowledge_docs),
        "circulars":       len(rc._CIRCULARS),
        "faculty":         len(rc._FACULTY_DATA),
        "updates_on_disk": len(load_updates()),
        "rag_ready":       rc.faiss_index is not None,
    }

# ── Reload updates into FAISS (on demand) ────────────────────────────────────
@admin_app.post("/reload")
async def reload_updates(admin: str = Depends(get_admin)):
    """Re-add all persisted updates to the live FAISS index."""
    updates = load_updates()
    total_added = 0
    for u in updates:
        text   = u.get("text", "")
        chunks = chunk_text(text) if text else []
        if chunks:
            added = add_to_live_index(chunks, u)
            total_added += added
    audit("RELOAD", admin, f"reloaded {len(updates)} entries, {total_added} vectors")
    return {"status": "reloaded", "entries": len(updates), "vectors_added": total_added}

# ── Admin UI ──────────────────────────────────────────────────────────────────
@admin_app.get("/", response_class=HTMLResponse)
async def admin_ui():
    return HTMLResponse(content=ADMIN_HTML)


# ─────────────────────────────────────────────────────────────────────────────
# Admin HTML UI
# ─────────────────────────────────────────────────────────────────────────────
ADMIN_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>NBKR Admin Panel</title>
  <meta charset="utf-8">
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',sans-serif;background:#f0f2f5;min-height:100vh}
    .topbar{background:linear-gradient(135deg,#1a237e,#283593);color:#fff;padding:14px 28px;display:flex;justify-content:space-between;align-items:center}
    .topbar h1{font-size:18px}
    .topbar span{font-size:12px;opacity:.8}
    #logout-btn{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px}
    .container{max-width:1100px;margin:24px auto;padding:0 20px}
    .tabs{display:flex;gap:4px;margin-bottom:20px;background:#fff;padding:6px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
    .tab{padding:9px 20px;border-radius:7px;cursor:pointer;font-size:13px;font-weight:600;color:#555;transition:all .2s}
    .tab.active{background:linear-gradient(135deg,#1a237e,#283593);color:#fff}
    .panel{display:none;background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
    .panel.active{display:block}
    /* Login */
    #login-screen{position:fixed;inset:0;background:linear-gradient(135deg,#1a237e,#283593);display:flex;align-items:center;justify-content:center;z-index:999}
    .login-box{background:#fff;border-radius:16px;padding:36px 40px;width:360px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
    .login-box h2{color:#1a237e;margin-bottom:6px;font-size:22px}
    .login-box p{color:#888;font-size:13px;margin-bottom:24px}
    .form-group{margin-bottom:16px}
    .form-group label{display:block;font-size:12px;font-weight:700;color:#555;margin-bottom:5px}
    .form-group input,.form-group textarea,.form-group select{width:100%;padding:10px 13px;border:2px solid #e0e0e0;border-radius:8px;font-size:14px;outline:none;transition:border-color .2s;font-family:inherit}
    .form-group input:focus,.form-group textarea:focus,.form-group select:focus{border-color:#1a237e}
    .form-group textarea{min-height:120px;resize:vertical}
    .btn{padding:10px 22px;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;transition:all .2s}
    .btn-primary{background:linear-gradient(135deg,#1a237e,#283593);color:#fff}
    .btn-primary:hover{opacity:.9;transform:translateY(-1px)}
    .btn-danger{background:#c62828;color:#fff}
    .btn-sm{padding:5px 12px;font-size:12px}
    .alert{padding:12px 16px;border-radius:8px;margin:12px 0;font-size:13px}
    .alert-success{background:#e8f5e9;color:#2e7d32;border-left:4px solid #4caf50}
    .alert-error{background:#ffebee;color:#c62828;border-left:4px solid #f44336}
    .alert-info{background:#e3f2fd;color:#1565c0;border-left:4px solid #2196f3}
    .section-title{font-size:15px;font-weight:700;color:#1a237e;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #e8eaf6}
    table{width:100%;border-collapse:collapse;font-size:13px}
    th{background:#e8eaf6;padding:10px 14px;text-align:left;font-weight:700;color:#333}
    td{padding:9px 14px;border-bottom:1px solid #f0f0f0;color:#444;vertical-align:top}
    tr:hover td{background:#f8f9ff}
    .badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
    .badge-blue{background:#e3f2fd;color:#1565c0}
    .badge-green{background:#e8f5e9;color:#2e7d32}
    .badge-orange{background:#fff3e0;color:#e65100}
    .stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:20px}
    .stat-card{background:linear-gradient(135deg,#e8eaf6,#f3e5f5);border-radius:10px;padding:16px;text-align:center}
    .stat-card .num{font-size:28px;font-weight:700;color:#1a237e}
    .stat-card .lbl{font-size:12px;color:#555;margin-top:4px}
    .drop-zone{border:2px dashed #c5cae9;border-radius:10px;padding:32px;text-align:center;cursor:pointer;transition:all .2s;color:#888}
    .drop-zone:hover,.drop-zone.drag-over{border-color:#1a237e;background:#e8eaf6;color:#1a237e}
    .drop-zone input{display:none}
    .progress{height:6px;background:#e0e0e0;border-radius:3px;margin-top:10px;overflow:hidden}
    .progress-bar{height:100%;background:linear-gradient(90deg,#1a237e,#283593);width:0;transition:width .3s;border-radius:3px}
    #msg{margin-top:12px}
  </style>
</head>
<body>

<!-- Login Screen -->
<div id="login-screen">
  <div class="login-box">
    <h2>🔐 Admin Login</h2>
    <p>NBKR Institute — Knowledge Management</p>
    <div class="form-group">
      <label>Username</label>
      <input type="text" id="uname" placeholder="admin / hod / principal" autocomplete="off"/>
    </div>
    <div class="form-group">
      <label>Password</label>
      <input type="password" id="pwd" placeholder="Enter password"/>
    </div>
    <div id="login-err" style="color:#c62828;font-size:13px;margin-bottom:10px;display:none"></div>
    <button class="btn btn-primary" style="width:100%" onclick="doLogin()">Login →</button>
    <p style="font-size:11px;color:#aaa;margin-top:14px;text-align:center">
      Default: admin / nbkr@admin2026
    </p>
  </div>
</div>

<!-- Main App -->
<div id="main-app" style="display:none">
  <div class="topbar">
    <h1>🎓 NBKR Admin — Knowledge Management Panel</h1>
    <div style="display:flex;align-items:center;gap:14px">
      <span id="user-label"></span>
      <button id="logout-btn" onclick="logout()">Logout</button>
    </div>
  </div>

  <div class="container">
    <div class="tabs">
      <div class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</div>
      <div class="tab" onclick="switchTab('upload')">📁 Upload File</div>
      <div class="tab" onclick="switchTab('text')">✏️ Add Text</div>
      <div class="tab" onclick="switchTab('manage')">📋 Manage Knowledge</div>
      <div class="tab" onclick="switchTab('audit')">🔍 Audit Log</div>
    </div>

    <!-- Dashboard -->
    <div id="tab-dashboard" class="panel active">
      <div class="section-title">📊 System Status</div>
      <div class="stat-grid" id="stat-grid">
        <div class="stat-card"><div class="num" id="s-vectors">—</div><div class="lbl">FAISS Vectors</div></div>
        <div class="stat-card"><div class="num" id="s-docs">—</div><div class="lbl">Knowledge Docs</div></div>
        <div class="stat-card"><div class="num" id="s-updates">—</div><div class="lbl">Admin Updates</div></div>
        <div class="stat-card"><div class="num" id="s-faculty">—</div><div class="lbl">Faculty Records</div></div>
        <div class="stat-card"><div class="num" id="s-circulars">—</div><div class="lbl">Circulars</div></div>
      </div>
      <div style="display:flex;gap:10px;margin-top:8px">
        <button class="btn btn-primary" onclick="loadStatus()">🔄 Refresh Status</button>
        <button class="btn btn-primary" onclick="reloadKB()" style="background:linear-gradient(135deg,#2e7d32,#388e3c)">⚡ Reload All Updates into FAISS</button>
      </div>
      <div id="dash-msg" style="margin-top:12px"></div>
    </div>

    <!-- Upload File -->
    <div id="tab-upload" class="panel">
      <div class="section-title">📁 Upload Document</div>
      <p style="font-size:13px;color:#666;margin-bottom:16px">
        Supported: <b>PDF, DOCX, TXT</b> — Text is auto-extracted, chunked, embedded and added to the live knowledge base instantly.
      </p>
      <div class="drop-zone" id="drop-zone" onclick="document.getElementById('file-input').click()">
        <input type="file" id="file-input" accept=".pdf,.docx,.doc,.txt" onchange="fileSelected(this)"/>
        <div style="font-size:32px;margin-bottom:8px">📂</div>
        <div style="font-weight:600">Click to select or drag & drop file here</div>
        <div style="font-size:12px;margin-top:4px" id="file-name">PDF, DOCX, TXT supported</div>
      </div>
      <div class="form-group" style="margin-top:16px">
        <label>Title / Description</label>
        <input type="text" id="up-title" placeholder="e.g. Fee Circular May 2026"/>
      </div>
      <div class="form-group">
        <label>Category</label>
        <select id="up-cat">
          <option value="circular">Circular / Notice</option>
          <option value="policy">Policy / Rules</option>
          <option value="academic">Academic Info</option>
          <option value="announcement">Announcement</option>
          <option value="general">General</option>
        </select>
      </div>
      <div class="progress"><div class="progress-bar" id="up-progress"></div></div>
      <button class="btn btn-primary" style="margin-top:14px" onclick="uploadFile()">⬆️ Upload & Process</button>
      <div id="up-msg"></div>
    </div>

    <!-- Add Text -->
    <div id="tab-text" class="panel">
      <div class="section-title">✏️ Add Text Knowledge</div>
      <p style="font-size:13px;color:#666;margin-bottom:16px">
        Type or paste any text — notice, policy, announcement, FAQ. It will be chunked, embedded and added to the live chatbot instantly.
      </p>
      <div class="form-group">
        <label>Title *</label>
        <input type="text" id="txt-title" placeholder="e.g. Exam Schedule June 2026"/>
      </div>
      <div class="form-group">
        <label>Category</label>
        <select id="txt-cat">
          <option value="circular">Circular / Notice</option>
          <option value="policy">Policy / Rules</option>
          <option value="academic">Academic Info</option>
          <option value="announcement">Announcement</option>
          <option value="general">General</option>
        </select>
      </div>
      <div class="form-group">
        <label>Content *</label>
        <textarea id="txt-content" placeholder="Paste or type the full text here..."></textarea>
      </div>
      <button class="btn btn-primary" onclick="addText()">➕ Add to Knowledge Base</button>
      <div id="txt-msg"></div>
    </div>

    <!-- Manage -->
    <div id="tab-manage" class="panel">
      <div class="section-title">📋 Manage Knowledge Entries</div>
      <button class="btn btn-primary btn-sm" onclick="loadUpdates()" style="margin-bottom:14px">🔄 Refresh</button>
      <div id="updates-table">Loading...</div>
    </div>

    <!-- Audit -->
    <div id="tab-audit" class="panel">
      <div class="section-title">🔍 Admin Audit Log</div>
      <button class="btn btn-primary btn-sm" onclick="loadAudit()" style="margin-bottom:14px">🔄 Refresh</button>
      <div id="audit-table">Loading...</div>
    </div>
  </div>
</div>

<script>
let TOKEN = localStorage.getItem('nbkr_admin_token') || '';
const BASE = '/admin';

// ── Auth ──────────────────────────────────────────────────────────────────────
async function doLogin() {
  const u = document.getElementById('uname').value.trim();
  const p = document.getElementById('pwd').value;
  const fd = new FormData();
  fd.append('username', u); fd.append('password', p);
  try {
    const r = await fetch(BASE + '/login', {method:'POST', body:fd});
    const d = await r.json();
    if (!r.ok) { document.getElementById('login-err').textContent = d.detail; document.getElementById('login-err').style.display='block'; return; }
    TOKEN = d.token;
    localStorage.setItem('nbkr_admin_token', TOKEN);
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('main-app').style.display = 'block';
    document.getElementById('user-label').textContent = '👤 ' + d.username;
    loadStatus();
  } catch(e) { document.getElementById('login-err').textContent = 'Connection error'; document.getElementById('login-err').style.display='block'; }
}

function logout() {
  localStorage.removeItem('nbkr_admin_token');
  TOKEN = '';
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('main-app').style.display = 'none';
}

// Auto-login if token exists
if (TOKEN) {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('main-app').style.display = 'block';
  loadStatus();
}

document.getElementById('pwd').addEventListener('keypress', e => { if(e.key==='Enter') doLogin(); });

function authHeaders() { return {'Authorization': 'Bearer ' + TOKEN}; }

// ── Tabs ──────────────────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  const tabs = ['dashboard','upload','text','manage','audit'];
  const idx = tabs.indexOf(name);
  document.querySelectorAll('.tab')[idx].classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'manage') loadUpdates();
  if (name === 'audit')  loadAudit();
}

// ── Status ────────────────────────────────────────────────────────────────────
async function loadStatus() {
  try {
    const r = await fetch(BASE + '/status', {headers: authHeaders()});
    if (r.status === 401) { logout(); return; }
    const d = await r.json();
    document.getElementById('s-vectors').textContent   = d.faiss_vectors;
    document.getElementById('s-docs').textContent      = d.knowledge_docs;
    document.getElementById('s-updates').textContent   = d.updates_on_disk;
    document.getElementById('s-faculty').textContent   = d.faculty;
    document.getElementById('s-circulars').textContent = d.circulars;
  } catch(e) {}
}

async function reloadKB() {
  const r = await fetch(BASE + '/reload', {method:'POST', headers: authHeaders()});
  const d = await r.json();
  showMsg('dash-msg', `✓ Reloaded ${d.entries} entries, ${d.vectors_added} vectors added`, 'success');
  loadStatus();
}

// ── Upload ────────────────────────────────────────────────────────────────────
let selectedFile = null;
function fileSelected(input) {
  selectedFile = input.files[0];
  document.getElementById('file-name').textContent = selectedFile ? selectedFile.name : 'No file selected';
}

const dz = document.getElementById('drop-zone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('drag-over');
  selectedFile = e.dataTransfer.files[0];
  document.getElementById('file-name').textContent = selectedFile.name;
});

async function uploadFile() {
  if (!selectedFile) { showMsg('up-msg','Please select a file first','error'); return; }
  const fd = new FormData();
  fd.append('file', selectedFile);
  fd.append('title', document.getElementById('up-title').value || selectedFile.name);
  fd.append('category', document.getElementById('up-cat').value);
  document.getElementById('up-progress').style.width = '40%';
  try {
    const r = await fetch(BASE + '/upload', {method:'POST', headers: authHeaders(), body: fd});
    document.getElementById('up-progress').style.width = '100%';
    const d = await r.json();
    if (!r.ok) { showMsg('up-msg', d.detail, 'error'); return; }
    showMsg('up-msg', `✓ ${d.message}<br>📊 Chunks: ${d.chunks} | Vectors added: ${d.vectors_added}<br>📝 Summary: ${d.summary}`, 'success');
    loadStatus();
    setTimeout(() => document.getElementById('up-progress').style.width = '0', 2000);
  } catch(e) { showMsg('up-msg','Upload failed: ' + e.message,'error'); }
}

// ── Add Text ──────────────────────────────────────────────────────────────────
async function addText() {
  const title   = document.getElementById('txt-title').value.trim();
  const content = document.getElementById('txt-content').value.trim();
  const cat     = document.getElementById('txt-cat').value;
  if (!title || !content) { showMsg('txt-msg','Title and content are required','error'); return; }
  const fd = new FormData();
  fd.append('title', title); fd.append('content', content); fd.append('category', cat);
  try {
    const r = await fetch(BASE + '/add-text', {method:'POST', headers: authHeaders(), body: fd});
    const d = await r.json();
    if (!r.ok) { showMsg('txt-msg', d.detail, 'error'); return; }
    showMsg('txt-msg', `✓ ${d.message}<br>📊 Chunks: ${d.chunks} | Vectors: ${d.vectors_added}<br>📝 Summary: ${d.summary}`, 'success');
    document.getElementById('txt-title').value = '';
    document.getElementById('txt-content').value = '';
    loadStatus();
  } catch(e) { showMsg('txt-msg','Error: ' + e.message,'error'); }
}

// ── Manage ────────────────────────────────────────────────────────────────────
async function loadUpdates() {
  const r = await fetch(BASE + '/updates', {headers: authHeaders()});
  const d = await r.json();
  if (!d.updates || d.updates.length === 0) {
    document.getElementById('updates-table').innerHTML = '<p style="color:#888;font-size:13px">No knowledge updates yet.</p>';
    return;
  }
  let html = `<table><thead><tr><th>#</th><th>Title</th><th>Category</th><th>Added By</th><th>Date</th><th>Chunks</th><th>Summary</th><th>Action</th></tr></thead><tbody>`;
  d.updates.forEach((u, i) => {
    const cat_badge = `<span class="badge badge-blue">${u.category}</span>`;
    html += `<tr>
      <td>${i+1}</td>
      <td><b>${u.title}</b></td>
      <td>${cat_badge}</td>
      <td>${u.added_by}</td>
      <td style="white-space:nowrap;font-size:11px">${u.added_at ? u.added_at.slice(0,16).replace('T',' ') : '—'}</td>
      <td style="text-align:center">${u.chunks}</td>
      <td style="font-size:11px;color:#666;max-width:200px">${u.summary}</td>
      <td><button class="btn btn-danger btn-sm" onclick="deleteEntry('${u.id}')">🗑 Delete</button></td>
    </tr>`;
  });
  html += '</tbody></table>';
  document.getElementById('updates-table').innerHTML = html;
}

async function deleteEntry(uid) {
  if (!confirm('Delete this knowledge entry?')) return;
  const r = await fetch(BASE + '/updates/' + uid, {method:'DELETE', headers: authHeaders()});
  const d = await r.json();
  showMsg('dash-msg', `✓ Deleted. ${d.note}`, 'info');
  loadUpdates(); loadStatus();
}

// ── Audit ─────────────────────────────────────────────────────────────────────
async function loadAudit() {
  const r = await fetch(BASE + '/audit', {headers: authHeaders()});
  const d = await r.json();
  if (!d.logs || d.logs.length === 0) {
    document.getElementById('audit-table').innerHTML = '<p style="color:#888;font-size:13px">No audit logs yet.</p>';
    return;
  }
  let html = `<table><thead><tr><th>Time</th><th>User</th><th>Action</th><th>Detail</th></tr></thead><tbody>`;
  d.logs.forEach(l => {
    const action_color = l.action === 'LOGIN' ? 'badge-green' : l.action === 'DELETE' ? 'badge-orange' : 'badge-blue';
    html += `<tr>
      <td style="white-space:nowrap;font-size:11px">${l.ts ? l.ts.slice(0,16).replace('T',' ') : '—'}</td>
      <td><b>${l.user}</b></td>
      <td><span class="badge ${action_color}">${l.action}</span></td>
      <td style="font-size:12px;color:#555">${l.detail}</td>
    </tr>`;
  });
  html += '</tbody></table>';
  document.getElementById('audit-table').innerHTML = html;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function showMsg(id, msg, type) {
  const el = document.getElementById(id);
  el.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
  setTimeout(() => el.innerHTML = '', 8000);
}
</script>
</body>
</html>"""
