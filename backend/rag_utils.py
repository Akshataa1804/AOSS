# backend/rag_utils.py
import os
import yaml
import json
import ollama

RULES_DIR = "rules"

# ----------------------------
# Load rules from YAML backend
# ----------------------------
def load_rules():
    """Load all rules from rules/ directory into a single dict"""
    rules = {"allowed": [], "forbidden": [], "required": []}
    if not os.path.exists(RULES_DIR):
        return rules

    for file in os.listdir(RULES_DIR):
        if file.endswith((".yml", ".yaml")):
            with open(os.path.join(RULES_DIR, file), "r") as f:
                data = yaml.safe_load(f) or {}
                for key in ["allowed", "forbidden", "required"]:
                    # store normalized strings; keep original item if dict
                    items = data.get(key, [])
                    for itm in items:
                        if isinstance(itm, dict):
                            # keep dicts as-is in required (they are conditions)
                            rules[key].append(itm)
                        else:
                            rules[key].append(str(itm).lower().strip())
    # Deduplicate simple string lists, keep dicts unique by string repr
    for key in ["allowed", "forbidden"]:
        rules[key] = list(dict.fromkeys(rules[key]))  # preserves order, dedups
    # required may contain dicts + strings; transform into list preserving items
    seen = set()
    normalized_required = []
    for itm in rules["required"]:
        keystr = json.dumps(itm, sort_keys=True) if isinstance(itm, dict) else str(itm)
        if keystr not in seen:
            seen.add(keystr)
            normalized_required.append(itm)
    rules["required"] = normalized_required
    return rules


# ----------------------------
# Compliance Check
# ----------------------------
def check_violations(commands, rules):
    """
    Check commands against forbidden, allowed, required rules.
    Returns:
      - violations: list of {command, rule} dicts
      - safe_plan: only commands that do NOT violate any rule
    """
    violations = []
    safe_plan = []

    for cmd in commands:
        cmd_lower = cmd.lower().strip()
        violated = False

        # Forbidden: any forbidden substring in command -> violation
        for f in rules.get("forbidden", []):
            if isinstance(f, str) and f and f in cmd_lower:
                violations.append({"command": cmd, "rule": f})
                violated = True
                break

        if violated:
            continue

        # Required: if rules.required contains dicts, check for keys; if strings, ensure presence
        if rules.get("required"):
            for req in rules["required"]:
                if isinstance(req, dict):
                    # dict like {"Networkrestart": "admin approval required"}
                    req_key = list(req.keys())[0].lower()
                    if req_key not in cmd_lower:
                        violations.append({"command": cmd, "rule": f"missing required: {req_key}"})
                        violated = True
                        break
                else:
                    if str(req).lower().strip() not in cmd_lower:
                        violations.append({"command": cmd, "rule": f"missing required: {req}"})
                        violated = True
                        break

        if violated:
            continue

        # Allowed: if allowed list is non-empty, command must match at least one allowed substring
        allowed_list = rules.get("allowed", [])
        if allowed_list:
            matched_allowed = False
            for a in allowed_list:
                if isinstance(a, str) and a and a in cmd_lower:
                    matched_allowed = True
                    break
            if not matched_allowed:
                violations.append({"command": cmd, "rule": "not allowed"})
                violated = True

        if not violated:
            safe_plan.append(cmd)

    return violations, safe_plan


# ----------------------------
# RAG + Compliance
# ----------------------------
def run_rag_query(query: str):
    """
    Convert natural language query -> shell commands -> compliance check
    Only return commands that pass compliance in safe_plan.
    """
    prompt = f"""
Convert the natural language query into shell commands.
Respond ONLY in JSON with this exact format:
{{ "Commands": ["cmd1", "cmd2"] }}

Query: {query}
"""

    rules = load_rules()

    try:
        response = ollama.generate(model="llama3", prompt=prompt)
        raw = response.get("response", "").strip()
    except Exception as e:
        print(f"\n\nOllama error:\n{str(e)}")
        raw = ""
        # return error wrapper
        return {
            "query": query,
            "planner_raw": "",
            "safe_plan": [],
            "violations": [{"command": "", "rule": f"LLM call failed: {str(e)}"}],
            "status": "error"
        }

    # Parse JSON safely
    commands = []
    if raw:
        try:
            parsed = json.loads(raw)
            commands = parsed.get("Commands", []) if isinstance(parsed, dict) else []
        except Exception:
            # attempt to extract JSON substring or eval fallback
            try:
                # find first { and last } and parse
                first = raw.find('{')
                last = raw.rfind('}')
                if first != -1 and last != -1:
                    snippet = raw[first:last+1]
                    parsed = json.loads(snippet)
                    commands = parsed.get("Commands", []) if isinstance(parsed, dict) else []
                else:
                    # last resort
                    parsed = eval(raw) if raw else {}
                    commands = parsed.get("Commands", []) if isinstance(parsed, dict) else []
            except Exception:
                commands = []

    # Normalize commands to list of strings
    commands = [str(c) for c in commands if c]

    violations, safe_plan = check_violations(commands, rules)

    return {
        "query": query,
        "planner_raw": raw,
        "safe_plan": safe_plan,
        "violations": violations,
        "status": "success" if safe_plan else ("violations" if violations else "no_plan"),
    }
