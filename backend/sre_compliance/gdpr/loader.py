from sre_compliance.graph.neo4j_client import Neo4jClient
from datetime import datetime

# ============================================================
# GDPR 1. DATA RETENTION (Article 5(1)(e))
# ============================================================

def load_retention_policy(
    company: str,
    service: str,
    data_type: str,
    retention_days: int
):
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


# ============================================================
# GDPR 2. PURPOSE LIMITATION + PROCESSING ACTIVITY
# ============================================================

def load_processing_activity(
    service: str,
    activity: str,
    purpose: str,
    data_types: list[str]
):
    query = """
    MERGE (s:Service {name: $service})
    MERGE (pa:ProcessingActivity {name: $activity, purpose: $purpose})
    MERGE (s)-[:RUNS]->(pa)
    WITH pa
    UNWIND $data_types AS dt
    MERGE (d:PersonalData {type: dt})
    MERGE (pa)-[:USES_DATA]->(d)
    """
    Neo4jClient.run(query, {
        "service": service,
        "activity": activity,
        "purpose": purpose,
        "data_types": data_types
    })


# ============================================================
# GDPR 3. LAWFUL BASIS (Article 6)
# ============================================================

def attach_legal_basis(activity: str, basis_type: str):
    query = """
    MATCH (pa:ProcessingActivity {name: $activity})
    MERGE (lb:LegalBasis {type: $basis})
    MERGE (pa)-[:HAS_LEGAL_BASIS]->(lb)
    """
    Neo4jClient.run(query, {
        "activity": activity,
        "basis": basis_type
    })


# ============================================================
# GDPR 4. DATA MINIMIZATION
# ============================================================

def allow_data_categories(service: str, allowed_categories: list[str]):
    query = """
    MATCH (s:Service {name: $service})
    SET s.allowed_data_categories = $categories
    """
    Neo4jClient.run(query, {
        "service": service,
        "categories": allowed_categories
    })


# ============================================================
# GDPR 6. RIGHT TO ERASURE (Article 17)
# ============================================================

def load_erasure_policy(company: str, sla_days: int):
    query = """
    MERGE (c:Company {name: $company})
    MERGE (p:ErasurePolicy {sla_days: $sla_days})
    MERGE (c)-[:HAS_ERASURE_POLICY]->(p)
    """
    Neo4jClient.run(query, {
        "company": company,
        "sla_days": sla_days
    })


def create_erasure_request(
    request_id: str,
    company: str,
    data_type: str
):
    query = """
    MERGE (e:ErasureRequest {id: $id})
    ON CREATE SET e.created_at = datetime($created_at)
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


# ============================================================
# GDPR 8. DATA LOCALIZATION
# ============================================================

def assign_data_region(data_type: str, region: str):
    query = """
    MERGE (d:PersonalData {type: $data_type})
    MERGE (r:Region {name: $region})
    MERGE (d)-[:LOCATED_IN]->(r)
    """
    Neo4jClient.run(query, {
        "data_type": data_type,
        "region": region
    })


# ============================================================
# GDPR 7. REPLICATION / BACKUP COVERAGE
# ============================================================

def load_replication_graph(
    service: str,
    replicas: list[str],
    backups: list[str],
    caches: list[str]
):
    query = """
    MATCH (s:Service {name: $service})
    WITH s
    UNWIND $replicas AS rname
        MERGE (r:Replica {name: rname})
        MERGE (s)-[:HAS_REPLICA]->(r)
    WITH s
    UNWIND $backups AS bname
        MERGE (b:Backup {name: bname})
        MERGE (s)-[:HAS_BACKUP]->(b)
    WITH s
    UNWIND $caches AS cname
        MERGE (c:Cache {name: cname})
        MERGE (s)-[:USES_CACHE]->(c)
    """
    Neo4jClient.run(query, {
        "service": service,
        "replicas": replicas,
        "backups": backups,
        "caches": caches
    })
