from sre_compliance.gdpr.checker import (
    check_erasure_sla,
    check_gdpr_retention,
    check_purpose_limitation,
    check_legal_basis,
    check_data_minimization,
    check_data_localization
)

def evaluate_intent(intent: dict):
    checks = [
        check_erasure_sla,
        check_gdpr_retention,
        check_legal_basis,          # HARD FAIL
        check_purpose_limitation,
        check_data_minimization,
        check_data_localization
    ]

    for check in checks:
        result = check(intent)
        if result["decision"] != "ALLOW":
            return result

    return {"decision": "ALLOW"}
