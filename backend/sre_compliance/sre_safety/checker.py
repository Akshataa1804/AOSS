from sre_compliance.graph.neo4j_client import Neo4jClient

# ============================================================
# 1. DESTRUCTIVE COMMAND GUARD
# ============================================================

DESTRUCTIVE_ACTIONS = {
    "DELETE_OS",
    "WIPE_DISK",
    "DROP_DATABASE",
    "RM_RF",
    "FORMAT_DISK"
}

def check_destructive_action(intent: dict):
    action = intent.get("action")

    if action in DESTRUCTIVE_ACTIONS:
        return {
            "decision": "DENY",
            "layer": "SRE_DESTRUCTIVE_GUARD",
            "reason": f"Destructive action '{action}' is permanently blocked"
        }

    return {"decision": "ALLOW"}


# ============================================================
# 2. ENVIRONMENT PROTECTION (PROD)
# ============================================================

def check_prod_environment(intent: dict):
    service = intent.get("service")
    action = intent.get("action")

    if not service:
        return {"decision": "ALLOW"}

    query = """
    MATCH (s:Service {name: $service})-[:DEPLOYED_IN]->(e:Environment)
    MATCH (a:Action {name: $action})
    WHERE e.name = "prod" AND a.risk_level = "HIGH"
    RETURN a.name
    """
    result = Neo4jClient.run(query, {
        "service": service,
        "action": action
    })

    if result:
        return {
            "decision": "REQUIRE_APPROVAL",
            "layer": "SRE_PROD_PROTECTION",
            "reason": "High-risk action on production requires approval"
        }

    return {"decision": "ALLOW"}


# ============================================================
# 3. INCIDENT FREEZE
# ============================================================

def check_incident_freeze(intent: dict):
    service = intent.get("service")
    action = intent.get("action")

    if not service:
        return {"decision": "ALLOW"}

    query = """
    MATCH (i:Incident {active: true})-[:AFFECTS]->(s:Service {name: $service})
    MATCH (a:Action {name: $action})
    WHERE a.risk_level IN ["MEDIUM", "HIGH"]
    RETURN i.id
    """
    result = Neo4jClient.run(query, {
        "service": service,
        "action": action
    })

    if result:
        return {
            "decision": "DENY",
            "layer": "SRE_INCIDENT_FREEZE",
            "reason": "Action blocked due to active incident"
        }

    return {"decision": "ALLOW"}
