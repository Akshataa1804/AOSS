# models.py

# Logical entities represented in Neo4j

GDPR_NODES = [
    "Company",
    "Service",
    "PersonalData",
    "RetentionPolicy"
]

GDPR_RELATIONSHIPS = [
    "PROCESSES",        # Service -> PersonalData
    "RETAINED_UNDER"    # PersonalData -> RetentionPolicy
]
