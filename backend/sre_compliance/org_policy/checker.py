from sre_compliance.graph.neo4j_client import Neo4jClient

# ============================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================

def check_role_permissions(intent: dict):
    role = intent.get("role")
    action = intent.get("action")

    if not role or not action:
        return {"decision": "ALLOW"}

    query = """
    MATCH (r:Role {name: $role})
    MATCH (a:Action {name: $action})
    WHERE (r)-[:FORBIDDEN]->(a)
    RETURN a.name
    """
    forbidden = Neo4jClient.run(query, {
        "role": role,
        "action": action
    })

    if forbidden:
        return {
            "decision": "DENY",
            "layer": "ORG_ROLE_POLICY",
            "reason": f"Role '{role}' is forbidden from executing '{action}'"
        }

    allowed = Neo4jClient.run("""
        MATCH (r:Role {name: $role})-[:CAN_EXECUTE]->(a:Action {name: $action})
        RETURN a
    """, {"role": role, "action": action})

    if not allowed:
        return {
            "decision": "DENY",
            "layer": "ORG_ROLE_POLICY",
            "reason": f"Role '{role}' is not permitted to execute '{action}'"
        }

    return {"decision": "ALLOW"}


# ============================================================
# ORG APPROVAL RULES
# ============================================================

def check_org_approval(intent: dict):
    action = intent.get("action")

    query = """
    MATCH (a:Action {name: $action})
    WHERE a.org_requires_approval = true
    RETURN a.name
    """
    result = Neo4jClient.run(query, {"action": action})

    if result:
        return {
            "decision": "REQUIRE_APPROVAL",
            "layer": "ORG_APPROVAL_POLICY",
            "reason": "Organization requires approval for this action"
        }

    return {"decision": "ALLOW"}


# ============================================================
# ORG BLAST RADIUS LIMIT
# ============================================================

def check_org_blast_radius(intent: dict):
    action = intent.get("action")
    scope = intent.get("scope", "SINGLE_RESOURCE")

    query = """
    MATCH (a:Action {name: $action})
    WHERE a.max_org_scope IS NOT NULL
      AND a.max_org_scope <> $scope
    RETURN a.max_org_scope
    """
    result = Neo4jClient.run(query, {
        "action": action,
        "scope": scope
    })

    if result:
        return {
            "decision": "REQUIRE_APPROVAL",
            "layer": "ORG_BLAST_RADIUS",
            "reason": "Requested scope exceeds organizational limit"
        }

    return {"decision": "ALLOW"}
