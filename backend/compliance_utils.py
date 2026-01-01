import subprocess
import json
import re
from PyPDF2 import PdfReader
from pathlib import Path


# ------------------------------------------------------------
# LLM CALL (WINDOWS-SAFE)
# ------------------------------------------------------------
def call_llm(prompt: str) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3", prompt],
            capture_output=True,
            text=True,
            errors="ignore"  # avoids cp1252 crash
        )
        return result.stdout.strip()
    except Exception as e:
        print("⚠ LLM call failed:", e)
        return ""


# ------------------------------------------------------------
# PDF → ACTION EXTRACTION (ROBUST)
# ------------------------------------------------------------
def extract_threats_from_pdf(file_path: str) -> dict:
    # ---- Read PDF ----
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    if not text.strip():
        return {"actions": []}

    # ---- Prompt ----
    prompt = f"""
Convert the following compliance policy into operational actions.

Return the result as JSON.
The JSON may be either:
- a list of action objects
- or an object with key "actions"

Each action object must have:
command, intent, service, affected_system,
risk_level (low|medium|high|critical),
needs_approval (true|false),
dependencies (list), policy_ref

POLICY TEXT:
{text}
"""

    raw = call_llm(prompt)

    if not raw:
        print("⚠ Empty LLM output")
        return {"actions": []}

    # ---- Extract FIRST JSON object or array from text ----
    json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", raw)
    if not json_match:
        print("⚠ Could not find JSON in output:\n", raw)
        return {"actions": []}

    json_text = json_match.group(1)

    # ---- Parse JSON ----
    try:
        parsed = json.loads(json_text)
    except Exception as e:
        print("⚠ JSON parse error:", e)
        print("⚠ Extracted text:\n", json_text)
        return {"actions": []}

    # ---- Normalize ----
    if isinstance(parsed, list):
        actions = parsed
    elif isinstance(parsed, dict) and "actions" in parsed:
        actions = parsed["actions"]
    else:
        print("⚠ Unexpected JSON structure:", parsed)
        return {"actions": []}

    normalized = []
    for item in actions:
        normalized.append({
            "command": str(item.get("command", "")).strip(),
            "intent": str(item.get("intent", "")).strip(),
            "service": str(item.get("service", "")).strip(),
            "affected_system": str(item.get("affected_system", "")).strip(),
            "risk_level": str(item.get("risk_level", "")).lower().strip(),
            "needs_approval": bool(item.get("needs_approval", False)),
            "dependencies": item.get("dependencies", []) if isinstance(item.get("dependencies", []), list) else [],
            "policy_ref": str(item.get("policy_ref", "")).strip()
        })

    return {"actions": normalized}


# ------------------------------------------------------------
# JSON PERSISTENCE (OPTIONAL)
# ------------------------------------------------------------
def save_threat_json(file_path: str, data: dict):
    rules_dir = Path("rules")
    rules_dir.mkdir(exist_ok=True)
    out_path = rules_dir / f"{Path(file_path).stem}.json"
    out_path.write_text(json.dumps(data, indent=2))
    return out_path.as_posix()


def load_threat_json(filename: str) -> dict:
    path = Path("rules") / f"{Path(filename).stem}.json"
    if not path.exists():
        return {"actions": []}
    return json.loads(path.read_text())
