# graph_connector.py
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class GraphConnector:
    driver = None

    @staticmethod
    def connect():
        if GraphConnector.driver is None:
            GraphConnector.driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
        return GraphConnector.driver

    @staticmethod
    def run(query: str, params: dict = None):
        driver = GraphConnector.connect()
        with driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    @staticmethod
    def close():
        if GraphConnector.driver:
            GraphConnector.driver.close()
            GraphConnector.driver = None
