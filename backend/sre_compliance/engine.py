from sre_compliance.sre_safety.checker import (
    check_destructive_action,
    check_incident_freeze,
    check_prod_environment
)

from sre_compliance.gdpr.checker import (
    check_erasure_sla,
    check_gdpr_retention,
    check_legal_basis,
    check_purpose_limitation,
    check_data_minimization,
    check_data_localization
)

def evaluate_intent(intent: dict):
    checks = [
         # PLATFORM / SRE SAFETY
        check_destructive_action,
        check_incident_freeze,
        check_change_freeze,
        check_blast_radius,
        check_prod_environment,

        # ORGANIZATIONAL POLICY
        check_role_permissions,
        check_org_blast_radius,
        check_org_approval,

        # REGULATORY (GDPR)
        check_erasure_sla,
        check_gdpr_retention,
        check_legal_basis,
        check_purpose_limitation,
        check_data_minimization,
        check_data_localization
    ]

    for check in checks:
        result = check(intent)
        if result["decision"] != "ALLOW":
            return result

    return {"decision": "ALLOW"}
