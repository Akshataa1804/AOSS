from sre_compliance.graph.neo4j_client import Neo4jClient
from datetime import datetime

# --------------------------------------------------
# GDPR RETENTION POLICY
# --------------------------------------------------

def load_retention_policy(
    company: str,
    service: str,
    data_type: str,
    retention_days: int
):
    """
    Stores GDPR retention rule
    """
    query = """
    MERGE (c:Company {name: $company})
    MERGE (s:Service {name: $service})
    MERGE (d:PersonalData {type: $data_type})
    MERGE (r:RetentionPolicy {days: $days})

    MERGE (c)-[:OWNS]->(s)
    MERGE (s)-[:PROCESSES]->(d)
    MERGE (d)-[:RETAINED_UNDER]->(r)
    """

    Neo4jClient.run(query, {
        "company": company,
        "service": service,
        "data_type": data_type,
        "days": retention_days
    })


# --------------------------------------------------
# GDPR ERASURE SLA POLICY
# --------------------------------------------------

def load_erasure_policy(company: str, sla_days: int):
    """
    Stores GDPR erasure SLA (Article 17)
    """
    query = """
    MERGE (c:Company {name: $company})
    MERGE (p:ErasurePolicy {sla_days: $sla_days})
    MERGE (c)-[:HAS_ERASURE_POLICY]->(p)
    """

    Neo4jClient.run(query, {
        "company": company,
        "sla_days": sla_days
    })


# --------------------------------------------------
# GDPR ERASURE REQUEST
# --------------------------------------------------

def create_erasure_request(
    request_id: str,
    company: str,
    data_type: str
):
    """
    Creates a GDPR erasure request
    """
    query = """
    MERGE (e:ErasureRequest {id: $id})
    SET e.created_at = datetime($created_at)
    MERGE (c:Company {name: $company})
    MERGE (d:PersonalData {type: $data_type})

    MERGE (c)-[:HAS_ERASURE_REQUEST]->(e)
    MERGE (e)-[:TARGETS]->(d)
    """

    Neo4jClient.run(query, {
        "id": request_id,
        "company": company,
        "data_type": data_type,
        "created_at": datetime.utcnow().isoformat()
    })
