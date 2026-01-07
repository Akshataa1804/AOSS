from sre_compliance.gdpr.checker import (
    check_erasure_sla,
    check_gdpr_retention
)

def evaluate_intent(intent: dict):
    checks = [
        check_erasure_sla,      # must run first
        check_gdpr_retention
    ]

    for check in checks:
        result = check(intent)
        if result["decision"] != "ALLOW":
            return result

    return {"decision": "ALLOW"}
