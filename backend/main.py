# backend/main.py
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Dict
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Chroma vector DB
from chromadb import PersistentClient

# ---------------- Config ----------------
UPLOAD_DIR = "uploads"
CHROMA_DIR = "chroma_store"
CHROMA_COLLECTION = "documents"
MAX_FILE_SIZE_MB = 200

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(title="Compliance Document Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

chroma_client = PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)

progress_store: Dict[str, str] = {}
upload_meta: Dict[str, dict] = {}

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

# ---------------- Routes ----------------

@app.get("/")
def root():
    return {"message": "API running", "endpoints": ["/upload", "/documents", "/documents/{doc_id}", "/status/{upload_id}", "/test-rag", "/rules/{doc_id}", "/rag", "/reset_index"]}

@app.post("/upload")
async def upload(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    upload_id = str(uuid.uuid4())
    progress_store[upload_id] = "Queued"
    saved_paths = []
    meta_list = []

    for f in files:
        f.file.seek(0, os.SEEK_END)
        size = f.file.tell()
        f.file.seek(0)
        if size > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"{f.filename} exceeds max size")
        dest = os.path.join(UPLOAD_DIR, f.filename)
        i = 1
        while os.path.exists(dest):
            name, ext = os.path.splitext(f.filename)
            dest = os.path.join(UPLOAD_DIR, f"{name}_{i}{ext}")
            i += 1
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        saved_paths.append(dest)
        meta_list.append({
            "filename": os.path.basename(dest),
            "size": size,
            "type": os.path.splitext(dest)[1].lower().lstrip("."),
            "uploaded_at": datetime.utcnow().isoformat() + "Z"
        })

    upload_meta[upload_id] = {"files": meta_list, "created_at": datetime.utcnow().isoformat() + "Z"}
    progress_store[upload_id] = "Uploaded"

    return {"upload_id": upload_id, "files": meta_list}

@app.get("/status/{upload_id}")
def status(upload_id: str):
    return {"upload_id": upload_id, "status": progress_store.get(upload_id, "unknown"), "meta": upload_meta.get(upload_id)}

@app.get("/documents")
def list_documents():
    files = []
    for fname in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, fname)
        stat = os.stat(path)
        files.append({
            "id": fname,
            "filename": fname,
            "size": stat.st_size,
            "type": os.path.splitext(fname)[1].lower().lstrip("."),
            "uploaded_at": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z"
        })
    return {"documents": files}

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    path = os.path.join(UPLOAD_DIR, doc_id)
    if os.path.exists(path):
        os.remove(path)
    try:
        collection.delete(where={"source": doc_id})
    except Exception:
        pass
    return {"deleted": doc_id}

@app.post("/test-rag")
def test_rag(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    try:
        res = collection.query(query_texts=[req.query], n_results=req.top_k, include=["metadatas","documents"])
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return {"query": req.query, "results": [{"document": d, "metadata": m} for d, m in zip(docs, metas)]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chroma query failed: {e}")

# -------- Updated Rule Extraction --------
@app.get("/rules/{doc_id}")
def extract_rules(doc_id: str):
    path = os.path.join(UPLOAD_DIR, doc_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Document not found")

    ext = os.path.splitext(path)[1].lower()
    text = ""

    try:
        if ext == ".pdf":
            import fitz  # PyMuPDF
            with fitz.open(path) as doc:
                for page in doc:
                    text += page.get_text("text")
        elif ext == ".docx":
            import docx
            doc = docx.Document(path)
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif ext in [".txt", ".md"]:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read document: {e}")

    # --- Simple rule extraction ---
    rules = []
    for idx, line in enumerate(text.split("\n")):
        if any(word in line.lower() for word in ["must", "should", "required"]):
            rules.append({
                "section": f"Line {idx+1}",
                "clause": f"C{idx+1}",
                "requirement": line.strip()
            })

    return {"doc_id": doc_id, "rules": rules}

@app.post("/reset_index")
def reset_index():
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    global chroma_client, collection
    chroma_client = PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)
    return {"message": "Index reset"}
