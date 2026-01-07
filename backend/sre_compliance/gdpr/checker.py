from sre_compliance.graph.neo4j_client import Neo4jClient

# ============================================================
# GDPR 1. DATA RETENTION
# ============================================================

def check_gdpr_retention(intent: dict):
    if intent.get("action") != "DELETE_LOGS":
        return {"decision": "ALLOW"}

    service = intent.get("service")
    requested_days = intent.get("params", {}).get("older_than_days")

    if requested_days is None:
        return {"decision": "ALLOW"}

    query = """
    MATCH (s:Service {name: $service})
          -[:PROCESSES]->(d:PersonalData)
          -[:RETAINED_UNDER]->(r:RetentionPolicy)
    WHERE r.days > $requested
    RETURN r.days
    """
    result = Neo4jClient.run(query, {
        "service": service,
        "requested": requested_days
    })

    if result:
        return {
            "decision": "DENY",
            "layer": "GDPR_RETENTION",
            "reason": f"Minimum retention is {result[0]['r.days']} days"
        }

    return {"decision": "ALLOW"}


# ============================================================
# GDPR 2. PURPOSE LIMITATION
# ============================================================

def check_purpose_limitation(intent: dict):
    declared_purpose = intent.get("purpose")
    activity = intent.get("activity")

    if not declared_purpose or not activity:
        return {"decision": "ALLOW"}

    query = """
    MATCH (pa:ProcessingActivity {name: $activity})
    WHERE pa.purpose <> $purpose
    RETURN pa.purpose
    """
    result = Neo4jClient.run(query, {
        "activity": activity,
        "purpose": declared_purpose
    })

    if result:
        return {
            "decision": "DENY",
            "layer": "GDPR_PURPOSE_LIMITATION",
            "reason": "Processing purpose mismatch"
        }

    return {"decision": "ALLOW"}


# ============================================================
# GDPR 3. LAWFUL BASIS (HARD FAIL)
# ============================================================

def check_legal_basis(intent: dict):
    activity = intent.get("activity")
    if not activity:
        return {"decision": "ALLOW"}

    query = """
    MATCH (pa:ProcessingActivity {name: $activity})
    WHERE NOT (pa)-[:HAS_LEGAL_BASIS]->(:LegalBasis)
    RETURN pa
    """
    result = Neo4jClient.run(query, {"activity": activity})

    if result:
        return {
            "decision": "DENY",
            "layer": "GDPR_LAWFUL_BASIS",
            "reason": "No lawful basis attached"
        }

    return {"decision": "ALLOW"}


# ============================================================
# GDPR 4. DATA MINIMIZATION
# ============================================================

def check_data_minimization(intent: dict):
    service = intent.get("service")
    data_type = intent.get("data_type")

    if not service or not data_type:
        return {"decision": "ALLOW"}

    query = """
    MATCH (s:Service {name: $service})
    WHERE NOT $data_type IN s.allowed_data_categories
    RETURN s
    """
    result = Neo4jClient.run(query, {
        "service": service,
        "data_type": data_type
    })

    if result:
        return {
            "decision": "DENY",
            "layer": "GDPR_DATA_MINIMIZATION",
            "reason": "Excessive personal data usage"
        }

    return {"decision": "ALLOW"}


# ============================================================
# GDPR 6. RIGHT TO ERASURE (SLA)
# ============================================================

def check_erasure_sla(intent: dict):
    query = """
    MATCH (c:Company)-[:HAS_ERASURE_POLICY]->(p:ErasurePolicy)
    MATCH (c)-[:HAS_ERASURE_REQUEST]->(e:ErasureRequest)
    WHERE duration.inDays(e.created_at, datetime()).days > p.sla_days
    RETURN e.id, p.sla_days
    """
    result = Neo4jClient.run(query)

    if result:
        return {
            "decision": "DENY",
            "layer": "GDPR_ERASURE_SLA",
            "reason": f"Erasure request {result[0]['e.id']} exceeded SLA of {result[0]['p.sla_days']} days"
        }

    return {"decision": "ALLOW"}


# ============================================================
# GDPR 8. DATA LOCALIZATION
# ============================================================

def check_data_localization(intent: dict):
    execution_region = intent.get("region")
    data_type = intent.get("data_type")

    if not execution_region or not data_type:
        return {"decision": "ALLOW"}

    query = """
    MATCH (d:PersonalData {type: $data_type})-[:LOCATED_IN]->(r:Region)
    WHERE r.name <> $region
    RETURN r.name
    """
    result = Neo4jClient.run(query, {
        "data_type": data_type,
        "region": execution_region
    })

    if result:
        return {
            "decision": "DENY",
            "layer": "GDPR_DATA_LOCALIZATION",
            "reason": "Cross-region personal data movement blocked"
        }

    return {"decision": "ALLOW"}
