import os
import subprocess
import yaml
from PyPDF2 import PdfReader
import re

UPLOADED_DIR = "uploaded_docs"
RULES_DIR = "rules"

os.makedirs(UPLOADED_DIR, exist_ok=True)
os.makedirs(RULES_DIR, exist_ok=True)

# Call LLM
def call_llm(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", "llama3"],
        input=prompt,
        text=True,
        capture_output=True
    )
    return result.stdout

# Extract rules and save raw + parsed YAML
def extract_rules_from_pdf(file_path: str) -> dict:
    reader = PdfReader(file_path)
    text = "".join(page.extract_text() or "" for page in reader.pages)

    prompt = f"""
Extract only YAML of compliance commands from this text.
Keys: allowed, forbidden, required.
One command per line. No explanations.

Text:
{text}
"""

    raw_output = call_llm(prompt)

    # Save raw output first
    rules_file = os.path.join(RULES_DIR, f"{os.path.splitext(os.path.basename(file_path))[0]}.yml")
    with open(rules_file, "w", encoding="utf-8") as f:
        f.write(raw_output)

    # Try to parse YAML safely to return structured data
    try:
        # Extract the first YAML block (if any extra text)
        match = re.search(r"(?s)(allowed:.*required:.*)", raw_output)
        yaml_text = match.group(1) if match else "allowed: []\nforbidden: []\nrequired: []"
        parsed = yaml.safe_load(yaml_text)
        for key in ["allowed", "forbidden", "required"]:
            parsed[key] = parsed.get(key, [])
    except Exception as e:
        parsed = {"allowed": [], "forbidden": [], "required": []}
    
    return {"raw_output": raw_output, "parsed": parsed}

# Get, add, delete rules (unchanged)
def get_all_rules(rules_file: str) -> dict:
    try:
        with open(rules_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        data = {}
    return data

def add_rule_to_file(rules_file: str, rule_type: str, rule_value: str):
    data = get_all_rules(rules_file)
    if rule_type not in data:
        data[rule_type] = []
    if rule_value.strip() and rule_value not in data[rule_type]:
        data[rule_type].append(rule_value.strip())
    with open(rules_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def delete_rule_from_file(rules_file: str, rule_type: str, rule_value: str):
    data = get_all_rules(rules_file)
    if rule_type in data and rule_value.strip() in data[rule_type]:
        data[rule_type].remove(rule_value.strip())
    with open(rules_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
