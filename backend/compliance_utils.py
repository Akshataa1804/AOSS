import subprocess
import yaml
from PyPDF2 import PdfReader
from pathlib import Path

# ----------------------------
# LLM-based Rule Extraction
# ----------------------------
def call_llm(prompt: str) -> str:
    """Call Ollama model and return raw response."""
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print("⚠️ LLM call failed:", e)
        return ""

def extract_rules_from_pdf(file_path: str) -> dict:
    """
    Extract compliance rules from natural language PDF using LLM.
    Returns dict with allowed, forbidden, required keys.
    """
    # 1. Read PDF text
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    if not text.strip():
        return {"allowed": [], "forbidden": [], "required": []}

    # 2. Prepare prompt
    prompt = f"""
    Extract compliance rules from the following text into YAML with keys: allowed, forbidden, required.
    Output ONLY valid YAML, no explanations.

    Text:
    {text}

    Example format:
    allowed:
      - ls
      - pwd
    forbidden:
      - rm
      - shutdown
    required:
      - check_user
    """

    # 3. Call LLM
    response = call_llm(prompt)

    # 4. Clean output
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("` \n")
        if cleaned.lower().startswith("yaml"):
            cleaned = cleaned[4:].strip()

    # 5. Parse YAML safely
    rules = {"allowed": [], "forbidden": [], "required": []}
    try:
        parsed = yaml.safe_load(cleaned)
        if isinstance(parsed, dict):
            for k in ["allowed", "forbidden", "required"]:
                rules[k] = list({str(cmd).strip() for cmd in parsed.get(k, []) if cmd})
    except yaml.YAMLError:
        print("⚠️ Failed to parse LLM output:", response)

    return rules

# ----------------------------
# Rule File Management
# ----------------------------
def ensure_rules_file(rules_file: str):
    """Create empty YAML if it doesn't exist."""
    if not Path(rules_file).exists():
        with open(rules_file, "w") as f:
            yaml.dump({"allowed": [], "forbidden": [], "required": []}, f)

def get_rules(rules_file: str) -> dict:
    ensure_rules_file(rules_file)
    with open(rules_file, "r") as f:
        data = yaml.safe_load(f) or {"allowed": [], "forbidden": [], "required": []}
    # Deduplicate & strip
    for k in data:
        data[k] = list({str(i).strip() for i in data[k] if i})
    return data

def add_rule(rules_file: str, rule_type: str, rule_value: str):
    rules = get_rules(rules_file)
    if rule_value.strip() and rule_value not in rules[rule_type]:
        rules[rule_type].append(rule_value.strip())
        with open(rules_file, "w") as f:
            yaml.dump(rules, f)

def delete_rule(rules_file: str, rule_type: str, rule_value: str):
    rules = get_rules(rules_file)
    if rule_value.strip() in rules[rule_type]:
        rules[rule_type].remove(rule_value.strip())
        with open(rules_file, "w") as f:
            yaml.dump(rules, f)
