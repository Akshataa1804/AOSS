from graph_connector import GraphConnector

def build_graph_from_threats(policy_name: str, threat_json: dict):
    """
    Build Neo4j graph from extracted threat JSON.
    policy_name = PDF filename (without .pdf)
    """

    actions = threat_json.get("actions", [])
    if not actions:
        return {"status": "no_actions"}

    # 1️⃣ Create Policy Document node
    GraphConnector.run(
        """
        MERGE (p:PolicyDoc {name: $policy})
        """,
        {"policy": policy_name}
    )

    for act in actions:
        # 2️⃣ Action node
        GraphConnector.run(
            """
            MERGE (a:Action {command: $command})
            SET a.intent = $intent
            WITH a
            MATCH (p:PolicyDoc {name: $policy})
            MERGE (a)-[:DEFINED_IN]->(p)
            """,
            {
                "command": act["command"],
                "intent": act["intent"],
                "policy": policy_name
            }
        )

        # 3️⃣ Service node
        if act["service"]:
            GraphConnector.run(
                """
                MERGE (s:Service {name: $service})
                WITH s
                MATCH (a:Action {command: $command})
                MERGE (a)-[:AFFECTS]->(s)
                """,
                {
                    "service": act["service"],
                    "command": act["command"]
                }
            )

        # 4️⃣ System node
        if act["affected_system"]:
            GraphConnector.run(
                """
                MERGE (sys:System {name: $system})
                WITH sys
                MATCH (a:Action {command: $command})
                MERGE (a)-[:TARGETS]->(sys)
                """,
                {
                    "system": act["affected_system"],
                    "command": act["command"]
                }
            )

        # 5️⃣ Risk node
        if act["risk_level"]:
            GraphConnector.run(
                """
                MERGE (r:Risk {level: $risk})
                WITH r
                MATCH (a:Action {command: $command})
                MERGE (a)-[:HAS_RISK]->(r)
                """,
                {
                    "risk": act["risk_level"],
                    "command": act["command"]
                }
            )

        # 6️⃣ Approval node
        if act["needs_approval"]:
            GraphConnector.run(
                """
                MERGE (ap:Approval {type: 'ADMIN'})
                WITH ap
                MATCH (a:Action {command: $command})
                MERGE (a)-[:REQUIRES_APPROVAL]->(ap)
                """,
                {
                    "command": act["command"]
                }
            )

    return {"status": "graph_built", "policy": policy_name}
