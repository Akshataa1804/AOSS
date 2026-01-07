from sre_compliance.graph.neo4j_client import Neo4jClient
from datetime import datetime

# ============================================================
# ENVIRONMENT SETUP
# ============================================================

def load_service_environment(service: str, environment: str):
    query = """
    MERGE (s:Service {name: $service})
    MERGE (e:Environment {name: $env})
    MERGE (s)-[:DEPLOYED_IN]->(e)
    """
    Neo4jClient.run(query, {
        "service": service,
        "env": environment
    })


# ============================================================
# ACTION RISK MODEL
# ============================================================

def load_action_risk(
    action: str,
    risk_level: str,
    needs_approval: bool
):
    query = """
    MERGE (a:Action {name: $action})
    SET a.risk_level = $risk,
        a.needs_approval = $approval
    """
    Neo4jClient.run(query, {
        "action": action,
        "risk": risk_level,
        "approval": needs_approval
    })


# ============================================================
# INCIDENT STATE
# ============================================================

def declare_incident(
    incident_id: str,
    service: str,
    severity: str,
    active: bool = True
):
    query = """
    MERGE (i:Incident {id: $id})
    SET i.severity = $severity,
        i.active = $active,
        i.started_at = datetime($started_at)
    MERGE (s:Service {name: $service})
    MERGE (i)-[:AFFECTS]->(s)
    """
    Neo4jClient.run(query, {
        "id": incident_id,
        "service": service,
        "severity": severity,
        "active": active,
        "started_at": datetime.utcnow().isoformat()
    })


# ============================================================
# CHANGE FREEZE WINDOWS
# ============================================================

def declare_freeze_window(
    window_id: str,
    environment: str,
    start_iso: str,
    end_iso: str,
    reason: str
):
    query = """
    MERGE (f:FreezeWindow {id: $id})
    SET f.start = datetime($start),
        f.end = datetime($end),
        f.reason = $reason
    MERGE (e:Environment {name: $env})
    MERGE (f)-[:APPLIES_TO]->(e)
    """
    Neo4jClient.run(query, {
        "id": window_id,
        "env": environment,
        "start": start_iso,
        "end": end_iso,
        "reason": reason
    })


# ============================================================
# BLAST RADIUS MODEL
# ============================================================

def load_action_scope(action: str, scope: str):
    """
    scope ∈ SINGLE_RESOURCE | MULTI_RESOURCE | GLOBAL
    """
    query = """
    MERGE (a:Action {name: $action})
    MERGE (s:TargetScope {name: $scope})
    MERGE (a)-[:AFFECTS_SCOPE]->(s)
    """
    Neo4jClient.run(query, {
        "action": action,
        "scope": scope
    })
