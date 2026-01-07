from sre_compliance.graph.neo4j_client import Neo4jClient

# --------------------------------------------------
# GDPR RETENTION CHECK
# --------------------------------------------------

def check_gdpr_retention(intent: dict):
    """
    Blocks premature deletion of data
    """

    if intent.get("action") != "DELETE_LOGS":
        return {"decision": "ALLOW"}

    service = intent.get("service")
    requested_days = intent.get("params", {}).get("older_than_days")

    if not service or requested_days is None:
        return {"decision": "ALLOW"}

    query = """
    MATCH (s:Service {name: $service})
          -[:PROCESSES]->(d:PersonalData)
          -[:RETAINED_UNDER]->(r:RetentionPolicy)
    WHERE r.days > $requested
    RETURN r.days AS required_days
    """

    result = Neo4jClient.run(query, {
        "service": service,
        "requested": requested_days
    })

    if result:
        return {
            "decision": "DENY",
            "layer": "GDPR_RETENTION",
            "reason": f"Minimum retention is {result[0]['required_days']} days"
        }

    return {"decision": "ALLOW"}


# --------------------------------------------------
# GDPR ERASURE SLA CHECK
# --------------------------------------------------

def check_erasure_sla(intent: dict):
    """
    Blocks automation if erasure SLA is violated
    """

    query = """
    MATCH (c:Company)-[:HAS_ERASURE_POLICY]->(p:ErasurePolicy)
    MATCH (c)-[:HAS_ERASURE_REQUEST]->(e:ErasureRequest)
    WHERE duration.inDays(e.created_at, datetime()).days > p.sla_days
    RETURN e.id AS request_id, p.sla_days AS sla_days
    """

    result = Neo4jClient.run(query)

    if result:
        return {
            "decision": "DENY",
            "layer": "GDPR_ERASURE_SLA",
            "reason": f"Erasure request {result[0]['request_id']} exceeded SLA of {result[0]['sla_days']} days"
        }

    return {"decision": "ALLOW"}
