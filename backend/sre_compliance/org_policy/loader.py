from sre_compliance.graph.neo4j_client import Neo4jClient

# ============================================================
# ROLE DEFINITION
# ============================================================

def define_role(role: str):
    query = """
    MERGE (r:Role {name: $role})
    """
    Neo4jClient.run(query, {"role": role})


# ============================================================
# ROLE → ACTION PERMISSIONS
# ============================================================

def allow_action_for_role(role: str, action: str):
    query = """
    MATCH (r:Role {name: $role})
    MERGE (a:Action {name: $action})
    MERGE (r)-[:CAN_EXECUTE]->(a)
    """
    Neo4jClient.run(query, {
        "role": role,
        "action": action
    })


def forbid_action_for_role(role: str, action: str):
    query = """
    MATCH (r:Role {name: $role})
    MERGE (a:Action {name: $action})
    MERGE (r)-[:FORBIDDEN]->(a)
    """
    Neo4jClient.run(query, {
        "role": role,
        "action": action
    })


# ============================================================
# APPROVAL RULES
# ============================================================

def require_approval_for_action(action: str):
    query = """
    MERGE (a:Action {name: $action})
    SET a.org_requires_approval = true
    """
    Neo4jClient.run(query, {"action": action})


# ============================================================
# ORG BLAST RADIUS LIMIT
# ============================================================

def set_org_blast_limit(action: str, max_scope: str):
    """
    max_scope ∈ SINGLE_RESOURCE | MULTI_RESOURCE | GLOBAL
    """
    query = """
    MERGE (a:Action {name: $action})
    SET a.max_org_scope = $scope
    """
    Neo4jClient.run(query, {
        "action": action,
        "scope": max_scope
    })
