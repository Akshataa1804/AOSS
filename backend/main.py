import os
import shutil
from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import yaml

from compliance_utils import extract_rules_from_pdf, get_rules, add_rule, delete_rule

# ----------------------------
# Setup paths
# ----------------------------
UPLOAD_DIR = "uploaded_docs"
RULES_DIR = "rules"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RULES_DIR, exist_ok=True)

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(title="AOSS Compliance Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Models
# ----------------------------
class RAGRequest(BaseModel):
    query: str

class RAGResponse(BaseModel):
    query: str
    plan: str
    status: str
    compliance: Dict[str, Any]

# ----------------------------
# Helpers
# ----------------------------
def rules_file_for_doc(filename: str) -> str:
    base = os.path.splitext(filename)[0]
    return os.path.join(RULES_DIR, f"{base}.yml")

# ----------------------------
# Document endpoints
# ----------------------------
@app.post("/upload")
async def upload_pdf(file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "uploaded", "filename": file.filename}

@app.get("/documents")
def list_docs():
    return {"documents": os.listdir(UPLOAD_DIR)}

@app.delete("/documents/{filename}")
def delete_doc(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    rule_file = rules_file_for_doc(filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        if os.path.exists(rule_file):
            os.remove(rule_file)
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="File not found")

# ----------------------------
# Rules extraction endpoint
# ----------------------------
@app.post("/fetch_rules/{filename}")
def fetch_rules_endpoint(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    rules = extract_rules_from_pdf(file_path)
    rule_file = rules_file_for_doc(filename)
    with open(rule_file, "w") as f:
        yaml.dump(rules, f)
    return {"status": "rules_extracted", "rules": rules}

# ----------------------------
# Rules CRUD
# ----------------------------
@app.get("/rules")
def get_all_rules():
    all_rules = {}
    for f in os.listdir(RULES_DIR):
        if f.endswith(".yml"):
            path = os.path.join(RULES_DIR, f)
            all_rules[f] = get_rules(path)
    return {"rules": all_rules}

@app.post("/rules")
def add_rule_endpoint(
    filename: str = Query(...),
    rule_type: str = Query(...),
    rule_value: str = Query(...)
):
    if rule_type not in ["allowed", "forbidden", "required"]:
        raise HTTPException(status_code=400, detail="Invalid rule type")
    file_path = rules_file_for_doc(filename)
    add_rule(file_path, rule_type, rule_value)
    return {"status": "added", "filename": filename, "rule_type": rule_type, "rule_value": rule_value}

@app.delete("/rules")
def delete_rule_endpoint(
    filename: str = Query(...),
    rule_type: str = Query(...),
    rule_value: str = Query(...)
):
    if rule_type not in ["allowed", "forbidden", "required"]:
        raise HTTPException(status_code=400, detail="Invalid rule type")
    file_path = rules_file_for_doc(filename)
    delete_rule(file_path, rule_type, rule_value)
    return {"status": "deleted", "filename": filename, "rule_type": rule_type, "rule_value": rule_value}

# ----------------------------
# Placeholder RAG endpoints
# ----------------------------
@app.post("/rag", response_model=RAGResponse)
async def rag_endpoint(request: RAGRequest):
    # For now return dummy response
    return {
        "query": request.query,
        "plan": "RAG executed",
        "status": "success",
        "compliance": {"allowed": [], "forbidden": [], "required": []}
    }
