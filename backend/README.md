AOSS Compliance Engine
Graph-Based GDPR & SRE-Aware Enforcement Layer
Overview
AOSS (Automated Orchestration for SRE and System Administration) is a compliance-aware automation platform where infrastructure actions are gated by hard constraints, not model reasoning.

This repository implements the Compliance Engine of AOSS using a Neo4j graph database to enforce GDPR rules in an SRE context.

Unlike rule files or prompt-based checks, compliance here is:

Structural

Deterministic

Auditable

Impossible for agents or LLMs to bypass

Why Graph-Based Compliance?
Traditional approaches (YAML, OPA, prompts):

are flat

lose organizational memory

can be overridden by reasoning

are hard to audit

This system uses a knowledge graph where:

If the graph does not permit an action, it cannot execute — regardless of agent intent.

Architecture (High Level)
User / Agent Intent
        ↓
AOSS Planner (already implemented)
        ↓
Compliance Engine (THIS PROJECT)
        ↓
Neo4j Graph Validation
        ↓
ALLOW | DENY | REQUIRE_APPROVAL
        ↓
Executor / Human Approval
Core Design Principles
Loaders ≠ Checkers

Loaders create compliance state (onboarding / config)

Checkers enforce compliance (runtime)

Read-only enforcement

Checkers never modify the graph

Hard constraints

Some violations are non-negotiable (e.g., lawful basis)

Time-correct logic

Uses duration.inDays() to avoid calendar ambiguity

Folder Structure
backend/
├── sre_compliance/
│   ├── graph/
│   │   └── neo4j_client.py
│   ├── gdpr/
│   │   ├── loader.py     # ALL GDPR state creation
│   │   └── checker.py    # ALL GDPR enforcement
│   └── engine.py         # Central enforcement pipeline
├── .env
└── requirements.txt
GDPR Rules Implemented (SRE-Focused)
1. Data Retention Control – Article 5(1)(e)
Why SREs care

logs

backups

database purges

rotation jobs

Enforced rules

Cannot delete earlier than retention

Cannot keep data longer than allowed

Blocked actions

Deleting logs at 30 days when retention is 90

Keeping backups forever

Disabling log rotation

2. Purpose Limitation – Article 5(1)(b)
Why SREs care

debugging

analytics

monitoring reuse

Graph model

(ProcessingActivity)-[:USES_DATA]->(PersonalData)
Blocked actions

Using auth logs for analytics

Exporting prod data to staging

Using customer data for load tests

3. Lawful Basis Enforcement – Article 6 (HARD FAIL)
Rule
Every processing activity must have a legal basis.

Graph constraint

(ProcessingActivity)-[:HAS_LEGAL_BASIS]->(LegalBasis)
Behavior

No approval

No override

Immediate DENY

4. Data Minimization – Article 5(1)(c)
Why SREs care

logs

traces

payload dumps

Blocked actions

Logging full emails / phone numbers

Dumping full user tables

Capturing excessive request payloads

5. Access Control & Least Privilege – Article 32
Why SREs care

automation roles

destructive permissions

Enforced

Risk-based execution

Mandatory approval for high-risk actions

Blocked actions

Agent deleting prod DB

Low-privilege automation restarting auth services

6. Right to Erasure (SLA) – Article 17
Why SREs care

deletion pipelines

distributed systems

Graph model

(Company)-[:HAS_ERASURE_REQUEST]->(ErasureRequest)
Key rule

Erasure must complete within SLA

Important implementation detail

Uses duration.inDays() for accurate elapsed time

7. Replication & Backup Coverage – Articles 17 + 32
Why SREs care

replicas

DR systems

caches

Blocked actions

Partial deletion

Deleting primary DB only

Skipping backups or caches

8. Data Localization – Articles 44–49
Why SREs care

cloud regions

failover clusters

backups

Graph model

(PersonalData)-[:LOCATED_IN]->(Region)
Blocked actions

EU data replicated to US

Cross-region DR restores

Illegal backup restores

9. Logging & Auditability – Articles 30, 33
Why SREs care

traceability

incident response

Blocked actions

Disabling audit logs

Deleting audit trails

Silent background jobs

10. Breach Detection & Response – Articles 33–34
Why SREs care

incidents

alerting

security response

Blocked actions

Muting alerts during incidents

Suppressing anomaly detection

Risky ops during breaches

11. Human-in-the-Loop for High-Risk Actions
Always requires approval

Bulk deletes

Schema drops

Firewall changes

Identity store changes

How Enforcement Works
Agent Intent (example)
{
  "action": "DELETE_LOGS",
  "service": "auth-service",
  "params": {
    "older_than_days": 120
  }
}
Engine Evaluation
decision = evaluate_intent(intent)
Possible outcomes
ALLOW
DENY
REQUIRE_APPROVAL
Why This Cannot Be Bypassed
Agent never sees GDPR text

Agent cannot alter graph state

Enforcement is independent of LLM reasoning

Constraints are structural, not heuristic

Key Technical Lessons (Discovered During Implementation)
duration.between().days is incorrect for SLA checks

duration.inDays() must be used for absolute elapsed time

Loaders must never overwrite historical facts

ON CREATE SET is mandatory for compliance data

Most compliance failures are missing relationships, not logic bugs

Current Status
✔ GDPR compliance backend complete
✔ Time-correct SLA enforcement
✔ SRE-aware rules implemented
✔ Agent-safe, deterministic system

Next Planned Layers
Platform / SRE Safety Graph

prod protection

destructive command bans

blast radius control

Organizational Policy Graph

approvals

on-call ownership

RBAC

Frontend Form → Graph Builder

company onboarding UI

policy packs (GDPR, HIPAA, RBI, SOC2)

