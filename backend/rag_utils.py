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
                    rules[key].extend([str(cmd).lower().strip() for cmd in data.get(key, [])])
    # Deduplicate
    for key in rules:
        rules[key] = list(set(rules[key]))
    return rules

# ----------------------------
# Compliance Check
# ----------------------------
def check_violations(commands, rules):
    """
    Check commands against forbidden, allowed, required rules.
    Return violations and safe_plan separately.
    """
    violations = []
    safe_plan = []

    for cmd in commands:
        cmd_lower = cmd.lower().strip()
        violated = False

        # Forbidden
        for f in rules.get("forbidden", []):
            if f in cmd_lower:
                violations.append({"command": cmd, "rule": f})
                violated = True
                break

        # Required
        if not violated and rules.get("required"):
            if not any(req in cmd_lower for req in rules["required"]):
                violations.append({"command": cmd, "rule": "missing required"})
                violated = True

        # Allowed
        if not violated and rules.get("allowed"):
            if not any(a in cmd_lower for a in rules["allowed"]):
                violations.append({"command": cmd, "rule": "not allowed"})
                violated = True

        if not violated:
            safe_plan.append(cmd)

    return violations, safe_plan

# ----------------------------
# RAG + Compliance
# ----------------------------
def run_rag_query(query: str, rules: dict):
    """
    Generate commands from natural language query using LLM.
    Then check compliance against rules from backend.
    """
    prompt = f"""
    You are an execution agent.
    Convert the natural language query into shell commands.
    Respond ONLY in JSON with this exact format:
    {{
      "Commands": ["cmd1", "cmd2"]
    }}

    Query: {query}
    """

    response = ollama.generate(model="llama3", prompt=prompt)
    raw = response.get("response", "").strip()

    # Parse JSON safely
    try:
        parsed = json.loads(raw)
        commands = parsed.get("Commands", [])
    except Exception:
        try:
            commands = eval(raw).get("Commands", [])
        except Exception:
            commands = []

    # Compliance check
    violations, safe_plan = check_violations(commands, rules)

    return {
        "query": query,
        "planner_raw": raw,
        "plan": commands,
        "safe_plan": safe_plan,
        "violations": violations,
        "rules": rules,
        "error": None
    }
