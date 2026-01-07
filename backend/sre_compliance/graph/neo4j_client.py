from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load .env ONCE when module is imported
load_dotenv()

class Neo4jClient:
    _driver = None

    @classmethod
    def init_driver(cls):
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(
                    os.getenv("NEO4J_USER"),
                    os.getenv("NEO4J_PASSWORD")
                )
            )

    @classmethod
    def run(cls, query: str, params: dict = None):
        if cls._driver is None:
            cls.init_driver()

        with cls._driver.session() as session:
            return session.run(query, params or {}).data()
